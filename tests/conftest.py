"""Shared test fixtures and models."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.testclient import TestClient

from kokage_ui import InMemoryStorage, KokageUI


# ---- Common test models ----


class SimpleItem(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    price: float = Field(ge=0, default=0.0)
    is_active: bool = True


# ---- Fixtures ----


@pytest.fixture
def simple_items() -> list[SimpleItem]:
    return [
        SimpleItem(id="1", name="Alpha", price=10.0),
        SimpleItem(id="2", name="Beta", price=20.0),
        SimpleItem(id="3", name="Gamma", price=30.0),
    ]


@pytest.fixture
def simple_storage(simple_items) -> InMemoryStorage:
    return InMemoryStorage(SimpleItem, initial=simple_items)


@pytest.fixture
def crud_app(simple_storage) -> FastAPI:
    app = FastAPI()
    ui = KokageUI(app)
    ui.crud("/items", model=SimpleItem, storage=simple_storage, title="Items")
    return app


@pytest.fixture
def crud_client(crud_app) -> TestClient:
    return TestClient(crud_app)
