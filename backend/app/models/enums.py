"""Domain vocabulary.

These enums are the shared language between the rules engine, the API and the UI. Keep
the string values stable — they appear in filed workpapers.
"""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    REVIEWER = "reviewer"  # CPA / EA — the only role that can approve and transmit
    PREPARER = "preparer"
    CLIENT = "client"


class Jurisdiction(StrEnum):
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    CANADA_FEDERAL = "canada_federal"
    CANADA_PROVINCIAL = "canada_provincial"


class EntityType(StrEnum):
    INDIVIDUAL = "individual"
    US_PARTNERSHIP = "us_partnership"          # the syndication LPs
    US_LLC = "us_llc"
    US_CORPORATION = "us_corporation"
    US_DISREGARDED = "us_disregarded"
    CA_CORPORATION = "ca_corporation"          # the two Canadian holdcos
    CA_PARTNERSHIP = "ca_partnership"
    TRUST = "trust"


class TaxClassification(StrEnum):
    PARTNERSHIP = "partnership"
    C_CORPORATION = "c_corporation"
    S_CORPORATION = "s_corporation"
    DISREGARDED = "disregarded"
    INDIVIDUAL = "individual"
    FOREIGN_CORPORATION = "foreign_corporation"


class DocumentKind(StrEnum):
    K1_1065 = "k1_1065"
    K3_1065 = "k3_1065"
    FORM_8805 = "form_8805"
    FORM_1042S = "form_1042s"
    FORM_8288A = "form_8288a"
    PRIOR_YEAR_RETURN = "prior_year_return"
    PRIOR_YEAR_WORKPAPER = "prior_year_workpaper"
    STATE_SUPPLEMENT = "state_supplement"
    PARTNERSHIP_AGREEMENT = "partnership_agreement"
    ENTITY_FORMATION = "entity_formation"
    CAPITAL_ACCOUNT_STATEMENT = "capital_account_statement"
    W8BEN_E = "w8ben_e"
    OTHER = "other"
    UNCLASSIFIED = "unclassified"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    NEEDS_REVIEW = "needs_review"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"   # an amended K-1 arrived
    FAILED = "failed"


class ExtractionFieldStatus(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"


class EngagementStatus(StrEnum):
    ONBOARDING = "onboarding"
    DOCUMENT_INTAKE = "document_intake"
    IN_PREPARATION = "in_preparation"
    IN_REVIEW = "in_review"
    READY_TO_FILE = "ready_to_file"
    FILED = "filed"
    CLOSED = "closed"


class FilingStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PREPARATION = "in_preparation"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"          # signer approved; may now be transmitted
    TRANSMITTED = "transmitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"  # determined not required, with a recorded reason


class Requirement(StrEnum):
    REQUIRED = "required"
    PROTECTIVE = "protective"      # filed to preserve deductions under Reg. 1.882-4
    RECOMMENDED = "recommended"
    NOT_REQUIRED = "not_required"
    NEEDS_ANALYSIS = "needs_analysis"


class IssueSeverity(StrEnum):
    BLOCKING = "blocking"          # cannot transmit while open
    WARNING = "warning"
    INFO = "info"


class IssueStatus(StrEnum):
    OPEN = "open"
    WAITING_ON_CLIENT = "waiting_on_client"
    WAITING_ON_SYNDICATOR = "waiting_on_syndicator"
    RESOLVED = "resolved"
    WAIVED = "waived"              # requires a reviewer and a written reason
