"""SQLModel-based storage backend for CRUD operations.

Provides SQLModelStorage that implements the Storage ABC using
SQLModel (Pydantic + SQLAlchemy) for database persistence.

Requires the ``sql`` optional dependency group::

    pip install kokage-ui[sql]
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from kokage_ui.crud import Storage
from kokage_ui.models import _resolve_annotation

T = TypeVar("T", bound=BaseModel)


class SQLModelStorage(Storage[T]):
    """Async SQL storage using SQLModel + SQLAlchemy AsyncEngine.

    Args:
        model: SQLModel class with ``table=True``.
        engine: SQLAlchemy ``AsyncEngine`` instance.
        id_field: Name of the primary key field (default: "id").
    """

    def __init__(
        self,
        model: type[T],
        engine: Any,
        *,
        id_field: str = "id",
        position_field: str = "position",
    ) -> None:
        try:
            from sqlmodel import SQLModel as _SQLModel  # noqa: F401
        except ImportError:
            raise ImportError(
                "sqlmodel is required for SQLModelStorage. "
                "Install it with: pip install kokage-ui[sql]"
            ) from None

        self._model = model
        self._engine = engine
        self._id_field = id_field
        self._position_field = position_field

        # Detect PK type for str→int conversion
        field_info = model.model_fields.get(id_field)
        if field_info is not None:
            base_type, _ = _resolve_annotation(field_info.annotation)
            self._id_type = base_type
        else:
            self._id_type = str

    def _convert_id(self, id: str) -> Any:
        """Convert string ID to the model's PK type."""
        if self._id_type is int:
            return int(id)
        return id

    def _has_position_field(self) -> bool:
        """Check if the model has the configured position field."""
        return self._position_field in self._model.model_fields

    async def list(
        self, *, skip: int = 0, limit: int = 20, search: str | None = None
    ) -> tuple[list[T], int]:
        from sqlalchemy import func, or_
        from sqlmodel import select
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine) as session:
            stmt = select(self._model)
            count_stmt = select(func.count()).select_from(self._model)

            if search:
                conditions = []
                for field_name, field_info in self._model.model_fields.items():
                    base_type, _ = _resolve_annotation(field_info.annotation)
                    if base_type is str:
                        col = getattr(self._model, field_name)
                        conditions.append(col.ilike(f"%{search}%"))
                if conditions:
                    search_filter = or_(*conditions)
                    stmt = stmt.where(search_filter)
                    count_stmt = count_stmt.where(search_filter)

            if self._has_position_field():
                pos_col = getattr(self._model, self._position_field)
                stmt = stmt.order_by(pos_col)

            total = (await session.exec(count_stmt)).one()
            results = (await session.exec(stmt.offset(skip).limit(limit))).all()
            return list(results), total

    async def get(self, id: str) -> T | None:
        from sqlmodel import select
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine) as session:
            pk_col = getattr(self._model, self._id_field)
            stmt = select(self._model).where(pk_col == self._convert_id(id))
            result = (await session.exec(stmt)).first()
            return result

    async def create(self, data: T) -> T:
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine, expire_on_commit=False) as session:
            # Exclude None/0 id for auto-increment
            dump = data.model_dump()
            id_val = dump.get(self._id_field)
            if self._id_type is int and (id_val is None or id_val == 0):
                dump.pop(self._id_field, None)

            instance = self._model(**dump)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def update(self, id: str, data: T) -> T | None:
        from sqlmodel import select
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine, expire_on_commit=False) as session:
            pk_col = getattr(self._model, self._id_field)
            converted_id = self._convert_id(id)
            stmt = select(self._model).where(pk_col == converted_id)
            existing = (await session.exec(stmt)).first()
            if existing is None:
                return None

            update_data = data.model_dump(exclude={self._id_field})
            for key, value in update_data.items():
                setattr(existing, key, value)

            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing

    async def delete(self, id: str) -> bool:
        from sqlmodel import select
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine) as session:
            pk_col = getattr(self._model, self._id_field)
            stmt = select(self._model).where(pk_col == self._convert_id(id))
            existing = (await session.exec(stmt)).first()
            if existing is None:
                return False

            await session.delete(existing)
            await session.commit()
            return True


    async def reorder(self, ids: list[str]) -> None:
        if not self._has_position_field():
            return

        from sqlmodel import select
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(self._engine) as session:
            pk_col = getattr(self._model, self._id_field)
            for index, raw_id in enumerate(ids):
                converted_id = self._convert_id(raw_id)
                stmt = select(self._model).where(pk_col == converted_id)
                item = (await session.exec(stmt)).first()
                if item is not None:
                    setattr(item, self._position_field, index)
                    session.add(item)
            await session.commit()


async def create_tables(engine: Any) -> None:
    """Create all SQLModel tables using the given async engine.

    Safe to call multiple times (idempotent).
    """
    from sqlmodel import SQLModel

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
