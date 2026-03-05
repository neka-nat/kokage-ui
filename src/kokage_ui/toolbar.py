"""DevToolbar middleware for kokage-ui.

Provides a debug toolbar that displays route info, request details,
and htmx debugging tools. Injected into HTML responses automatically
when debug=True.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class DevToolbarMiddleware(BaseHTTPMiddleware):
    """Injects a dev toolbar into full-page HTML responses."""

    def __init__(self, app, *, routes=None):
        super().__init__(app)
        self._routes = routes or []

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and "text/html" in content_type:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            body_str = body.decode("utf-8")

            if "</body>" in body_str:
                toolbar = _render_toolbar(request, body_str, elapsed, self._routes)
                body_str = body_str.replace("</body>", toolbar + "\n</body>")

            headers = dict(response.headers)
            headers.pop("content-length", None)
            return Response(
                content=body_str.encode("utf-8"),
                status_code=response.status_code,
                headers=headers,
                media_type="text/html",
            )

        return response


def _render_toolbar(
    request: Request,
    body: str,
    elapsed_ms: float,
    routes: list[dict],
) -> str:
    """Generate DevToolbar HTML string."""
    method = request.method
    path = str(request.url.path)
    html_size = len(body.encode("utf-8"))
    is_htmx = "hx-request" in request.headers

    size_str = f"{html_size / 1024:.1f}KB"

    query_params = dict(request.query_params)
    htmx_headers = {k: v for k, v in request.headers.items() if k.startswith("hx-")}
    all_headers = dict(request.headers.items())

    # Routes table rows
    route_rows = ""
    for r in routes:
        methods_str = ", ".join(r.get("methods", []))
        r_path = r.get("path", "")
        r_type = r.get("type", "")
        r_name = r.get("name", "")
        is_current = r_path == path
        highlight = "background:#570df8;color:#fff;" if is_current else ""
        current_mark = " ← current" if is_current else ""
        route_rows += (
            f'<tr style="{highlight}">'
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{methods_str}</td>"
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{r_path}</td>"
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{r_type}</td>"
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{r_name}{current_mark}</td>"
            f"</tr>"
        )

    # Query params rows
    query_rows = ""
    if query_params:
        for k, v in query_params.items():
            query_rows += (
                f"<tr>"
                f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{k}</td>"
                f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{v}</td>"
                f"</tr>"
            )
    else:
        query_rows = '<tr><td style="padding:4px 12px;color:#666;" colspan="2">No query parameters</td></tr>'

    # htmx headers rows
    htmx_header_rows = ""
    if htmx_headers:
        for k, v in htmx_headers.items():
            htmx_header_rows += (
                f"<tr>"
                f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{k}</td>"
                f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{v}</td>"
                f"</tr>"
            )
    else:
        htmx_header_rows = '<tr><td style="padding:4px 12px;color:#666;" colspan="2">No htmx headers</td></tr>'

    # All headers rows
    header_rows = ""
    for k, v in all_headers.items():
        header_rows += (
            f"<tr>"
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;\">{k}</td>"
            f"<td style=\"padding:4px 12px;border-bottom:1px solid #333;word-break:break-all;\">{v}</td>"
            f"</tr>"
        )

    htmx_indicator = "htmx: ✓" if is_htmx else "htmx: ✗"

    return f'''<div id="kokage-devtoolbar" style="position:fixed;bottom:0;left:0;right:0;z-index:99999;font-family:monospace;font-size:13px;color:#a6adba;background:#1d232a;border-top:2px solid #570df8;">
  <div id="kokage-tb-toggle" style="text-align:right;padding:4px 12px;cursor:pointer;" onclick="document.getElementById('kokage-tb-panel').style.display=document.getElementById('kokage-tb-panel').style.display==='none'?'block':'none'">🔧 kokage</div>
  <div id="kokage-tb-panel" style="display:none;">
    <div id="kokage-tb-info" style="display:flex;gap:24px;padding:6px 12px;background:#181e24;border-bottom:1px solid #333;">
      <span style="color:#fff;font-weight:bold;">{method} {path}</span>
      <span>⏱ {elapsed_ms:.1f}ms</span>
      <span>📄 {size_str}</span>
      <span>{htmx_indicator}</span>
    </div>
    <div style="padding:4px 12px;border-bottom:1px solid #333;">
      <button class="kokage-tab-btn" onclick="kokageShowTab('routes')" style="background:none;border:none;color:#570df8;cursor:pointer;padding:4px 12px;font-family:monospace;font-size:13px;font-weight:bold;">Routes</button>
      <button class="kokage-tab-btn" onclick="kokageShowTab('request')" style="background:none;border:none;color:#a6adba;cursor:pointer;padding:4px 12px;font-family:monospace;font-size:13px;">Request</button>
      <button class="kokage-tab-btn" onclick="kokageShowTab('htmx')" style="background:none;border:none;color:#a6adba;cursor:pointer;padding:4px 12px;font-family:monospace;font-size:13px;">htmx</button>
    </div>
    <div style="max-height:320px;overflow-y:auto;">
      <div id="kokage-tab-routes" style="display:block;padding:8px 12px;">
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr style="color:#570df8;">
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Method</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Path</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Type</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Handler</th>
          </tr></thead>
          <tbody>{route_rows}</tbody>
        </table>
      </div>
      <div id="kokage-tab-request" style="display:none;padding:8px 12px;">
        <h4 style="margin:0 0 8px;color:#570df8;">Query Parameters</h4>
        <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
          <thead><tr style="color:#570df8;">
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Key</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Value</th>
          </tr></thead>
          <tbody>{query_rows}</tbody>
        </table>
        <h4 style="margin:0 0 8px;color:#570df8;">htmx Headers</h4>
        <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
          <thead><tr style="color:#570df8;">
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Header</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Value</th>
          </tr></thead>
          <tbody>{htmx_header_rows}</tbody>
        </table>
        <h4 style="margin:0 0 8px;color:#570df8;">All Headers</h4>
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr style="color:#570df8;">
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Header</th>
            <th style="text-align:left;padding:4px 12px;border-bottom:2px solid #333;">Value</th>
          </tr></thead>
          <tbody>{header_rows}</tbody>
        </table>
      </div>
      <div id="kokage-tab-htmx" style="display:none;padding:8px 12px;">
        <p style="margin:0 0 8px;">Toggle <code style="background:#333;padding:2px 6px;border-radius:3px;">htmx.logAll()</code> to log all htmx events to the browser console.</p>
        <button id="kokage-htmx-log-btn" onclick="kokageToggleHtmxLog()" style="background:#570df8;color:#fff;border:none;padding:6px 16px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:13px;">Enable htmx.logAll()</button>
        <p style="margin:12px 0 4px;color:#666;">Key htmx events: htmx:configRequest, htmx:beforeRequest, htmx:afterRequest, htmx:beforeSwap, htmx:afterSwap, htmx:responseError</p>
      </div>
    </div>
  </div>
</div>
<script>
function kokageShowTab(name){{
  var tabs=["routes","request","htmx"];
  for(var i=0;i<tabs.length;i++){{
    document.getElementById("kokage-tab-"+tabs[i]).style.display=tabs[i]===name?"block":"none";
  }}
  var btns=document.querySelectorAll(".kokage-tab-btn");
  for(var j=0;j<btns.length;j++){{
    btns[j].style.color=btns[j].textContent.toLowerCase()===name?"#570df8":"#a6adba";
    btns[j].style.fontWeight=btns[j].textContent.toLowerCase()===name?"bold":"normal";
  }}
}}
var _kokageHtmxLog=false;
function kokageToggleHtmxLog(){{
  _kokageHtmxLog=!_kokageHtmxLog;
  var btn=document.getElementById("kokage-htmx-log-btn");
  if(_kokageHtmxLog){{
    if(typeof htmx!=="undefined")htmx.logAll();
    btn.textContent="Disable htmx.logAll()";
    btn.style.background="#e53e3e";
  }}else{{
    if(typeof htmx!=="undefined")htmx.logger=null;
    btn.textContent="Enable htmx.logAll()";
    btn.style.background="#570df8";
  }}
}}
</script>'''
