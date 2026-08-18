/** Mirrors the API's pydantic schemas. Kept hand-written and small rather than generated,
 *  so a field that disappears server-side shows up as a type error here. */

export type Requirement =
  | "required"
  | "protective"
  | "recommended"
  | "not_required"
  | "needs_analysis";

export type FilingStatus =
  | "not_started"
  | "in_preparation"
  | "ready_for_review"
  | "approved"
  | "transmitted"
  | "accepted"
  | "rejected"
  | "not_required";

export type IssueSeverity = "blocking" | "warning" | "info";
export type IssueStatus =
  | "open"
  | "waiting_on_client"
  | "waiting_on_syndicator"
  | "resolved"
  | "waived";

export interface CurrentUser {
  id: string;
  firm_id: string;
  email: string;
  full_name: string;
  role: "admin" | "reviewer" | "preparer" | "client";
  credential: string | null;
  credential_number: string | null;
}

export interface Engagement {
  id: string;
  client_id: string;
  tax_year: number;
  status: string;
  fixed_fee: number | null;
  fee_currency: string;
  is_first_year: boolean;
  assigned_preparer_id: string | null;
  assigned_reviewer_id: string | null;
}

export interface EngagementDashboard {
  engagement: Engagement;
  client_name: string;
  documents_received: number;
  documents_expected: number;
  fields_needing_review: number;
  determinations: number;
  filings_required: number;
  filings_accepted: number;
  open_items_blocking: number;
  open_items_total: number;
  next_due_date: string | null;
  memo_available: boolean;
}

export interface Determination {
  id: string;
  entity_id: string;
  rule_id: string;
  rule_version: string;
  form: string;
  jurisdiction: string;
  state: string | null;
  requirement: Requirement;
  rationale: string;
  authority: string;
  triggering_facts: Record<string, unknown>;
  confidence: number;
  due_date: string | null;
  extended_due_date: string | null;
  override_requirement: Requirement | null;
  override_reason: string | null;
}

export interface Filing {
  id: string;
  entity_id: string;
  form: string;
  tax_year: number;
  jurisdiction: string;
  state: string | null;
  status: FilingStatus;
  is_protective: boolean;
  is_extension: boolean;
  prepared_at: string | null;
  approved_by_id: string | null;
  approved_at: string | null;
  submission_id: string | null;
  transmitted_at: string | null;
  acknowledged_at: string | null;
  ack_reference: string | null;
  reject_codes: string[] | null;
  balance_due: number | null;
}

export interface GateCheck {
  filing_id: string;
  transmittable: boolean;
  blockers: string[];
}

export interface Workpaper {
  id: string;
  entity_id: string | null;
  code: string;
  title: string;
  rows: Record<string, unknown>[];
  totals: Record<string, number>;
  narrative: string | null;
  ties_out: boolean;
  tie_out_detail: Record<string, unknown>;
}

export interface OpenItem {
  id: string;
  entity_id: string | null;
  code: string;
  title: string;
  detail: string;
  severity: IssueSeverity;
  status: IssueStatus;
  blocks_filing: boolean;
  requested_from: string | null;
  resolution_note: string | null;
}

export interface Variance {
  id: string;
  entity_id: string | null;
  metric: string;
  prior_year: number;
  prior_value: number | null;
  current_value: number | null;
  absolute_change: number | null;
  relative_change: number | null;
  is_material: boolean;
  explanation: string | null;
}

export interface TaxDocument {
  id: string;
  engagement_id: string;
  filename: string;
  kind: string;
  kind_confidence: number | null;
  status: string;
  tax_year: number | null;
  byte_size: number;
  page_count: number | null;
  sha256: string;
  is_amended: boolean;
  source_entity_id: string | null;
  recipient_entity_id: string | null;
  created_at: string;
}

export interface ExtractedField {
  id: string;
  document_id: string;
  field_path: string;
  label: string;
  raw_value: string | null;
  numeric_value: number | null;
  corrected_value: number | null;
  confidence: number;
  page: number | null;
  source_text: string | null;
  status: "auto_accepted" | "needs_review" | "confirmed" | "corrected";
}

export interface StructureNode {
  id: string;
  name: string;
  entity_type: string;
  country: string;
  is_syndication: boolean;
  states: string[];
  k1_count: number;
}

export interface StructureEdge {
  source: string;
  target: string;
  profits_pct: number;
  capital_pct: number;
}

export interface StructureGraph {
  nodes: StructureNode[];
  edges: StructureEdge[];
}

export interface PipelineReport {
  engagement_id: string;
  tax_year: number;
  rules_evaluated: number;
  determinations: number;
  filings_required: number;
  workpapers_generated: number;
  open_items: number;
  blocking_items: number;
  variances: number;
}
