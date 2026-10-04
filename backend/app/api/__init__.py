from app.api.routes import router
from app.api.policy_routes import router as policy_router
from app.api.audit_routes import router as audit_router
from app.api.action_routes import router as action_router

__all__ = ["router", "policy_router", "audit_router", "action_router"]

