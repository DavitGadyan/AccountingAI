"""E-file transmission.

The platform is not an IRS-authorized transmitter; it drives one through this adapter.
The value in this module is not the HTTP call — it is the gate above it.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import settings
from app.core.errors import FilingBlocked
from app.models import Filing, OpenItem, User
from app.models.enums import FilingStatus, IssueStatus, UserRole


@dataclass
class TransmissionReceipt:
    submission_id: str
    accepted: bool
    reference: str
    received_at: datetime
    reject_codes: list[str] | None = None


class EfileTransmitter(ABC):
    @abstractmethod
    async def transmit(self, filing: Filing, payload: dict) -> TransmissionReceipt: ...

    @abstractmethod
    async def poll(self, submission_id: str) -> TransmissionReceipt: ...


class StubTransmitter(EfileTransmitter):
    """Used in development, tests and demos. Never reaches the IRS."""

    async def transmit(self, filing: Filing, payload: dict) -> TransmissionReceipt:
        return TransmissionReceipt(
            submission_id=f"STUB-{uuid.uuid4().hex[:12].upper()}",
            accepted=True,
            reference=f"stub-ack/{filing.form}/{filing.tax_year}",
            received_at=datetime.now(UTC),
        )

    async def poll(self, submission_id: str) -> TransmissionReceipt:
        return TransmissionReceipt(
            submission_id=submission_id,
            accepted=True,
            reference="stub-ack",
            received_at=datetime.now(UTC),
        )


class MefTransmitter(EfileTransmitter):
    """Adapter for a third-party MeF transmitter.

    Kept deliberately thin: authentication, submit, poll. Everything that decides *whether*
    to submit lives in ``FilingGate`` so it is testable without a network.
    """

    def __init__(self) -> None:
        if not settings.efile_base_url or not settings.efile_api_key:
            raise ValueError("E-file provider is configured but credentials are missing")
        self.base_url = settings.efile_base_url
        self.api_key = settings.efile_api_key
        self.etin = settings.efile_etin

    async def transmit(self, filing: Filing, payload: dict) -> TransmissionReceipt:
        import httpx

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/submissions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "etin": self.etin,
                    "form": filing.form,
                    "taxYear": filing.tax_year,
                    "jurisdiction": filing.jurisdiction,
                    "state": filing.state,
                    "return": payload,
                },
            )
            response.raise_for_status()
            body = response.json()
        return TransmissionReceipt(
            submission_id=body["submissionId"],
            accepted=body.get("status") == "accepted",
            reference=body.get("reference", ""),
            received_at=datetime.now(UTC),
            reject_codes=body.get("rejectCodes"),
        )

    async def poll(self, submission_id: str) -> TransmissionReceipt:
        import httpx

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            response = await client.get(
                f"/submissions/{submission_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            body = response.json()
        return TransmissionReceipt(
            submission_id=submission_id,
            accepted=body.get("status") == "accepted",
            reference=body.get("reference", ""),
            received_at=datetime.now(UTC),
            reject_codes=body.get("rejectCodes"),
        )


def get_transmitter() -> EfileTransmitter:
    if settings.efile_provider == "mef":
        return MefTransmitter()
    return StubTransmitter()


class FilingGate:
    """The four conditions that must hold before anything reaches the IRS.

    There is no override flag and no bypass parameter. Every transmission path in the
    codebase calls ``assert_transmittable`` first; that is the whole reason the class
    exists as a separate object rather than as a few ifs inside a route handler.
    """

    @staticmethod
    def check(filing: Filing, approver: User | None, open_items: list[OpenItem]) -> list[str]:
        problems: list[str] = []

        if filing.status != FilingStatus.APPROVED:
            problems.append(
                f"{filing.form} is in status '{filing.status}'. Only an approved return may "
                f"be transmitted."
            )

        if approver is None:
            problems.append("No approver recorded on this filing.")
        else:
            if approver.role not in {UserRole.REVIEWER, UserRole.ADMIN}:
                problems.append(
                    f"{approver.full_name} holds the '{approver.role}' role. Only a reviewer "
                    f"may authorise transmission."
                )
            if not approver.credential:
                problems.append(
                    f"{approver.full_name} has no CPA/EA credential on file. Circular 230 "
                    f"requires a credentialed signer."
                )

        blocking = [
            item
            for item in open_items
            if item.blocks_filing
            and item.status
            in {
                IssueStatus.OPEN,
                IssueStatus.WAITING_ON_CLIENT,
                IssueStatus.WAITING_ON_SYNDICATOR,
            }
        ]
        for item in blocking:
            problems.append(f"Blocking open item unresolved: {item.title}")

        return problems

    @staticmethod
    def assert_transmittable(
        filing: Filing, approver: User | None, open_items: list[OpenItem]
    ) -> None:
        problems = FilingGate.check(filing, approver, open_items)
        if problems:
            raise FilingBlocked(
                "This return cannot be transmitted yet.",
                detail={"blockers": problems, "filing_id": filing.id},
            )
