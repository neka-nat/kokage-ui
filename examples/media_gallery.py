"""kokage-ui: Media Gallery example.

Demonstrates MediaField annotation for image/video/audio uploads,
high-level media components, and CRUDRouter with file_handler.

Run:
    uv run uvicorn examples.media_gallery:app --reload

Open http://localhost:8000/gallery in your browser.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from kokage_ui import (
    A,
    Card,
    Div,
    H1,
    H2,
    InMemoryStorage,
    KokageUI,
    Layout,
    MediaCard,
    MediaField,
    ModelForm,
    NavBar,
    Page,
    VideoPlayer,
    AudioPlayer,
    ImageGallery,
)

app = FastAPI()
ui = KokageUI(app)


@app.get("/")
def root():
    from starlette.responses import RedirectResponse

    return RedirectResponse("/gallery")

# --- Upload directory ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve uploaded files as static
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# --- File handler ---
async def handle_upload(field_name: str, file: UploadFile) -> str:
    """Save uploaded file and return its URL."""
    ext = Path(file.filename).suffix if file.filename else ""
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    dest = UPLOAD_DIR / filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return f"/uploads/{filename}"


# --- Models ---
class Photo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=100)
    image: Annotated[str, MediaField()] = ""


class MediaItem(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=100)
    image: Annotated[str, MediaField()] = ""
    video: Annotated[str, MediaField("video")] = ""
    audio: Annotated[str, MediaField("audio")] = ""


# --- Storage with sample data ---
photo_storage = InMemoryStorage(
    Photo,
    initial=[
        Photo(id="1", title="Mountain", image="https://picsum.photos/seed/mt/400/300"),
        Photo(id="2", title="Ocean", image="https://picsum.photos/seed/oc/400/300"),
        Photo(id="3", title="Forest", image="https://picsum.photos/seed/fr/400/300"),
    ],
)

media_storage = InMemoryStorage(MediaItem)

# --- Layout ---
layout = Layout(
    navbar=NavBar(
        start=A("Media Gallery", cls="btn btn-ghost text-xl", href="/gallery"),
        end=Div(
            A("Photos", cls="btn btn-ghost btn-sm", href="/photos"),
            A("Media Items", cls="btn btn-ghost btn-sm", href="/media"),
            A("Showcase", cls="btn btn-ghost btn-sm", href="/gallery"),
        ),
    ),
    title_suffix=" - Media Gallery",
    include_toast=True,
)

# --- CRUD routes ---
ui.crud(
    "/photos",
    model=Photo,
    storage=photo_storage,
    title="Photos",
    layout=layout,
    file_handler=handle_upload,
)

ui.crud(
    "/media",
    model=MediaItem,
    storage=media_storage,
    title="Media Items",
    layout=layout,
    file_handler=handle_upload,
)


# --- Gallery showcase page ---
@ui.page("/gallery", layout=layout, title="Gallery")
async def gallery_page():
    photos, _ = await photo_storage.list(limit=100)

    # Image gallery from stored photos
    gallery_images = [
        {"src": p.image, "alt": p.title, "caption": p.title}
        for p in photos
        if p.image
    ]

    # Demo media cards
    demo_cards = Div(
        MediaCard(
            src="https://picsum.photos/seed/card1/400/300",
            media_type="image",
            title="Sample Image Card",
        ),
        MediaCard(
            src="https://www.w3schools.com/html/mov_bbb.mp4",
            media_type="video",
            title="Sample Video Card",
        ),
        MediaCard(
            src="https://www.w3schools.com/html/horse.mp3",
            media_type="audio",
            title="Sample Audio Card",
        ),
        cls="grid grid-cols-1 md:grid-cols-3 gap-6",
    )

    # Video player demo
    video_section = Card(
        VideoPlayer(
            "https://www.w3schools.com/html/mov_bbb.mp4",
            poster="https://picsum.photos/seed/poster/800/450",
        ),
        title="Video Player",
    )

    # Audio player demo
    audio_section = Card(
        AudioPlayer("https://www.w3schools.com/html/horse.mp3"),
        title="Audio Player",
    )

    # Quick upload form
    upload_form = Card(
        ModelForm(
            Photo,
            action="/photos/new",
            exclude=["id"],
            submit_text="Upload Photo",
            submit_color="primary",
        ),
        title="Quick Upload",
    )

    return Div(
        H1("Media Gallery", cls="text-3xl font-bold mb-6"),

        H2("Photo Gallery", cls="text-2xl font-semibold mb-4"),
        ImageGallery(images=gallery_images, columns=3, gap="gap-4")
        if gallery_images
        else Div("No photos yet.", cls="text-gray-500 mb-4"),

        H2("Media Cards", cls="text-2xl font-semibold mb-4 mt-8"),
        demo_cards,

        Div(
            Div(video_section, cls="flex-1"),
            Div(audio_section, cls="flex-1"),
            cls="flex flex-col md:flex-row gap-6 mt-8",
        ),

        Div(upload_form, cls="max-w-lg mt-8"),

        cls="container mx-auto p-4",
    )
