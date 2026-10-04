import re
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.data_record import DataRecordModel
from app.models.policy import PolicyRuleModel
from app.schemas.policy import (
    PolicyRuleCreate,
    PolicyRuleUpdate,
    PolicyEvaluationItem,
    PolicyEvaluationSummary,
    ALLOWED_LIFECYCLE_ACTIONS,
)

class PolicyService:
    @staticmethod
    def parse_duration_to_days(duration_str: str) -> int:
        """
        Parses human-readable duration strings into numeric days.
        Supported formats:
        - '1 year', '2 years', '3 years' (1 year = 365 days)
        - '90 days', '180 days', '365 days'
        - '6 months', '1 month' (1 month = 30 days)
        - Raw integer digits (e.g. '730')
        """
        if not duration_str or not str(duration_str).strip():
            raise ValueError("Retention duration cannot be empty.")

        cleaned = str(duration_str).strip().lower()

        # Check raw digits
        if cleaned.isdigit():
            val = int(cleaned)
            if val <= 0:
                raise ValueError("Retention days must be greater than zero.")
            return val

        # Match regex pattern: <number> <unit>
        match = re.match(r"^(\d+)\s*(year|years|month|months|day|days)$", cleaned)
        if not match:
            raise ValueError(
                f"Invalid retention duration '{duration_str}'. "
                "Expected formats like '2 years', '90 days', '6 months'."
            )

        number = int(match.group(1))
        unit = match.group(2)

        if number <= 0:
            raise ValueError("Retention duration number must be greater than zero.")

        if unit in ("year", "years"):
            return number * 365
        elif unit in ("month", "months"):
            return number * 30
        elif unit in ("day", "days"):
            return number * 1
        else:
            raise ValueError(f"Unsupported duration unit '{unit}'.")

    @staticmethod
    def evaluate_expiry(
        expiry_date_str: str,
        as_of_date: Optional[date] = None,
        expiring_soon_days: int = 30
    ) -> Tuple[str, int]:
        """
        Calculates expiry status and delta days based on an as_of_date and configurable threshold.
        Status outcomes:
        - delta_days < 0 -> EXPIRED
        - 0 <= delta_days <= expiring_soon_days -> EXPIRING_SOON
        - delta_days > expiring_soon_days -> ACTIVE
        """
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc).date()

        try:
            exp_date = datetime.strptime(expiry_date_str.strip()[:10], "%Y-%m-%d").date()
        except Exception:
            raise ValueError(f"Invalid expiry date format: '{expiry_date_str}'. Expected 'YYYY-MM-DD'.")

        delta_days = (exp_date - as_of_date).days

        if delta_days < 0:
            expiry_status = "EXPIRED"
        elif 0 <= delta_days <= expiring_soon_days:
            expiry_status = "EXPIRING_SOON"
        else:
            expiry_status = "ACTIVE"

        return expiry_status, delta_days

    @staticmethod
    def match_policy(
        db: Session,
        category: str
    ) -> Optional[PolicyRuleModel]:
        """
        Finds the governing active policy rule for a category.
        Prefers specific category match over wildcard '*'.
        """
        active_policies = db.query(PolicyRuleModel).filter(
            PolicyRuleModel.is_active == True
        ).all()

        category_clean = category.strip().lower()
        wildcard_policy = None

        for pol in active_policies:
            pol_cat = pol.category.strip().lower()
            if pol_cat == category_clean:
                return pol
            if pol_cat == "*":
                wildcard_policy = pol

        return wildcard_policy

    @classmethod
    def evaluate_record(
        cls,
        db: Session,
        record: DataRecordModel,
        as_of_date: Optional[date] = None,
        expiring_soon_days: int = 30
    ) -> PolicyEvaluationItem:
        """
        Evaluates a single data record against deterministic governance rules and active policies.
        Deterministic Decision Hierarchy:
        - RULE 1: If purpose_mismatch == True -> deterministic recommendation = REVIEW (overrides AI DELETE/KEEP/ANONYMIZE).
        - RULE 2: If expiry status is ACTIVE -> deterministic recommendation = KEEP (unless purpose mismatch forces REVIEW).
        - RULE 3: If expiry status is EXPIRING_SOON -> deterministic recommendation = REVIEW.
        - RULE 4: If expiry status is EXPIRED -> matched policy action_on_expiry (unless purpose mismatch forces REVIEW).
        """
        # Step 1: Calculate expiry status
        expiry_status, delta_days = cls.evaluate_expiry(
            expiry_date_str=record.expiry_date,
            as_of_date=as_of_date,
            expiring_soon_days=expiring_soon_days
        )

        # Step 2: Match governing policy
        matched_policy = cls.match_policy(db, record.category)
        matched_rule_code = matched_policy.rule_code if matched_policy else None
        policy_action = matched_policy.action_on_expiry if matched_policy else "REVIEW"

        ai_rec = (record.ai_recommendation or "").strip().upper()
        purpose_mismatch = bool(record.purpose_mismatch)

        # Step 3: Apply deterministic rules
        if purpose_mismatch:
            # RULE 1: Purpose mismatch strictly mandates human review
            deterministic_rec = "REVIEW"
            if ai_rec in ("DELETE", "KEEP", "ANONYMIZE"):
                reason = f"Deterministic override: Purpose mismatch detected for record '{record.record_id}'. AI recommended '{ai_rec}', but governance mandates human REVIEW."
            else:
                reason = "Mandatory human REVIEW required due to purpose mismatch."
        elif expiry_status == "ACTIVE":
            # RULE 2: Active records are preserved
            deterministic_rec = "KEEP"
            reason = f"Record retention is ACTIVE ({delta_days} days remaining until expiry)."
        elif expiry_status == "EXPIRING_SOON":
            # RULE 3: Approaching expiry queues proactive review
            deterministic_rec = "REVIEW"
            reason = f"Record is EXPIRING SOON ({delta_days} days remaining <= threshold of {expiring_soon_days} days). Queued for retention review."
        elif expiry_status == "EXPIRED":
            # RULE 4: Expired records execute policy mandate
            deterministic_rec = policy_action
            reason = f"Record EXPIRED ({abs(delta_days)} days overdue). Governed by policy '{matched_rule_code or 'DEFAULT'}' action '{policy_action}'."
        else:
            deterministic_rec = "REVIEW"
            reason = "State undetermined. Queued for review."

        return PolicyEvaluationItem(
            record_id=record.record_id,
            category=record.category,
            expiry_date=record.expiry_date,
            expiry_status=expiry_status,
            days_until_expiry=delta_days,
            deterministic_recommendation=deterministic_rec,
            matched_policy_rule=matched_rule_code,
            ai_recommendation=ai_rec or None,
            purpose_mismatch=purpose_mismatch,
            evaluation_reason=reason
        )

    @classmethod
    def evaluate_all_records(
        cls,
        db: Session,
        as_of_date: Optional[date] = None,
        expiring_soon_days: int = 30,
        category: Optional[str] = None
    ) -> PolicyEvaluationSummary:
        """
        Batch evaluates records and compiles summary statistics.
        """
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc).date()

        query = db.query(DataRecordModel)
        if category:
            query = query.filter(DataRecordModel.category.ilike(f"%{category.strip()}%"))

        records = query.order_by(DataRecordModel.id.asc()).all()

        active_count = 0
        expiring_soon_count = 0
        expired_count = 0
        recommendations = {"KEEP": 0, "REVIEW": 0, "ANONYMIZE": 0, "DELETE": 0}
        evaluation_items = []

        for rec in records:
            item = cls.evaluate_record(
                db=db,
                record=rec,
                as_of_date=as_of_date,
                expiring_soon_days=expiring_soon_days
            )
            evaluation_items.append(item)

            if item.expiry_status == "ACTIVE":
                active_count += 1
            elif item.expiry_status == "EXPIRING_SOON":
                expiring_soon_count += 1
            elif item.expiry_status == "EXPIRED":
                expired_count += 1

            if item.deterministic_recommendation in recommendations:
                recommendations[item.deterministic_recommendation] += 1
            else:
                recommendations[item.deterministic_recommendation] = 1

        return PolicyEvaluationSummary(
            total_evaluated=len(records),
            active_count=active_count,
            expiring_soon_count=expiring_soon_count,
            expired_count=expired_count,
            recommendations=recommendations,
            as_of_date=as_of_date.isoformat(),
            expiring_soon_days=expiring_soon_days,
            records=evaluation_items
        )

    # ----------------------------------------------------
    # Policy CRUD Methods
    # ----------------------------------------------------

    @classmethod
    def create_policy(cls, db: Session, policy_in: PolicyRuleCreate) -> PolicyRuleModel:
        """Creates a new policy rule with uniqueness and duration validation."""
        existing = db.query(PolicyRuleModel).filter(
            PolicyRuleModel.rule_code.ilike(policy_in.rule_code.strip())
        ).first()
        if existing:
            raise ValueError(f"Policy rule with code '{policy_in.rule_code}' already exists.")

        # Compute or validate retention days
        computed_days = cls.parse_duration_to_days(policy_in.retention_period)
        retention_days = policy_in.retention_days or computed_days

        action = policy_in.action_on_expiry.strip().upper()
        if action not in ALLOWED_LIFECYCLE_ACTIONS:
            raise ValueError(f"action_on_expiry must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")

        new_policy = PolicyRuleModel(
            rule_code=policy_in.rule_code.strip().upper(),
            name=policy_in.name.strip(),
            category=policy_in.category.strip(),
            retention_period=policy_in.retention_period.strip(),
            retention_days=retention_days,
            action_on_expiry=action,
            description=policy_in.description,
            is_active=policy_in.is_active
        )
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
        return new_policy

    @staticmethod
    def get_policy(db: Session, policy_id: int) -> Optional[PolicyRuleModel]:
        """Fetches policy by numerical ID."""
        return db.query(PolicyRuleModel).filter(PolicyRuleModel.id == policy_id).first()

    @staticmethod
    def get_policy_by_code(db: Session, rule_code: str) -> Optional[PolicyRuleModel]:
        """Fetches policy by rule code."""
        return db.query(PolicyRuleModel).filter(
            PolicyRuleModel.rule_code.ilike(rule_code.strip())
        ).first()

    @staticmethod
    def list_policies(db: Session, active_only: bool = False) -> List[PolicyRuleModel]:
        """Lists policies with optional active-only filtering."""
        query = db.query(PolicyRuleModel)
        if active_only:
            query = query.filter(PolicyRuleModel.is_active == True)
        return query.order_by(PolicyRuleModel.id.asc()).all()

    @classmethod
    def update_policy(
        cls,
        db: Session,
        policy_id: int,
        policy_in: PolicyRuleUpdate
    ) -> PolicyRuleModel:
        """Updates an existing policy rule."""
        policy = db.query(PolicyRuleModel).filter(PolicyRuleModel.id == policy_id).first()
        if not policy:
            raise ValueError(f"Policy rule with id {policy_id} not found.")

        update_data = policy_in.model_dump(exclude_unset=True)

        if "retention_period" in update_data and update_data["retention_period"]:
            computed_days = cls.parse_duration_to_days(update_data["retention_period"])
            update_data["retention_days"] = computed_days

        if "action_on_expiry" in update_data and update_data["action_on_expiry"]:
            action = update_data["action_on_expiry"].strip().upper()
            if action not in ALLOWED_LIFECYCLE_ACTIONS:
                raise ValueError(f"action_on_expiry must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")
            update_data["action_on_expiry"] = action

        for field, value in update_data.items():
            setattr(policy, field, value)

        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def deactivate_policy(db: Session, policy_id: int) -> PolicyRuleModel:
        """
        Soft deactivates a policy rule (sets is_active=False).
        Does NOT physically delete the database row.
        """
        policy = db.query(PolicyRuleModel).filter(PolicyRuleModel.id == policy_id).first()
        if not policy:
            raise ValueError(f"Policy rule with id {policy_id} not found.")

        policy.is_active = False
        db.commit()
        db.refresh(policy)
        return policy
