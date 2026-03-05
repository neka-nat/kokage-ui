"""Media field annotation and high-level media components.

Provides MediaField for marking Pydantic model fields as media (image/video/audio),
and high-level DaisyUI-styled media display components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from kokage_ui.elements import Component, Div, Img, Source

# Lazy imports to avoid circular dependencies
_Video = None
_Audio = None


def _get_video_cls() -> type[Component]:
    global _Video
    if _Video is None:
        from kokage_ui.elements import Video

        _Video = Video
    return _Video


def _get_audio_cls() -> type[Component]:
    global _Audio
    if _Audio is None:
        from kokage_ui.elements import Audio

        _Audio = Audio
    return _Audio


@dataclass(frozen=True)
class MediaField:
    """Annotated marker for media fields in Pydantic models.

    Usage:
        class Product(BaseModel):
            image: Annotated[str, MediaField()] = ""
            video: Annotated[str, MediaField("video")] = ""
            audio: Annotated[str, MediaField("audio")] = ""
    """

    media_type: Literal["image", "video", "audio"] = "image"
    accept: str | None = None

    @property
    def accept_str(self) -> str:
        if self.accept:
            return self.accept
        return f"{self.media_type}/*"


class VideoPlayer(Component):
    """DaisyUI styled video player."""

    tag = "div"

    def __init__(
        self,
        src: str,
        *,
        poster: str | None = None,
        controls: bool = True,
        width: str = "100%",
        **attrs: Any,
    ) -> None:
        Video = _get_video_cls()
        video_attrs: dict[str, Any] = {"style": f"width:{width}"}
        if poster:
            video_attrs["poster"] = poster
        if controls:
            video_attrs["controls"] = True
        video = Video(Source(src=src), **video_attrs)
        attrs.setdefault("cls", "rounded-box overflow-hidden")
        super().__init__(video, **attrs)


class AudioPlayer(Component):
    """DaisyUI styled audio player."""

    tag = "div"

    def __init__(self, src: str, *, controls: bool = True, **attrs: Any) -> None:
        Audio = _get_audio_cls()
        audio_attrs: dict[str, Any] = {"cls": "w-full"}
        if controls:
            audio_attrs["controls"] = True
        audio = Audio(Source(src=src), **audio_attrs)
        attrs.setdefault("cls", "p-2")
        super().__init__(audio, **attrs)


class ImageGallery(Component):
    """Grid gallery of images with optional lightbox.

    Args:
        images: List of dicts with "src", optional "alt" and "caption".
        columns: Number of grid columns (default 3).
        gap: Tailwind gap class (default "gap-4").
    """

    tag = "div"

    def __init__(
        self,
        *,
        images: list[dict[str, str]],
        columns: int = 3,
        gap: str = "gap-4",
        **attrs: Any,
    ) -> None:
        cards: list[Any] = []
        for img_data in images:
            src = img_data.get("src", "")
            alt = img_data.get("alt", "")
            caption = img_data.get("caption", "")
            children: list[Any] = [
                Img(src=src, alt=alt, cls="w-full rounded"),
            ]
            if caption:
                children.append(
                    Div(caption, cls="text-sm text-center mt-1 opacity-70")
                )
            cards.append(Div(*children, cls="card bg-base-100 shadow-sm"))
        attrs.setdefault("cls", f"grid grid-cols-{columns} {gap}")
        super().__init__(*cards, **attrs)


class MediaCard(Component):
    """Card with media preview (image/video/audio).

    Args:
        src: Media source URL.
        media_type: One of "image", "video", "audio".
        title: Optional card title.
    """

    tag = "div"

    def __init__(
        self,
        *,
        src: str,
        media_type: str = "image",
        title: str | None = None,
        **attrs: Any,
    ) -> None:
        children: list[Any] = []
        if media_type == "image":
            children.append(Img(src=src, cls="w-full rounded-t-box", alt=title or ""))
        elif media_type == "video":
            Video = _get_video_cls()
            children.append(
                Video(Source(src=src), controls=True, cls="w-full rounded-t-box")
            )
        elif media_type == "audio":
            Audio = _get_audio_cls()
            children.append(
                Audio(Source(src=src), controls=True, cls="w-full")
            )
        if title:
            children.append(
                Div(Div(title, cls="card-title"), cls="card-body")
            )
        attrs.setdefault("cls", "card bg-base-100 shadow-md")
        super().__init__(*children, **attrs)
