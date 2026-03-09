"""Tests for media field annotation and media components."""

from __future__ import annotations

from typing import Annotated, Optional
from unittest.mock import AsyncMock

import pytest
import dataclasses

from pydantic import BaseModel

from kokage_ui.elements import Audio, Canvas, Component, Picture, Source, Track, Video
from kokage_ui.fields.media import AudioPlayer, ImageGallery, MediaCard, MediaField, VideoPlayer
from kokage_ui.models import (
    ModelDetail,
    ModelForm,
    ModelTable,
    _extract_media_field,
    _field_to_component,
    _resolve_annotation,
)


# ========================================
# Test MediaField dataclass
# ========================================


class TestMediaField:
    def test_default_image(self):
        mf = MediaField()
        assert mf.media_type == "image"
        assert mf.accept is None
        assert mf.accept_str == "image/*"

    def test_video(self):
        mf = MediaField(media_type="video")
        assert mf.media_type == "video"
        assert mf.accept_str == "video/*"

    def test_audio(self):
        mf = MediaField(media_type="audio")
        assert mf.media_type == "audio"
        assert mf.accept_str == "audio/*"

    def test_custom_accept(self):
        mf = MediaField(media_type="image", accept=".png,.jpg")
        assert mf.accept_str == ".png,.jpg"

    def test_frozen(self):
        mf = MediaField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            mf.media_type = "video"  # type: ignore[misc]


# ========================================
# Test _resolve_annotation with Annotated
# ========================================


class TestResolveAnnotation:
    def test_plain_str(self):
        base, opt = _resolve_annotation(str)
        assert base is str
        assert opt is False

    def test_annotated_str(self):
        base, opt = _resolve_annotation(Annotated[str, MediaField()])
        assert base is str
        assert opt is False

    def test_optional_annotated(self):
        base, opt = _resolve_annotation(Optional[Annotated[str, MediaField()]])
        assert base is str
        assert opt is True

    def test_annotated_int(self):
        base, opt = _resolve_annotation(Annotated[int, "some marker"])
        assert base is int
        assert opt is False


# ========================================
# Test _extract_media_field
# ========================================


class TestExtractMediaField:
    def test_media_field_present(self):
        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        fi = M.model_fields["image"]
        mf = _extract_media_field(fi)
        assert mf is not None
        assert mf.media_type == "image"

    def test_no_media_field(self):
        class M(BaseModel):
            name: str = ""

        fi = M.model_fields["name"]
        assert _extract_media_field(fi) is None

    def test_video_field(self):
        class M(BaseModel):
            clip: Annotated[str, MediaField(media_type="video")] = ""

        fi = M.model_fields["clip"]
        mf = _extract_media_field(fi)
        assert mf is not None
        assert mf.media_type == "video"


# ========================================
# Test _field_to_component with MediaField
# ========================================


class TestFieldToComponent:
    def test_image_file_input(self):
        class M(BaseModel):
            photo: Annotated[str, MediaField()] = ""

        fi = M.model_fields["photo"]
        comp = _field_to_component("photo", fi)
        html = comp.render()
        assert 'type="file"' in html
        assert 'accept="image/*"' in html
        assert "file-input" in html

    def test_video_file_input(self):
        class M(BaseModel):
            video: Annotated[str, MediaField(media_type="video")] = ""

        fi = M.model_fields["video"]
        comp = _field_to_component("video", fi)
        html = comp.render()
        assert 'type="file"' in html
        assert 'accept="video/*"' in html

    def test_audio_file_input(self):
        class M(BaseModel):
            audio: Annotated[str, MediaField(media_type="audio")] = ""

        fi = M.model_fields["audio"]
        comp = _field_to_component("audio", fi)
        html = comp.render()
        assert 'type="file"' in html
        assert 'accept="audio/*"' in html

    def test_edit_mode_image_preview(self):
        class M(BaseModel):
            photo: Annotated[str, MediaField()] = ""

        fi = M.model_fields["photo"]
        comp = _field_to_component("photo", fi, value="/img/test.jpg")
        html = comp.render()
        assert "<img" in html
        assert "/img/test.jpg" in html
        assert 'type="file"' in html

    def test_edit_mode_video_preview(self):
        class M(BaseModel):
            clip: Annotated[str, MediaField(media_type="video")] = ""

        fi = M.model_fields["clip"]
        comp = _field_to_component("clip", fi, value="/vid/test.mp4")
        html = comp.render()
        assert "<video" in html
        assert "/vid/test.mp4" in html

    def test_edit_mode_audio_preview(self):
        class M(BaseModel):
            sound: Annotated[str, MediaField(media_type="audio")] = ""

        fi = M.model_fields["sound"]
        comp = _field_to_component("sound", fi, value="/audio/test.mp3")
        html = comp.render()
        assert "<audio" in html
        assert "/audio/test.mp3" in html

    def test_no_preview_when_empty_value(self):
        class M(BaseModel):
            photo: Annotated[str, MediaField()] = ""

        fi = M.model_fields["photo"]
        comp = _field_to_component("photo", fi, value="")
        html = comp.render()
        assert "<img" not in html
        assert 'type="file"' in html


# ========================================
# Test ModelForm enctype auto-detection
# ========================================


class TestModelFormEnctype:
    def test_enctype_set_with_media(self):
        class M(BaseModel):
            name: str = ""
            image: Annotated[str, MediaField()] = ""

        form = ModelForm(M, action="/upload")
        html = form.render()
        assert 'enctype="multipart/form-data"' in html

    def test_no_enctype_without_media(self):
        class M(BaseModel):
            name: str = ""

        form = ModelForm(M, action="/submit")
        html = form.render()
        assert "enctype" not in html

    def test_enctype_not_overridden(self):
        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        form = ModelForm(M, action="/upload", enctype="custom/type")
        html = form.render()
        assert 'enctype="custom/type"' in html


# ========================================
# Test _process_media_fields
# ========================================


class TestProcessMediaFields:
    @pytest.mark.anyio
    async def test_file_upload_with_handler(self):
        from kokage_ui.data.crud import _process_media_fields

        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        mock_file = AsyncMock()
        mock_file.filename = "photo.jpg"
        handler = AsyncMock(return_value="/uploads/photo.jpg")

        raw_data: dict = {}
        form_data = {"image": mock_file}

        await _process_media_fields(M, raw_data, form_data, [], handler)
        assert raw_data["image"] == "/uploads/photo.jpg"
        handler.assert_awaited_once_with("image", mock_file)

    @pytest.mark.anyio
    async def test_no_handler_sets_empty(self):
        from kokage_ui.data.crud import _process_media_fields

        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        mock_file = AsyncMock()
        mock_file.filename = "photo.jpg"

        raw_data: dict = {}
        form_data = {"image": mock_file}

        await _process_media_fields(M, raw_data, form_data, [], None)
        assert raw_data["image"] == ""

    @pytest.mark.anyio
    async def test_keep_existing_on_no_upload(self):
        from kokage_ui.data.crud import _process_media_fields

        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        existing = M(image="/old/image.jpg")
        mock_file = AsyncMock()
        mock_file.filename = ""  # empty filename = no file uploaded

        raw_data: dict = {}
        form_data = {"image": mock_file}

        await _process_media_fields(M, raw_data, form_data, [], None, existing_instance=existing)
        assert raw_data["image"] == "/old/image.jpg"

    @pytest.mark.anyio
    async def test_excluded_field_skipped(self):
        from kokage_ui.data.crud import _process_media_fields

        class M(BaseModel):
            image: Annotated[str, MediaField()] = ""

        raw_data: dict = {}
        form_data = {}

        await _process_media_fields(M, raw_data, form_data, ["image"], None)
        assert "image" not in raw_data


# ========================================
# Test HTML elements
# ========================================


class TestHTMLElements:
    def test_video(self):
        v = Video(Source(src="test.mp4"), controls=True)
        html = v.render()
        assert "<video" in html
        assert "</video>" in html
        assert 'src="test.mp4"' in html
        assert "controls" in html

    def test_audio(self):
        a = Audio(Source(src="test.mp3"), controls=True)
        html = a.render()
        assert "<audio" in html
        assert "</audio>" in html
        assert 'src="test.mp3"' in html

    def test_source_void(self):
        s = Source(src="test.mp4", type="video/mp4")
        html = s.render()
        assert "<source" in html
        assert "/>" in html

    def test_track_void(self):
        t = Track(src="subs.vtt", kind="subtitles")
        html = t.render()
        assert "<track" in html
        assert "/>" in html

    def test_picture(self):
        p = Picture(Source(srcset="large.jpg", media="(min-width: 800px)"))
        html = p.render()
        assert "<picture>" in html
        assert "</picture>" in html

    def test_canvas(self):
        c = Canvas(id="my-canvas", width="400", height="300")
        html = c.render()
        assert "<canvas" in html
        assert "</canvas>" in html


# ========================================
# Test high-level components
# ========================================


class TestHighLevelComponents:
    def test_video_player(self):
        vp = VideoPlayer("test.mp4", poster="thumb.jpg")
        html = vp.render()
        assert "<video" in html
        assert 'poster="thumb.jpg"' in html
        assert "controls" in html

    def test_audio_player(self):
        ap = AudioPlayer("test.mp3")
        html = ap.render()
        assert "<audio" in html
        assert "controls" in html

    def test_image_gallery(self):
        images = [
            {"src": "a.jpg", "alt": "A", "caption": "Image A"},
            {"src": "b.jpg", "alt": "B"},
        ]
        ig = ImageGallery(images=images, columns=2)
        html = ig.render()
        assert "a.jpg" in html
        assert "b.jpg" in html
        assert "Image A" in html
        assert "grid-cols-2" in html

    def test_media_card_image(self):
        mc = MediaCard(src="photo.jpg", media_type="image", title="My Photo")
        html = mc.render()
        assert "<img" in html
        assert "photo.jpg" in html
        assert "My Photo" in html

    def test_media_card_video(self):
        mc = MediaCard(src="clip.mp4", media_type="video")
        html = mc.render()
        assert "<video" in html
        assert "clip.mp4" in html

    def test_media_card_audio(self):
        mc = MediaCard(src="song.mp3", media_type="audio")
        html = mc.render()
        assert "<audio" in html
        assert "song.mp3" in html


# ========================================
# Test ModelTable/ModelDetail with media
# ========================================


class TestModelTableMediaRendering:
    def test_image_rendered_in_table(self):
        class M(BaseModel):
            photo: Annotated[str, MediaField()] = ""

        row = M(photo="/img/test.jpg")
        table = ModelTable(M, rows=[row])
        html = table.render()
        assert "<img" in html
        assert "/img/test.jpg" in html

    def test_video_badge_in_table(self):
        class M(BaseModel):
            clip: Annotated[str, MediaField(media_type="video")] = ""

        row = M(clip="/vid/test.mp4")
        table = ModelTable(M, rows=[row])
        html = table.render()
        assert "Video" in html

    def test_detail_image_preview(self):
        class M(BaseModel):
            photo: Annotated[str, MediaField()] = ""

        instance = M(photo="/img/test.jpg")
        detail = ModelDetail(instance)
        html = detail.render()
        assert "<img" in html
        assert "/img/test.jpg" in html
