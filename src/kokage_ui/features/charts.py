"""Chart.js chart component.

Renders a <canvas> with inline <script> for Chart.js configuration.
Provides typed Pydantic models for Chart.js data structures.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Literal

from markupsafe import Markup
from pydantic import BaseModel, ConfigDict

from kokage_ui.elements import Component


class Dataset(BaseModel):
    """A single Chart.js dataset.

    Args:
        data: Data points — numbers or {x, y} dicts for scatter/bubble.
        label: Dataset label shown in legends.
        backgroundColor: Fill color(s) — single string or per-point list.
        borderColor: Border color(s) — single string or per-point list.
        fill: Area fill — True, False, or fill target string.
        tension: Bezier curve tension for line charts (0 = straight).
        borderDash: Dash pattern [dash_length, gap_length].
        borderWidth: Border width in pixels.
        pointRadius: Point radius for line/radar/scatter charts.
        pointStyle: Point shape (circle, cross, rect, star, triangle, etc.).
        hidden: Hide this dataset initially.
        order: Drawing order (lower = drawn first).
        type: Override chart type for this dataset (mixed charts).
    """

    model_config = ConfigDict(extra="allow")

    data: list[int | float | dict[str, Any]]
    label: str = ""
    backgroundColor: str | list[str] = ""
    borderColor: str | list[str] = ""
    fill: bool | str | None = None
    tension: float | None = None
    borderDash: list[int] | None = None
    borderWidth: float | None = None
    pointRadius: float | None = None
    pointStyle: str | None = None
    hidden: bool | None = None
    order: int | None = None
    type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Chart.js-compatible dict, omitting unset fields."""
        d: dict[str, Any] = {"data": self.data}
        for key in (
            "label", "backgroundColor", "borderColor", "fill", "tension",
            "borderDash", "borderWidth", "pointRadius", "pointStyle",
            "hidden", "order", "type",
        ):
            val = getattr(self, key)
            if val is not None and val != "" and val != []:
                d[key] = val
        # Include extra fields (Chart.js-specific props not in schema)
        if self.model_extra:
            d.update(self.model_extra)
        return d


class ChartData(BaseModel):
    """Chart.js data configuration.

    Args:
        datasets: List of datasets to display.
        labels: Category labels for the x-axis (bar, line, pie, etc.).
    """

    datasets: list[Dataset]
    labels: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Chart.js-compatible dict."""
        d: dict[str, Any] = {
            "datasets": [ds.to_dict() for ds in self.datasets],
        }
        if self.labels is not None:
            d["labels"] = self.labels
        return d


class ChartOptions(BaseModel):
    """Chart.js options configuration.

    Args:
        responsive: Enable responsive resizing.
        plugins: Plugin options (title, legend, tooltip, etc.).
        scales: Axis scale options.
        animation: Animation configuration.
        interaction: Hover/tooltip interaction options.
        layout: Layout padding options.
    """

    model_config = ConfigDict(extra="allow")

    responsive: bool | None = None
    plugins: dict[str, Any] | None = None
    scales: dict[str, Any] | None = None
    animation: dict[str, Any] | bool | None = None
    interaction: dict[str, Any] | None = None
    layout: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Chart.js-compatible dict, omitting unset fields."""
        d: dict[str, Any] = {}
        for key in ("responsive", "plugins", "scales", "animation", "interaction", "layout"):
            val = getattr(self, key)
            if val is not None:
                d[key] = val
        if self.model_extra:
            d.update(self.model_extra)
        return d


class Chart(Component):
    """Chart.js chart rendered as a <canvas> with inline script.

    Args:
        type: Chart type (line, bar, pie, doughnut, radar, scatter).
        data: Chart.js data — ChartData model or plain dict.
        options: Chart.js options — ChartOptions model or plain dict.
        width: CSS width (default "100%").
        height: CSS height (default "400px").
        chart_id: Canvas element id (auto-generated if None).
        responsive: Merge responsive option into config (default True).
    """

    tag = "div"

    def __init__(
        self,
        *,
        type: str,
        data: ChartData | dict[str, Any],
        options: ChartOptions | dict[str, Any] | None = None,
        width: str = "100%",
        height: str = "400px",
        chart_id: str | None = None,
        responsive: bool = True,
        **attrs: Any,
    ) -> None:
        self._chart_type = type
        self._data = data.to_dict() if isinstance(data, ChartData) else data
        self._options = (
            options.to_dict() if isinstance(options, ChartOptions)
            else (options or {})
        )
        self._width = width
        self._height = height
        self._chart_id = chart_id or f"kokage-chart-{uuid.uuid4().hex[:8]}"
        self._responsive = responsive
        self._attrs = attrs

    def render(self) -> str:
        options = dict(self._options)
        if self._responsive:
            options.setdefault("responsive", True)

        config = {
            "type": self._chart_type,
            "data": self._data,
            "options": options,
        }
        config_json = json.dumps(config, ensure_ascii=False)
        canvas_id = self._chart_id

        script = (
            f"<script>(function(){{"
            f"var canvas=document.getElementById('{canvas_id}');"
            f"var existing=Chart.getChart(canvas);"
            f"if(existing)existing.destroy();"
            f"new Chart(canvas.getContext('2d'),{config_json});"
            f"}})()</script>"
        )

        from kokage_ui.elements import _render_attrs

        attrs = dict(self._attrs)
        style = f"width:{self._width};height:{self._height}"
        if "style" in attrs:
            style = f"{attrs['style']};{style}"
        attrs["style"] = style

        attr_str = _render_attrs(attrs)

        return Markup(
            f"<div{attr_str}>"
            f'<canvas id="{canvas_id}"></canvas>'
            f"{script}"
            f"</div>"
        )
