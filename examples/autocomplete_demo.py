"""kokage-ui: Autocomplete / Combobox demo.

Run:
    uv run uvicorn examples.autocomplete_demo:app --reload

Open http://localhost:8000 in your browser.
"""

from fastapi import FastAPI

from kokage_ui import (
    Autocomplete,
    Card,
    DaisyButton,
    Div,
    Form,
    H1,
    KokageUI,
    Page,
    autocomplete_option,
)

app = FastAPI()
ui = KokageUI(app)

# Sample data
USERS = [
    {"id": 1, "name": "Alice Johnson"},
    {"id": 2, "name": "Bob Smith"},
    {"id": 3, "name": "Charlie Brown"},
    {"id": 4, "name": "Diana Prince"},
    {"id": 5, "name": "Edward Norton"},
    {"id": 6, "name": "Fiona Apple"},
    {"id": 7, "name": "George Lucas"},
    {"id": 8, "name": "Hannah Montana"},
    {"id": 9, "name": "Ivan Drago"},
    {"id": 10, "name": "Julia Roberts"},
]


@ui.page("/")
def home():
    return Page(
        Card(
            H1("Autocomplete Demo"),
            Form(
                Autocomplete(
                    name="user_id",
                    search_url="/api/users/search",
                    label="Select User",
                    placeholder="Type to search users...",
                    min_chars=1,
                ),
                DaisyButton("Submit", color="primary", type="submit", cls="mt-4"),
                method="post",
                action="/submit",
            ),
            title="User Search",
        ),
        title="Autocomplete Demo",
    )


@ui.fragment("/api/users/search")
def search_users(q: str = ""):
    if not q:
        return []
    matches = [u for u in USERS if q.lower() in u["name"].lower()]
    return Div(*[autocomplete_option(str(u["id"]), u["name"]) for u in matches])


@ui.page("/submit")
def submit(user_id: str = ""):
    user = next((u for u in USERS if str(u["id"]) == user_id), None)
    name = user["name"] if user else "Unknown"
    return Page(
        Card(
            H1(f"Selected: {name} (ID: {user_id})"),
            DaisyButton("Back", color="ghost", onclick="history.back()"),
            title="Result",
        ),
        title="Result",
    )
