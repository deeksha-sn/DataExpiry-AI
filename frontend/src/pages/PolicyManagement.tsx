import React, { useEffect, useState, useMemo } from 'react';
import {
  ShieldCheck,
  Sliders,
  Plus,
  Edit2,
  Trash2,
  Play,
  Lock,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Filter,
  X,
  Clock,
  FileText,
  Search,
  Check,
  Info,
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  PolicyRule,
  PolicyRuleCreateInput,
  PolicyRuleUpdateInput,
  PolicyEvaluationSummary,
  PolicyEvaluationItem,
} from '../types';

const ALLOWED_ACTIONS = ['KEEP', 'REVIEW', 'ANONYMIZE', 'DELETE'] as const;
const DEV_ROLES = ['DATA_GOVERNANCE', 'ADMIN', 'PRIVACY_OFFICER', 'AUDITOR', 'VIEWER'] as const;

export const PolicyManagement: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeOnly, setActiveOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Role simulation & Dev Headers
  const [currentRole, setCurrentRole] = useState<string>(() => apiService.getDevRole());
  const [authHeaderEnabled, setAuthHeaderEnabled] = useState<boolean>(() =>
    apiService.isDevAuthHeaderEnabled()
  );

  // Modal states
  const [isFormOpen, setIsFormOpen] = useState<boolean>(false);
  const [editingPolicy, setEditingPolicy] = useState<PolicyRule | null>(null);
  const [deactivatingId, setDeactivatingId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form fields
  const [ruleCode, setRuleCode] = useState<string>('');
  const [policyName, setPolicyName] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [retentionPeriod, setRetentionPeriod] = useState<string>('2 years');
  const [actionOnExpiry, setActionOnExpiry] = useState<string>('REVIEW');
  const [description, setDescription] = useState<string>('');
  const [isActive, setIsActive] = useState<boolean>(true);

  // Evaluation modal states
  const [isEvalOpen, setIsEvalOpen] = useState<boolean>(false);
  const [evalLoading, setEvalLoading] = useState<boolean>(false);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [evalSummary, setEvalSummary] = useState<PolicyEvaluationSummary | null>(null);
  const [asOfDate, setAsOfDate] = useState<string>(() => new Date().toISOString().slice(0, 10));
  const [expiringSoonDays, setExpiringSoonDays] = useState<number>(30);
  const [evalCategoryFilter, setEvalCategoryFilter] = useState<string>('');
  const [singleRecordId, setSingleRecordId] = useState<string>('');
  const [singleEvalItem, setSingleEvalItem] = useState<PolicyEvaluationItem | null>(null);
  const [singleEvalLoading, setSingleEvalLoading] = useState<boolean>(false);

  // Fetch policies
  const loadPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.listPolicies(activeOnly);
      setPolicies(data);
    } catch (err: any) {
      console.error('Failed to load policies:', err);
      setError(err.message || 'Unable to fetch retention policies from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, [activeOnly]);

  // Handle role change
  const handleRoleChange = (role: string) => {
    setCurrentRole(role);
    apiService.setDevRole(role);
  };

  const handleAuthHeaderToggle = (enabled: boolean) => {
    setAuthHeaderEnabled(enabled);
    apiService.setDevAuthHeaderEnabled(enabled);
  };

  // Open Create Modal
  const openCreateModal = () => {
    setEditingPolicy(null);
    setRuleCode('');
    setPolicyName('');
    setCategory('');
    setRetentionPeriod('2 years');
    setActionOnExpiry('REVIEW');
    setDescription('');
    setIsActive(true);
    setFormError(null);
    setIsFormOpen(true);
  };

  // Open Edit Modal
  const openEditModal = (p: PolicyRule) => {
    setEditingPolicy(p);
    setRuleCode(p.rule_code);
    setPolicyName(p.name);
    setCategory(p.category);
    setRetentionPeriod(p.retention_period);
    setActionOnExpiry(p.action_on_expiry);
    setDescription(p.description || '');
    setIsActive(p.is_active);
    setFormError(null);
    setIsFormOpen(true);
  };

  // Validate form fields
  const validateForm = (): string | null => {
    if (!editingPolicy && !ruleCode.trim()) {
      return 'Rule Code is required (e.g. POL-CUS-01).';
    }
    if (!policyName.trim()) {
      return 'Policy Name is required.';
    }
    if (!category.trim()) {
      return 'Category is required (e.g. Customer, Financial, or *).';
    }
    if (!retentionPeriod.trim()) {
      return 'Retention Period is required (e.g. 2 years, 90 days, 6 months).';
    }
    const durationPattern = /^(\d+)\s*(year|years|month|months|day|days)$/i;
    const isDigitsOnly = /^\d+$/.test(retentionPeriod.trim());
    if (!durationPattern.test(retentionPeriod.trim()) && !isDigitsOnly) {
      return "Retention Period must be in formats like '2 years', '90 days', '6 months', or positive days.";
    }
    if (!ALLOWED_ACTIONS.includes(actionOnExpiry as any)) {
      return `Action on Expiry must be one of: ${ALLOWED_ACTIONS.join(', ')}`;
    }
    return null;
  };

  // Submit Create or Edit
  const handleSavePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErr = validateForm();
    if (validationErr) {
      setFormError(validationErr);
      return;
    }

    setSubmitting(true);
    setFormError(null);

    try {
      if (editingPolicy) {
        const updatePayload: PolicyRuleUpdateInput = {
          name: policyName.trim(),
          category: category.trim(),
          retention_period: retentionPeriod.trim(),
          action_on_expiry: actionOnExpiry,
          description: description.trim() || undefined,
          is_active: isActive,
        };
        const updated = await apiService.updatePolicy(editingPolicy.id, updatePayload);
        setSuccessMessage(`Policy '${updated.rule_code}' successfully updated.`);
      } else {
        const createPayload: PolicyRuleCreateInput = {
          rule_code: ruleCode.trim().toUpperCase(),
          name: policyName.trim(),
          category: category.trim(),
          retention_period: retentionPeriod.trim(),
          action_on_expiry: actionOnExpiry,
          description: description.trim() || undefined,
          is_active: isActive,
        };
        const created = await apiService.createPolicy(createPayload);
        setSuccessMessage(`Policy '${created.rule_code}' successfully created.`);
      }

      setIsFormOpen(false);
      await loadPolicies();
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Save policy error:', err);
      setFormError(err.message || 'Operation failed. Please check permissions or field constraints.');
    } finally {
      setSubmitting(false);
    }
  };

  // Soft Deactivate Policy
  const handleDeactivate = async (policy: PolicyRule) => {
    if (!window.confirm(`Are you sure you want to deactivate policy rule '${policy.rule_code}'?`)) {
      return;
    }

    setDeactivatingId(policy.id);
    setError(null);
    try {
      await apiService.deactivatePolicy(policy.id);
      setSuccessMessage(`Policy '${policy.rule_code}' deactivated.`);
      await loadPolicies();
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Deactivate policy error:', err);
      setError(err.message || `Failed to deactivate policy ${policy.rule_code}.`);
    } finally {
      setDeactivatingId(null);
    }
  };

  // Run Batch Evaluation
  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    setEvalError(null);
    try {
      const summary = await apiService.evaluatePolicies({
        as_of_date: asOfDate.trim() || undefined,
        expiring_soon_days: expiringSoonDays,
        category: evalCategoryFilter.trim() || undefined,
      });
      setEvalSummary(summary);
    } catch (err: any) {
      console.error('Evaluation error:', err);
      setEvalError(err.message || 'Evaluation request failed.');
    } finally {
      setEvalLoading(false);
    }
  };

  // Run Single Record Evaluation
  const handleRunSingleEvaluation = async () => {
    if (!singleRecordId.trim()) {
      setEvalError('Please provide a record identifier (e.g. CUS-1001).');
      return;
    }
    setSingleEvalLoading(true);
    setEvalError(null);
    setSingleEvalItem(null);
    try {
      const item = await apiService.evaluateSingleRecord(singleRecordId.trim(), {
        as_of_date: asOfDate.trim() || undefined,
        expiring_soon_days: expiringSoonDays,
      });
      setSingleEvalItem(item);
    } catch (err: any) {
      console.error('Single record evaluation error:', err);
      setEvalError(err.message || `Failed to evaluate record '${singleRecordId}'.`);
    } finally {
      setSingleEvalLoading(false);
    }
  };

  // Filtered policies
  const filteredPolicies = useMemo(() => {
    return policies.filter((p) => {
      const matchesSearch =
        searchQuery === '' ||
        p.rule_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesCat =
        categoryFilter === 'ALL' || p.category.toLowerCase() === categoryFilter.toLowerCase();

      return matchesSearch && matchesCat;
    });
  }, [policies, searchQuery, categoryFilter]);

  const uniqueCategories = useMemo(() => {
    const cats = Array.from(new Set(policies.map((p) => p.category)));
    return cats.sort();
  }, [policies]);

  const actionBadge = (action: string) => {
    switch (action.toUpperCase()) {
      case 'KEEP':
        return 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
      case 'REVIEW':
        return 'border border-amber-500/30 bg-amber-500/10 text-amber-400';
      case 'ANONYMIZE':
        return 'border border-purple-500/30 bg-purple-500/10 text-purple-400';
      case 'DELETE':
        return 'border border-rose-500/30 bg-rose-500/10 text-rose-400';
      default:
        return 'border border-slate-700 bg-slate-800 text-slate-300';
    }
  };

  const statusBadge = (active: boolean) => {
    return active
      ? 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
      : 'border border-slate-700 bg-slate-800 text-slate-400';
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-amber-400">
            Governance · Retention policy
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">
            Policy Management Engine
          </h1>
          <p className="text-slate-400 mt-1">
            Define enterprise data retention rules, expiration triggers, and deterministic lifecycle actions.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setIsEvalOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-sky-600/40 bg-sky-950/40 px-3.5 py-2 text-sm font-medium text-sky-300 transition hover:bg-sky-900/50 hover:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <Play className="h-4 w-4" />
            <span>Evaluate Policies</span>
          </button>

          <button
            type="button"
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <Plus className="h-4 w-4" />
            <span>New Retention Policy</span>
          </button>
        </div>
      </div>

      {/* Role & Auth Simulator Notice */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-950/80 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Lock className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong className="text-slate-200">RBAC Identity Header:</strong> Policy mutations require{' '}
            <code className="text-sky-300">ADMIN</code> or <code className="text-sky-300">DATA_GOVERNANCE</code>.
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={authHeaderEnabled}
              onChange={(e) => handleAuthHeaderToggle(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-sky-400"
            />
            <span className="text-slate-300">Send Dev Header</span>
          </label>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Acting Role:</span>
            <select
              value={currentRole}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200 focus:border-sky-500 focus:outline-none"
            >
              {DEV_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-lg border border-rose-900/60 bg-rose-950/40 p-4 text-sm text-rose-300"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-400 hover:text-rose-200"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div
          role="status"
          className="flex items-center justify-between rounded-lg border border-emerald-900/60 bg-emerald-950/40 p-4 text-sm text-emerald-300"
        >
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-400 hover:text-emerald-200"
            aria-label="Dismiss message"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-slate-400">Total Policies</div>
          <div className="mt-1 text-2xl font-bold text-slate-100">{policies.length}</div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-emerald-400">Active Rules</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400">
            {policies.filter((p) => p.is_active).length}
          </div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-slate-400">Inactive Rules</div>
          <div className="mt-1 text-2xl font-bold text-slate-400">
            {policies.filter((p) => !p.is_active).length}
          </div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-sky-400">Categories Covered</div>
          <div className="mt-1 text-2xl font-bold text-sky-400">{uniqueCategories.length}</div>
        </div>
      </div>

      {/* Filters & Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-950">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search policies by code, name, category, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-800 bg-slate-900 text-sm text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-300 focus:border-sky-500 focus:outline-none"
            >
              <option value="ALL">All Categories</option>
              {uniqueCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer text-slate-300 select-none">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-sky-400"
            />
            <span>Active only</span>
          </label>

          <button
            type="button"
            onClick={loadPolicies}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-300 hover:text-sky-400 disabled:opacity-50"
            title="Refresh policies"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Table / Content Section */}
      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-sky-400" />
            <p className="font-medium text-slate-200">Loading retention policies...</p>
            <p className="text-xs text-slate-500 mt-1">Connecting to FastAPI policy engine</p>
          </div>
        ) : filteredPolicies.length === 0 ? (
          <div className="p-16 text-center">
            <ShieldCheck className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-200">
              {policies.length === 0 ? 'No Retention Policies Defined' : 'No Policies Match Filters'}
            </h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
              {policies.length === 0
                ? 'Create retention rules to govern how long records in each category are kept, reviewed, anonymized, or deleted.'
                : 'Try adjusting your search query or category filter.'}
            </p>
            {policies.length === 0 && (
              <button
                type="button"
                onClick={openCreateModal}
                className="mt-5 inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-sky-500"
              >
                <Plus className="w-4 h-4" />
                <span>Create First Retention Policy</span>
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left text-sm">
              <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Rule Code</th>
                  <th className="px-4 py-3 font-medium">Name & Description</th>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Retention Period</th>
                  <th className="px-4 py-3 font-medium">Action On Expiry</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredPolicies.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className="font-mono text-sm font-semibold text-sky-400">
                        {p.rule_code}
                      </span>
                    </td>
                    <td className="px-4 py-4 max-w-xs">
                      <div className="font-medium text-slate-200">{p.name}</div>
                      {p.description && (
                        <div className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                          {p.description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center rounded-md bg-slate-900 px-2 py-1 font-mono text-xs text-slate-300 border border-slate-800">
                        {p.category}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-slate-200 font-medium">{p.retention_period}</div>
                      <div className="text-xs text-slate-500">{p.retention_days} days</div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${actionBadge(p.action_on_expiry)}`}>
                        {p.action_on_expiry}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusBadge(p.is_active)}`}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right space-x-2">
                      <button
                        type="button"
                        onClick={() => openEditModal(p)}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-600 hover:text-sky-300 transition-colors"
                        title="Edit policy"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>

                      {p.is_active && (
                        <button
                          type="button"
                          onClick={() => handleDeactivate(p)}
                          disabled={deactivatingId === p.id}
                          className="inline-flex items-center gap-1 rounded-md border border-rose-900/60 bg-rose-950/30 px-2.5 py-1.5 text-xs font-medium text-rose-300 hover:bg-rose-900/40 hover:text-rose-200 transition-colors disabled:opacity-50"
                          title="Deactivate policy rule"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>{deactivatingId === p.id ? 'Deactivating...' : 'Deactivate'}</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* CREATE / EDIT MODAL */}
      {isFormOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <Sliders className="w-5 h-5 text-sky-400" />
                <h3 className="text-lg font-bold text-slate-100">
                  {editingPolicy ? `Edit Policy: ${editingPolicy.rule_code}` : 'Create New Retention Policy'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => !submitting && setIsFormOpen(false)}
                className="text-slate-400 hover:text-slate-200"
                disabled={submitting}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div role="alert" className="rounded-lg border border-rose-900 bg-rose-950/40 p-3 text-sm text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleSavePolicy} className="space-y-4 text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Rule Code <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingPolicy || submitting}
                    value={ruleCode}
                    onChange={(e) => setRuleCode(e.target.value.toUpperCase())}
                    placeholder="e.g. POL-CUS-01"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 font-mono focus:border-sky-500 focus:outline-none disabled:opacity-50"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">Unique policy identifier.</p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Category <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    disabled={submitting}
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="e.g. Customer, Financial, or *"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">Use '*' as fallback wildcard.</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Policy Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  disabled={submitting}
                  value={policyName}
                  onChange={(e) => setPolicyName(e.target.value)}
                  placeholder="e.g. Customer Account Retention Policy"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Retention Period <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    disabled={submitting}
                    value={retentionPeriod}
                    onChange={(e) => setRetentionPeriod(e.target.value)}
                    placeholder="e.g. 2 years, 90 days, 6 months"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Allowed: &apos;&lt;number&gt; years/months/days&apos; or numeric days.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Action on Expiry <span className="text-rose-400">*</span>
                  </label>
                  <select
                    disabled={submitting}
                    value={actionOnExpiry}
                    onChange={(e) => setActionOnExpiry(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 focus:border-sky-500 focus:outline-none"
                  >
                    {ALLOWED_ACTIONS.map((act) => (
                      <option key={act} value={act}>
                        {act}
                      </option>
                    ))}
                  </select>
                  <p className="text-[11px] text-slate-500 mt-1">Lifecycle action applied once expired.</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows={3}
                  disabled={submitting}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional context, regulatory requirements (GDPR Art. 5, etc.)"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none resize-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_active_checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  disabled={submitting}
                  className="rounded border-slate-700 bg-slate-950 text-sky-500 focus:ring-sky-400"
                />
                <label htmlFor="is_active_checkbox" className="text-xs text-slate-300 cursor-pointer">
                  Rule is active and evaluated during batch scans
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => setIsFormOpen(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-sky-500 disabled:opacity-50"
                >
                  {submitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                  <span>{editingPolicy ? 'Update Policy' : 'Create Policy'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* POLICY EVALUATION MODAL */}
      {isEvalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 p-6">
              <div className="flex items-center gap-3">
                <Play className="w-5 h-5 text-sky-400" />
                <div>
                  <h3 className="text-lg font-bold text-slate-100">Retention Policy Evaluation</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Evaluate data records against active retention rules using deterministic decision hierarchy.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsEvalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm">
              {evalError && (
                <div role="alert" className="rounded-lg border border-rose-900 bg-rose-950/40 p-4 text-rose-300 text-sm">
                  {evalError}
                </div>
              )}

              {/* Batch Evaluation Controls */}
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-4">
                <h4 className="font-semibold text-slate-200 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-sky-400" />
                  <span>Batch Evaluation Parameters</span>
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      As Of Date (Baseline)
                    </label>
                    <input
                      type="date"
                      value={asOfDate}
                      onChange={(e) => setAsOfDate(e.target.value)}
                      className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 text-xs focus:border-sky-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Expiring Soon Threshold (Days)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={expiringSoonDays}
                      onChange={(e) => setExpiringSoonDays(parseInt(e.target.value) || 30)}
                      className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 text-xs focus:border-sky-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Category Filter (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Customer"
                      value={evalCategoryFilter}
                      onChange={(e) => setEvalCategoryFilter(e.target.value)}
                      className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 text-xs focus:border-sky-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={handleRunEvaluation}
                    disabled={evalLoading}
                    className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-sky-500 disabled:opacity-50"
                  >
                    {evalLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    <span>{evalLoading ? 'Evaluating...' : 'Run Batch Evaluation'}</span>
                  </button>
                </div>
              </div>

              {/* Evaluation Summary Results */}
              {evalSummary && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-slate-200">Batch Evaluation Summary</h4>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950">
                      <div className="text-xs text-slate-400">Total Evaluated</div>
                      <div className="text-xl font-bold text-slate-100">{evalSummary.total_evaluated}</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950">
                      <div className="text-xs text-emerald-400">Active Records</div>
                      <div className="text-xl font-bold text-emerald-400">{evalSummary.active_count}</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950">
                      <div className="text-xs text-amber-400">Expiring Soon</div>
                      <div className="text-xl font-bold text-amber-400">{evalSummary.expiring_soon_count}</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950">
                      <div className="text-xs text-rose-400">Expired Records</div>
                      <div className="text-xl font-bold text-rose-400">{evalSummary.expired_count}</div>
                    </div>
                  </div>

                  {/* Recommendations Distribution */}
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 space-y-2">
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Deterministic Recommendations
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {Object.entries(evalSummary.recommendations).map(([rec, count]) => (
                        <div key={rec} className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${actionBadge(rec)}`}>
                            {rec}
                          </span>
                          <span className="font-mono text-sm font-bold text-slate-200">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Evaluated Records Table */}
                  {evalSummary.records && evalSummary.records.length > 0 ? (
                    <div className="overflow-x-auto rounded-xl border border-slate-800">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase">
                          <tr>
                            <th className="p-3">Record ID</th>
                            <th className="p-3">Category</th>
                            <th className="p-3">Expiry Date</th>
                            <th className="p-3">Status</th>
                            <th className="p-3">Recommendation</th>
                            <th className="p-3">Governing Policy</th>
                            <th className="p-3">Reasoning</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-900/60">
                          {evalSummary.records.map((r) => (
                            <tr key={r.record_id} className="hover:bg-slate-900">
                              <td className="p-3 font-mono font-semibold text-sky-400">{r.record_id}</td>
                              <td className="p-3 text-slate-300">{r.category}</td>
                              <td className="p-3 text-slate-400">{r.expiry_date}</td>
                              <td className="p-3">
                                <span className="font-medium text-slate-200">{r.expiry_status}</span>
                                <span className="text-[10px] text-slate-500 block">
                                  ({r.days_until_expiry} days)
                                </span>
                              </td>
                              <td className="p-3">
                                <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${actionBadge(r.deterministic_recommendation)}`}>
                                  {r.deterministic_recommendation}
                                </span>
                              </td>
                              <td className="p-3 font-mono text-slate-400">
                                {r.matched_policy_rule || 'DEFAULT'}
                              </td>
                              <td className="p-3 text-slate-400 max-w-xs">{r.evaluation_reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-500 rounded-lg border border-slate-800 bg-slate-950">
                      0 data records currently stored in the database to evaluate.
                    </div>
                  )}
                </div>
              )}

              {/* Single Record Evaluation Sandbox */}
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
                <h4 className="font-semibold text-slate-200 flex items-center gap-2">
                  <Search className="w-4 h-4 text-sky-400" />
                  <span>Single Record Evaluation</span>
                </h4>
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder="Enter Record ID (e.g. CUS-1001)"
                    value={singleRecordId}
                    onChange={(e) => setSingleRecordId(e.target.value)}
                    className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={handleRunSingleEvaluation}
                    disabled={singleEvalLoading}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50"
                  >
                    {singleEvalLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                    <span>Evaluate Record</span>
                  </button>
                </div>

                {singleEvalItem && (
                  <div className="mt-3 p-3 rounded-lg border border-slate-800 bg-slate-900 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sky-400 font-bold">{singleEvalItem.record_id}</span>
                      <span className={`px-2 py-0.5 rounded-full font-semibold ${actionBadge(singleEvalItem.deterministic_recommendation)}`}>
                        {singleEvalItem.deterministic_recommendation}
                      </span>
                    </div>
                    <div className="text-slate-300">
                      <strong>Expiry Status:</strong> {singleEvalItem.expiry_status} ({singleEvalItem.days_until_expiry} days)
                    </div>
                    <div className="text-slate-300">
                      <strong>Matched Policy:</strong> {singleEvalItem.matched_policy_rule || 'DEFAULT'}
                    </div>
                    {singleEvalItem.purpose_mismatch && (
                      <div className="text-amber-400 font-medium">
                        ⚠️ Purpose Mismatch detected: mandates human REVIEW
                      </div>
                    )}
                    <div className="text-slate-400">
                      <strong>Reason:</strong> {singleEvalItem.evaluation_reason}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="border-t border-slate-800 p-4 flex justify-end">
              <button
                type="button"
                onClick={() => setIsEvalOpen(false)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyManagement;
