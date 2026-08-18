"""Nothing reaches the IRS without a credentialed human and a clean open-item list."""

from __future__ import annotations

import asyncio

import pytest

from app.core.errors import FilingBlocked
from app.models import Filing, OpenItem, User
from app.models.enums import FilingStatus, IssueSeverity, IssueStatus, UserRole
from app.services.efile import FilingGate, StubTransmitter


def make_filing(status=FilingStatus.APPROVED) -> Filing:
    return Filing(
        id="fil-1",
        firm_id="firm-1",
        engagement_id="eng-1",
        entity_id="holdco-a",
        form="1120-F",
        tax_year=2025,
        jurisdiction="us_federal",
        status=status,
        approved_by_id="user-1",
        form_data={},
    )


def make_reviewer(**kw) -> User:
    defaults = dict(
        id="user-1",
        firm_id="firm-1",
        email="cpa@firm.test",
        full_name="Dana Reyes",
        hashed_password="x",
        role=UserRole.REVIEWER,
        credential="CPA",
        credential_number="123456",
        credential_state="NY",
        is_active=True,
    )
    return User(**{**defaults, **kw})


def blocking_item() -> OpenItem:
    return OpenItem(
        id="oi-1",
        firm_id="firm-1",
        engagement_id="eng-1",
        code="MISSING_K3",
        title="Schedule K-3 outstanding for Sunbelt Fund III",
        detail="",
        severity=IssueSeverity.BLOCKING,
        status=IssueStatus.OPEN,
        blocks_filing=True,
    )


def test_approved_filing_with_credentialed_reviewer_passes():
    assert FilingGate.check(make_filing(), make_reviewer(), []) == []


def test_unapproved_filing_cannot_transmit():
    problems = FilingGate.check(make_filing(FilingStatus.IN_PREPARATION), make_reviewer(), [])
    assert any("approved" in p for p in problems)


def test_preparer_cannot_authorise_transmission():
    preparer = make_reviewer(role=UserRole.PREPARER, credential=None)
    problems = FilingGate.check(make_filing(), preparer, [])
    assert any("reviewer" in p for p in problems)


def test_reviewer_without_a_credential_cannot_sign():
    """Circular 230, enforced in code rather than in a policy document."""
    problems = FilingGate.check(make_filing(), make_reviewer(credential=None), [])
    assert any("credential" in p for p in problems)


def test_blocking_open_item_stops_transmission():
    problems = FilingGate.check(make_filing(), make_reviewer(), [blocking_item()])
    assert any("K-3" in p for p in problems)


def test_resolved_open_item_no_longer_blocks():
    item = blocking_item()
    item.status = IssueStatus.RESOLVED
    assert FilingGate.check(make_filing(), make_reviewer(), [item]) == []


def test_assert_transmittable_raises_with_every_blocker_listed():
    with pytest.raises(FilingBlocked) as exc:
        FilingGate.assert_transmittable(
            make_filing(FilingStatus.IN_PREPARATION),
            make_reviewer(credential=None, role=UserRole.PREPARER),
            [blocking_item()],
        )
    blockers = exc.value.detail["blockers"]
    assert len(blockers) >= 3  # status, role, credential, open item — all reported at once


def test_no_approver_recorded_is_itself_a_blocker():
    problems = FilingGate.check(make_filing(), None, [])
    assert any("No approver" in p for p in problems)


def test_stub_transmitter_never_reaches_the_irs():
    # Driven with asyncio.run rather than an async test so the suite needs no plugin —
    # this file must stay runnable with a bare pytest and nothing else installed.
    receipt = asyncio.run(StubTransmitter().transmit(make_filing(), {}))
    assert receipt.submission_id.startswith("STUB-")
    assert receipt.accepted is True
