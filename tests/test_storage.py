"""Tests for SQLModelStorage."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel

from kokage_ui import KokageUI, SQLModelStorage
from kokage_ui.crud import CRUDRouter
from kokage_ui.storage import create_tables


# ---- Test models ----


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    is_active: bool = True


class StringItem(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str = ""


# ---- Fixtures ----


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def storage(engine):
    return SQLModelStorage(Item, engine)


@pytest.fixture
def str_storage(engine):
    return SQLModelStorage(StringItem, engine)


# ---- Helper ----


async def _seed(storage: SQLModelStorage, items: list) -> list:
    created = []
    for item in items:
        created.append(await storage.create(item))
    return created


# ========================================
# List tests
# ========================================


class TestList:
    async def test_empty(self, storage):
        items, total = await storage.list()
        assert items == []
        assert total == 0

    async def test_all_items(self, storage):
        await _seed(storage, [
            Item(name="Widget", price=9.99),
            Item(name="Gadget", price=19.99),
        ])
        items, total = await storage.list()
        assert total == 2
        assert len(items) == 2

    async def test_pagination_skip_limit(self, storage):
        await _seed(storage, [
            Item(name="A", price=1),
            Item(name="B", price=2),
            Item(name="C", price=3),
        ])
        items, total = await storage.list(skip=1, limit=1)
        assert total == 3
        assert len(items) == 1
        assert items[0].name == "B"

    async def test_search_case_insensitive(self, storage):
        await _seed(storage, [
            Item(name="Widget", price=9.99),
            Item(name="Gadget", price=19.99),
        ])
        items, total = await storage.list(search="widget")
        assert total == 1
        assert items[0].name == "Widget"

    async def test_search_partial(self, storage):
        await _seed(storage, [
            Item(name="Widget", price=9.99),
            Item(name="Gadget", price=19.99),
        ])
        items, total = await storage.list(search="dget")
        assert total == 2
        assert len(items) == 2

    async def test_search_no_match(self, storage):
        await _seed(storage, [Item(name="Widget", price=9.99)])
        items, total = await storage.list(search="zzz")
        assert total == 0
        assert items == []


# ========================================
# Get tests
# ========================================


class TestGet:
    async def test_existing(self, storage):
        created = await storage.create(Item(name="Widget", price=9.99))
        result = await storage.get(str(created.id))
        assert result is not None
        assert result.name == "Widget"

    async def test_nonexistent(self, storage):
        result = await storage.get("9999")
        assert result is None

    async def test_str_to_int_conversion(self, storage):
        created = await storage.create(Item(name="Widget", price=9.99))
        result = await storage.get(str(created.id))
        assert result is not None
        assert result.id == created.id


# ========================================
# Create tests
# ========================================


class TestCreate:
    async def test_auto_increment_id(self, storage):
        item = await storage.create(Item(name="Widget", price=9.99))
        assert item.id is not None
        assert item.id > 0

    async def test_round_trip(self, storage):
        created = await storage.create(Item(name="Gadget", price=19.99, is_active=False))
        fetched = await storage.get(str(created.id))
        assert fetched is not None
        assert fetched.name == "Gadget"
        assert fetched.price == 19.99
        assert fetched.is_active is False


# ========================================
# Update tests
# ========================================


class TestUpdate:
    async def test_existing(self, storage):
        created = await storage.create(Item(name="Widget", price=9.99))
        updated = await storage.update(
            str(created.id),
            Item(name="Updated Widget", price=12.99),
        )
        assert updated is not None
        assert updated.name == "Updated Widget"
        assert updated.price == 12.99

    async def test_preserves_id(self, storage):
        created = await storage.create(Item(name="Widget", price=9.99))
        original_id = created.id
        updated = await storage.update(
            str(created.id),
            Item(name="Updated", price=5.0),
        )
        assert updated is not None
        assert updated.id == original_id

    async def test_nonexistent(self, storage):
        result = await storage.update("9999", Item(name="X", price=1.0))
        assert result is None


# ========================================
# Delete tests
# ========================================


class TestDelete:
    async def test_existing(self, storage):
        created = await storage.create(Item(name="Widget", price=9.99))
        assert await storage.delete(str(created.id)) is True
        assert await storage.get(str(created.id)) is None

    async def test_nonexistent(self, storage):
        assert await storage.delete("9999") is False


# ========================================
# String PK tests
# ========================================


class TestStringPK:
    async def test_str_id_passthrough(self, str_storage):
        item = await str_storage.create(StringItem(id="abc", title="Hello"))
        assert item.id == "abc"

        fetched = await str_storage.get("abc")
        assert fetched is not None
        assert fetched.title == "Hello"

    async def test_str_id_update(self, str_storage):
        await str_storage.create(StringItem(id="abc", title="Hello"))
        updated = await str_storage.update("abc", StringItem(id="abc", title="World"))
        assert updated is not None
        assert updated.title == "World"

    async def test_str_id_delete(self, str_storage):
        await str_storage.create(StringItem(id="abc", title="Hello"))
        assert await str_storage.delete("abc") is True
        assert await str_storage.get("abc") is None


# ========================================
# create_tables tests
# ========================================


class TestCreateTables:
    async def test_idempotent(self):
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        await create_tables(engine)
        await create_tables(engine)  # should not raise
        await engine.dispose()


# ========================================
# CRUDRouter integration
# ========================================


class TestCRUDRouterIntegration:
    @pytest.fixture
    def app_and_client(self, engine):
        app = FastAPI()
        ui = KokageUI(app)
        storage = SQLModelStorage(Item, engine)
        CRUDRouter(app, "/items", Item, storage)
        client = TestClient(app)
        return app, client, storage

    def test_list_page(self, app_and_client):
        _, client, _ = app_and_client
        resp = client.get("/items")
        assert resp.status_code == 200
        assert "Items" in resp.text

    def test_create_page(self, app_and_client):
        _, client, _ = app_and_client
        resp = client.get("/items/new")
        assert resp.status_code == 200
        assert "New" in resp.text

    def test_create_and_list(self, app_and_client):
        _, client, _ = app_and_client
        resp = client.post(
            "/items/new",
            data={"name": "TestItem", "price": "5.99"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Verify item appears in list
        resp = client.get("/items")
        assert "TestItem" in resp.text
