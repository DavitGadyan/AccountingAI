from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.api.deps import FirmDep, SessionDep, StaffDep
from app.core.errors import NotFound
from app.models import Client, Entity, K1Record, Ownership, PropertyState
from app.schemas.entities import (
    ClientCreate,
    ClientOut,
    EntityCreate,
    EntityOut,
    OwnershipCreate,
    OwnershipOut,
    PropertyStateCreate,
    PropertyStateOut,
    StructureEdge,
    StructureGraph,
    StructureNode,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
async def list_clients(session: SessionDep, firm_id: FirmDep, _: StaffDep) -> list[Client]:
    return list(await session.scalars(select(Client).where(Client.firm_id == firm_id)))


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> Client:
    client = Client(firm_id=firm_id, **payload.model_dump())
    session.add(client)
    await session.flush()
    return client


@router.get("/{client_id}/entities", response_model=list[EntityOut])
async def list_entities(
    client_id: str, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> list[Entity]:
    return list(
        await session.scalars(
            select(Entity).where(Entity.client_id == client_id, Entity.firm_id == firm_id)
        )
    )


@router.post("/entities", response_model=EntityOut, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: EntityCreate, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> Entity:
    entity = Entity(firm_id=firm_id, **payload.model_dump())
    session.add(entity)
    await session.flush()
    return entity


@router.post("/ownerships", response_model=OwnershipOut, status_code=status.HTTP_201_CREATED)
async def create_ownership(
    payload: OwnershipCreate, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> Ownership:
    edge = Ownership(firm_id=firm_id, **payload.model_dump())
    session.add(edge)
    await session.flush()
    return edge


@router.post(
    "/property-states", response_model=PropertyStateOut, status_code=status.HTTP_201_CREATED
)
async def create_property_state(
    payload: PropertyStateCreate, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> PropertyState:
    ps = PropertyState(firm_id=firm_id, **payload.model_dump())
    session.add(ps)
    await session.flush()
    return ps


@router.get("/{client_id}/structure", response_model=StructureGraph)
async def structure(
    client_id: str, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> StructureGraph:
    """The org chart. Rendered as the entity map in the UI and read by the rules engine."""
    client = await session.scalar(
        select(Client).where(Client.id == client_id, Client.firm_id == firm_id)
    )
    if client is None:
        raise NotFound("Client not found").as_http()

    entities = list(
        await session.scalars(select(Entity).where(Entity.client_id == client_id))
    )
    ids = {e.id for e in entities}
    edges = list(
        await session.scalars(select(Ownership).where(Ownership.owner_entity_id.in_(ids)))
    )
    states = list(
        await session.scalars(select(PropertyState).where(PropertyState.entity_id.in_(ids)))
    )
    k1_counts = dict(
        (
            await session.execute(
                select(K1Record.partner_entity_id, func.count())
                .where(K1Record.partner_entity_id.in_(ids))
                .group_by(K1Record.partner_entity_id)
            )
        ).all()
    )

    states_by_entity: dict[str, list[str]] = {}
    for ps in states:
        states_by_entity.setdefault(ps.entity_id, []).append(ps.state)

    return StructureGraph(
        nodes=[
            StructureNode(
                id=e.id,
                name=e.name,
                entity_type=str(e.entity_type),
                country=e.country,
                is_syndication=bool(e.is_syndication),
                states=sorted(set(states_by_entity.get(e.id, []))),
                k1_count=int(k1_counts.get(e.id, 0)),
            )
            for e in entities
        ],
        edges=[
            StructureEdge(
                source=e.owner_entity_id,
                target=e.owned_entity_id,
                profits_pct=float(e.profits_pct),
                capital_pct=float(e.capital_pct),
            )
            for e in edges
        ],
    )
