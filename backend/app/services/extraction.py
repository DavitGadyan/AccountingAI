"""Document classification and K-1/K-3 extraction.

The model does three jobs and no others: identify what a PDF is, pull typed numbers out
of it with a confidence and a page reference, and draft prose a human will edit. It never
decides a filing requirement — that is ``app.rules``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import DocumentKind, ExtractionFieldStatus

log = get_logger(__name__)

PROMPT_VERSION = "k1-extract-2025.3"

# The fields worth extracting from a syndication K-1. Anything not on this list is noise
# for this engagement and is deliberately not asked for - a shorter schema extracts more
# accurately than an exhaustive one.
K1_FIELD_SPEC: list[tuple[str, str]] = [
    ("header.partnership_name", "Partnership name (Part I item B)"),
    ("header.partnership_ein", "Partnership EIN (Part I item A)"),
    ("header.partner_name", "Partner name (Part II item F)"),
    ("header.partner_tin", "Partner identifying number (Part II item E)"),
    ("header.is_foreign_partner", "Part II item I2 foreign partner checkbox"),
    ("header.is_final", "Final K-1 checkbox"),
    ("header.is_amended", "Amended K-1 checkbox"),
    ("boxes.box_1", "Box 1 ordinary business income (loss)"),
    ("boxes.box_2", "Box 2 net rental real estate income (loss)"),
    ("boxes.box_3", "Box 3 other net rental income (loss)"),
    ("boxes.box_5", "Box 5 interest income"),
    ("boxes.box_9a", "Box 9a net long-term capital gain (loss)"),
    ("boxes.box_10", "Box 10 net section 1231 gain (loss)"),
    ("boxes.box_13_K", "Box 13 code K excess business interest expense"),
    ("boxes.box_15_O", "Box 15 code O credit for section 1446 withholding"),
    ("boxes.box_19_A", "Box 19 code A distributions of cash and marketable securities"),
    ("boxes.box_20_AH", "Box 20 code AH other information incl. section 897 amounts"),
    ("capital_account.beginning_capital", "Item L beginning capital account"),
    ("capital_account.contributions", "Item L capital contributed during the year"),
    ("capital_account.current_year_net", "Item L current year net income (loss)"),
    ("capital_account.withdrawals", "Item L withdrawals and distributions"),
    ("capital_account.ending_capital", "Item L ending capital account"),
    ("liabilities.nonrecourse", "Item K nonrecourse liabilities"),
    ("liabilities.qualified_nonrecourse", "Item K qualified nonrecourse financing"),
    ("liabilities.recourse", "Item K recourse liabilities"),
    ("profit_loss.ending_profit_pct", "Item J ending profit share percentage"),
    ("profit_loss.ending_capital_pct", "Item J ending capital share percentage"),
]

CLASSIFY_PROMPT = """You are classifying a tax document for a U.S. compliance engagement.

Return JSON only:
{{"kind": <one of {kinds}>, "tax_year": <int or null>, "issuer": <string or null>,
  "recipient": <string or null>, "is_amended": <bool>, "confidence": <0..1>}}

Judge only from what is visible. If the year is not printed on the document, return null
rather than inferring it from context - a wrong year silently files against the wrong
engagement.

Document text:
{text}
"""

EXTRACT_PROMPT = """Extract the listed fields from this Schedule K-1 (Form 1065).

Rules that matter more than completeness:
- A number in parentheses is negative. Return -12345.67, never "(12,345.67)".
- A blank or dashed box is null, NOT zero. Zero is an assertion; blank is an absence, and
  the two lead to different determinations downstream.
- Never compute, infer or reconcile a value. Report only what is printed.
- confidence is your own read of legibility and certainty for that specific field.
- page is the 1-based page the value appears on; source_text is the surrounding line.

Fields:
{fields}

Return JSON only:
{{"fields": [{{"path": str, "raw_value": str|null, "numeric_value": float|null,
              "confidence": float, "page": int|null, "source_text": str|null}}]}}

Document text:
{text}
"""


@dataclass
class ExtractedValue:
    path: str
    label: str
    raw_value: str | None
    numeric_value: float | None
    confidence: float
    page: int | None = None
    source_text: str | None = None

    @property
    def status(self) -> ExtractionFieldStatus:
        """Anything the model is not sure about goes to a human. No exceptions."""
        if self.confidence >= settings.extraction_confidence_threshold:
            return ExtractionFieldStatus.AUTO_ACCEPTED
        return ExtractionFieldStatus.NEEDS_REVIEW


@dataclass
class ExtractionResult:
    kind: DocumentKind
    kind_confidence: float
    tax_year: int | None
    values: list[ExtractedValue] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = settings.extraction_model
    prompt_version: str = PROMPT_VERSION

    @property
    def needs_review_count(self) -> int:
        return sum(1 for v in self.values if v.status == ExtractionFieldStatus.NEEDS_REVIEW)

    @property
    def auto_accept_rate(self) -> float:
        if not self.values:
            return 0.0
        return 1 - (self.needs_review_count / len(self.values))

    def as_boxes(self) -> dict[str, Any]:
        """Collapse dotted paths into the nested payload stored on ``K1Record``."""
        out: dict[str, dict[str, Any]] = {}
        for v in self.values:
            head, _, tail = v.path.partition(".")
            out.setdefault(head, {})[tail] = (
                v.numeric_value if v.numeric_value is not None else v.raw_value
            )
        return out


class ExtractionClient:
    """Thin wrapper over the model API.

    Kept behind an interface so the whole pipeline runs in tests and in CI with no
    network and no key, using ``StubExtractionClient``.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.extraction_model

    async def _complete(self, prompt: str) -> tuple[dict, int, int]:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text
        # The model is asked for JSON only, but a stray prose preamble should degrade to a
        # retry-able error rather than a silently empty extraction.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model returned no JSON object")
        return (
            json.loads(text[start : end + 1]),
            message.usage.input_tokens,
            message.usage.output_tokens,
        )

    async def classify(self, text: str) -> tuple[DocumentKind, float, int | None]:
        payload, _, _ = await self._complete(
            CLASSIFY_PROMPT.format(
                kinds=[k.value for k in DocumentKind], text=text[:20_000]
            )
        )
        try:
            kind = DocumentKind(payload.get("kind", "unclassified"))
        except ValueError:
            kind = DocumentKind.UNCLASSIFIED
        return kind, float(payload.get("confidence", 0.0)), payload.get("tax_year")

    async def extract_k1(self, text: str) -> ExtractionResult:
        fields = "\n".join(f"- {path}: {label}" for path, label in K1_FIELD_SPEC)
        payload, tin, tout = await self._complete(
            EXTRACT_PROMPT.format(fields=fields, text=text[:60_000])
        )
        labels = dict(K1_FIELD_SPEC)
        values = [
            ExtractedValue(
                path=item["path"],
                label=labels.get(item["path"], item["path"]),
                raw_value=item.get("raw_value"),
                numeric_value=item.get("numeric_value"),
                confidence=float(item.get("confidence", 0.0)),
                page=item.get("page"),
                source_text=item.get("source_text"),
            )
            for item in payload.get("fields", [])
            if item.get("path") in labels
        ]
        return ExtractionResult(
            kind=DocumentKind.K1_1065,
            kind_confidence=1.0,
            tax_year=None,
            values=values,
            input_tokens=tin,
            output_tokens=tout,
            model=self.model,
        )


class StubExtractionClient(ExtractionClient):
    """Deterministic client for tests, CI and offline demos.

    Its existence is the reason the whole pipeline has a test that runs with no network.
    """

    def __init__(self, fixture: dict[str, Any] | None = None) -> None:
        super().__init__(api_key="stub", model="stub")
        self.fixture = fixture or {}

    async def classify(self, text: str) -> tuple[DocumentKind, float, int | None]:
        lowered = text.lower()
        if "schedule k-3" in lowered:
            return DocumentKind.K3_1065, 0.97, self.fixture.get("tax_year")
        if "schedule k-1" in lowered:
            return DocumentKind.K1_1065, 0.98, self.fixture.get("tax_year")
        if "8805" in lowered:
            return DocumentKind.FORM_8805, 0.95, self.fixture.get("tax_year")
        return DocumentKind.UNCLASSIFIED, 0.2, None

    async def extract_k1(self, text: str) -> ExtractionResult:
        labels = dict(K1_FIELD_SPEC)
        values = [
            ExtractedValue(
                path=path,
                label=labels[path],
                raw_value=str(value),
                numeric_value=value if isinstance(value, int | float) else None,
                confidence=float(self.fixture.get("confidence", 0.97)),
                page=1,
                source_text=f"{labels[path]} {value}",
            )
            for path, value in self.fixture.get("values", {}).items()
            if path in labels
        ]
        return ExtractionResult(
            kind=DocumentKind.K1_1065,
            kind_confidence=0.98,
            tax_year=self.fixture.get("tax_year"),
            values=values,
            model="stub",
        )


def extract_pdf_text(raw: bytes) -> str:
    """Text layer first; a scanned page falls through to OCR at the worker level."""
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
