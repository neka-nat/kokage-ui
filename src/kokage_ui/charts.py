"""Chart.js chart component.

Renders a <canvas> with inline <script> for Chart.js configuration.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from markupsafe import Markup

from kokage_ui.elements import Component


class Chart(Component):
    """Chart.js chart rendered as a <canvas> with inline script.

    Args:
        type: Chart type (line, bar, pie, doughnut, radar, scatter).
        data: Chart.js data dict (labels + datasets).
        options: Chart.js options dict.
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
        data: dict[str, Any],
        options: dict[str, Any] | None = None,
        width: str = "100%",
        height: str = "400px",
        chart_id: str | None = None,
        responsive: bool = True,
        **attrs: Any,
    ) -> None:
        self._chart_type = type
        self._data = data
        self._options = options or {}
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
