"""Initial schema.

Generated from the models rather than hand-written, then edited for the indexes that
matter: firm_id on every table (tenancy), sha256 on documents (dedupe), and
(engagement_id, tax_year) on the tables the dashboard aggregates.
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "firms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("ptin", sa.String(20)),
        sa.Column("efin", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), sa.ForeignKey("firms.id"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="preparer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("credential", sa.String(40)),
        sa.Column("credential_number", sa.String(60)),
        sa.Column("credential_state", sa.String(2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_firm", "users", ["firm_id"])

    op.create_table(
        "clients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("primary_contact_email", sa.String(320)),
        sa.Column("residence_country", sa.String(2), server_default="CA"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_clients_firm", "clients", ["firm_id"])

    op.create_table(
        "entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("client_id", sa.String(36), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("tax_classification", sa.String(40), nullable=False),
        sa.Column("country", sa.String(2), server_default="US"),
        sa.Column("formation_state", sa.String(2)),
        sa.Column("us_tin", sa.String(20)),
        sa.Column("foreign_tin", sa.String(30)),
        sa.Column("treaty_country", sa.String(2)),
        sa.Column("treaty_lob_qualified", sa.Boolean),
        sa.Column("treaty_lob_basis", sa.Text),
        sa.Column("is_syndication", sa.Boolean, server_default=sa.false()),
        sa.Column("syndicator_name", sa.String(200)),
        sa.Column("first_investment_date", sa.Date),
        sa.Column("exited_on", sa.Date),
        sa.Column("net_election_871d", sa.Boolean, server_default=sa.false()),
        sa.Column("net_election_year", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_entities_firm", "entities", ["firm_id"])
    op.create_index("ix_entities_client", "entities", ["client_id"])

    op.create_table(
        "ownerships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("owner_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("owned_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("profits_pct", sa.Numeric(9, 6), nullable=False),
        sa.Column("capital_pct", sa.Numeric(9, 6), nullable=False),
        sa.Column("loss_pct", sa.Numeric(9, 6)),
        sa.Column("is_general_partner", sa.Boolean, server_default=sa.false()),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("owner_entity_id", "owned_entity_id", "effective_from", name="uq_edge"),
    )
    op.create_index("ix_ownerships_owner", "ownerships", ["owner_entity_id"])
    op.create_index("ix_ownerships_owned", "ownerships", ["owned_entity_id"])

    op.create_table(
        "property_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("property_name", sa.String(200)),
        sa.Column("apportionment_pct", sa.Float),
        sa.Column("composite_election_made", sa.Boolean, server_default=sa.false()),
        sa.Column("withholding_remitted", sa.Numeric(14, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_property_states_entity", "property_states", ["entity_id"])

    op.create_table(
        "engagements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("client_id", sa.String(36), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("tax_year", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), server_default="onboarding"),
        sa.Column("fixed_fee", sa.Numeric(12, 2)),
        sa.Column("fee_currency", sa.String(3), server_default="USD"),
        sa.Column("is_first_year", sa.Boolean, server_default=sa.true()),
        sa.Column("assigned_preparer_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("assigned_reviewer_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("rolled_from_engagement_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("client_id", "tax_year", name="uq_client_year"),
    )
    op.create_index("ix_engagements_firm", "engagements", ["firm_id"])
    op.create_index("ix_engagements_year", "engagements", ["tax_year"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("source_entity_id", sa.String(36), sa.ForeignKey("entities.id")),
        sa.Column("recipient_entity_id", sa.String(36), sa.ForeignKey("entities.id")),
        sa.Column("filename", sa.String(400), nullable=False),
        sa.Column("storage_key", sa.String(600), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("byte_size", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(40), server_default="unclassified"),
        sa.Column("kind_confidence", sa.Float),
        sa.Column("status", sa.String(30), server_default="uploaded"),
        sa.Column("tax_year", sa.Integer),
        sa.Column("is_amended", sa.Boolean, server_default=sa.false()),
        sa.Column("supersedes_document_id", sa.String(36)),
        sa.Column("page_count", sa.Integer),
        sa.Column("uploaded_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_engagement", "documents", ["engagement_id"])
    # Content hash lookup is on the upload path for every file — syndicators re-send the
    # same PDF constantly and this index is what makes dedupe free.
    op.create_index("ix_documents_sha", "documents", ["sha256"])

    op.create_table(
        "extraction_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_extraction_jobs_document", "extraction_jobs", ["document_id"])

    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("extraction_jobs.id"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("field_path", sa.String(120), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("raw_value", sa.String(400)),
        sa.Column("numeric_value", sa.Numeric(16, 2)),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("page", sa.Integer),
        sa.Column("source_text", sa.Text),
        sa.Column("status", sa.String(30), server_default="needs_review"),
        sa.Column("reviewed_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("corrected_value", sa.Numeric(16, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_extracted_fields_document", "extracted_fields", ["document_id"])
    op.create_index("ix_extracted_fields_job", "extracted_fields", ["job_id"])

    op.create_table(
        "k1_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("partnership_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("partner_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("tax_year", sa.Integer, nullable=False),
        sa.Column("form_year", sa.Integer, nullable=False),
        sa.Column("is_final_k1", sa.Boolean, server_default=sa.false()),
        sa.Column("is_amended", sa.Boolean, server_default=sa.false()),
        sa.Column("partnership_ein", sa.String(20)),
        sa.Column("partner_is_foreign", sa.Boolean, server_default=sa.true()),
        sa.Column("boxes", sa.JSON, server_default="{}"),
        sa.Column("capital_account", sa.JSON, server_default="{}"),
        sa.Column("liabilities", sa.JSON, server_default="{}"),
        sa.Column("k3", sa.JSON, server_default="{}"),
        sa.Column("state_amounts", sa.JSON, server_default="{}"),
        sa.Column("withholding_1446", sa.Numeric(14, 2)),
        sa.Column("reviewed_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_k1_engagement", "k1_records", ["engagement_id"])
    op.create_index("ix_k1_partner", "k1_records", ["partner_entity_id"])

    op.create_table(
        "determinations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("tax_year", sa.Integer, nullable=False),
        sa.Column("rule_id", sa.String(60), nullable=False),
        sa.Column("rule_version", sa.String(20), nullable=False),
        sa.Column("form", sa.String(40), nullable=False),
        sa.Column("jurisdiction", sa.String(30), nullable=False),
        sa.Column("state", sa.String(2)),
        sa.Column("requirement", sa.String(30), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("authority", sa.Text, nullable=False),
        sa.Column("triggering_facts", sa.JSON, server_default="{}"),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("due_date", sa.Date),
        sa.Column("extended_due_date", sa.Date),
        sa.Column("overridden_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("overridden_at", sa.DateTime(timezone=True)),
        sa.Column("override_requirement", sa.String(30)),
        sa.Column("override_reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_determinations_engagement", "determinations", ["engagement_id"])
    op.create_index("ix_determinations_rule", "determinations", ["rule_id"])

    op.create_table(
        "filings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("determination_id", sa.String(36), sa.ForeignKey("determinations.id")),
        sa.Column("form", sa.String(40), nullable=False),
        sa.Column("tax_year", sa.Integer, nullable=False),
        sa.Column("jurisdiction", sa.String(30), nullable=False),
        sa.Column("state", sa.String(2)),
        sa.Column("is_protective", sa.Boolean, server_default=sa.false()),
        sa.Column("is_extension", sa.Boolean, server_default=sa.false()),
        sa.Column("status", sa.String(30), server_default="not_started"),
        sa.Column("form_data", sa.JSON, server_default="{}"),
        sa.Column("prepared_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("prepared_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("submission_id", sa.String(80)),
        sa.Column("transmitted_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("ack_reference", sa.String(120)),
        sa.Column("reject_codes", sa.JSON),
        sa.Column("balance_due", sa.Numeric(14, 2)),
        sa.Column("overpayment", sa.Numeric(14, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_filings_engagement", "filings", ["engagement_id"])
    op.create_index("ix_filings_submission", "filings", ["submission_id"])

    op.create_table(
        "workpapers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id")),
        sa.Column("filing_id", sa.String(36), sa.ForeignKey("filings.id")),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("generator_version", sa.String(20), nullable=False),
        sa.Column("rows", sa.JSON, server_default="[]"),
        sa.Column("totals", sa.JSON, server_default="{}"),
        sa.Column("narrative", sa.Text),
        sa.Column("ties_out", sa.Boolean, server_default=sa.true()),
        sa.Column("tie_out_detail", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workpapers_engagement", "workpapers", ["engagement_id"])

    op.create_table(
        "open_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id")),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), server_default="warning"),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("blocks_filing", sa.Boolean, server_default=sa.false()),
        sa.Column("requested_from", sa.String(40)),
        sa.Column("resolved_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_note", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_open_items_engagement", "open_items", ["engagement_id"])

    op.create_table(
        "variances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id")),
        sa.Column("metric", sa.String(120), nullable=False),
        sa.Column("prior_year", sa.Integer, nullable=False),
        sa.Column("prior_value", sa.Numeric(16, 2)),
        sa.Column("current_value", sa.Numeric(16, 2)),
        sa.Column("absolute_change", sa.Numeric(16, 2)),
        sa.Column("relative_change", sa.Float),
        sa.Column("is_material", sa.Boolean, server_default=sa.false()),
        sa.Column("explanation", sa.Text),
        sa.Column("accepted_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_variances_engagement", "variances", ["engagement_id"])

    op.create_table(
        "deliverables",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("storage_key", sa.String(600), nullable=False),
        sa.Column("manifest", sa.JSON, server_default="{}"),
        sa.Column("memo_markdown", sa.Text),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("released_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_deliverables_engagement", "deliverables", ["engagement_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("firm_id", sa.String(36), nullable=False),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("engagements.id")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("object_type", sa.String(60), nullable=False),
        sa.Column("object_id", sa.String(36)),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, server_default="{}"),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_firm", "audit_events", ["firm_id"])
    op.create_index("ix_audit_action", "audit_events", ["action"])
    op.create_index("ix_audit_object", "audit_events", ["object_id"])
    op.create_index("ix_audit_engagement", "audit_events", ["engagement_id"])


def downgrade() -> None:
    for table in [
        "audit_events",
        "deliverables",
        "variances",
        "open_items",
        "workpapers",
        "filings",
        "determinations",
        "k1_records",
        "extracted_fields",
        "extraction_jobs",
        "documents",
        "engagements",
        "property_states",
        "ownerships",
        "entities",
        "clients",
        "users",
        "firms",
    ]:
        op.drop_table(table)
