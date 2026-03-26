"""AI Agent dashboard component with tool call visualization.

Provides AgentView for rendering an agent execution dashboard with
SSE streaming, tool call panels, status bar, and metrics display.
AgentEvent defines a framework-agnostic event type for LLM agent integration.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from pydantic import BaseModel
from typing import Any

from markupsafe import escape
from starlette.responses import StreamingResponse

from kokage_ui.ai.preview import JS_PREVIEW_RENDERER, render_preview
from kokage_ui.elements import Component, _render_attrs


class ToolCall(BaseModel):
    """A single tool call record.

    Args:
        name: Tool function name.
        input: Tool input arguments.
        result: Tool execution result.
        call_id: Unique identifier for this call.
    """

    name: str
    input: dict | str = ""
    result: str = ""
    call_id: str = ""
    preview_hint: str = ""


class AgentMessage(BaseModel):
    """A message in the agent conversation.

    Args:
        role: Message role — "user" or "assistant".
        content: Message text content.
        tool_calls: List of tool calls (assistant messages).
        name: Optional display name override.
    """

    role: str
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    name: str | None = None


class AgentEvent(BaseModel):
    """SSE event for agent streaming.

    Args:
        type: Event type — "text", "tool_call", "tool_result",
              "status", "error", or "done".
        content: Text content (for text, status, error events).
        tool_name: Tool function name (for tool_call).
        tool_input: Tool input arguments (for tool_call).
        call_id: Unique call identifier (for tool_call, tool_result).
        result: Tool execution result (for tool_result).
        preview_hint: Content type hint for rich preview (for tool_result).
        metrics: Execution metrics (for done event).
    """

    type: str
    content: str = ""
    tool_name: str = ""
    tool_input: dict | str = ""
    call_id: str = ""
    result: str = ""
    preview_hint: str = ""
    metrics: dict | None = None

    def to_dict(self) -> dict:
        """Convert to dict, omitting empty fields."""
        d: dict[str, Any] = {"type": self.type}
        if self.content:
            d["content"] = self.content
        if self.tool_name:
            d["tool_name"] = self.tool_name
        if self.tool_input:
            d["tool_input"] = self.tool_input
        if self.call_id:
            d["call_id"] = self.call_id
        if self.result:
            d["result"] = self.result
        if self.preview_hint:
            d["preview_hint"] = self.preview_hint
        if self.metrics is not None:
            d["metrics"] = self.metrics
        return d


def agent_stream(generator: AsyncIterator[AgentEvent]) -> StreamingResponse:
    """Convert an async AgentEvent generator to an SSE StreamingResponse.

    Each event is sent as a Server-Sent Event with JSON payload.

    Args:
        generator: Async iterator yielding AgentEvent instances.

    Returns:
        A StreamingResponse with ``text/event-stream`` content type.
    """

    async def event_stream():
        async for event in generator:
            yield f"data: {json.dumps(event.to_dict(), ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _render_tool_collapse(tc: ToolCall, expanded: bool = False) -> str:
    """Render a ToolCall as a DaisyUI collapse panel."""
    name_escaped = escape(tc.name)
    input_str = tc.input if isinstance(tc.input, str) else json.dumps(tc.input, ensure_ascii=False, indent=2)
    input_escaped = escape(input_str)
    checked = " checked" if expanded else ""

    html = (
        f'<div class="collapse collapse-arrow bg-base-200 my-2">'
        f'<input type="checkbox"{checked} />'
        f'<div class="collapse-title font-medium text-sm">'
        f'🔧 Tool: {name_escaped}()'
        f"</div>"
        f'<div class="collapse-content">'
        f'<div class="text-xs">'
        f'<div class="font-semibold">Input:</div>'
        f'<pre class="bg-base-300 p-2 rounded mt-1 whitespace-pre-wrap">{input_escaped}</pre>'
    )
    if tc.result:
        result_html = render_preview(tc.result, hint=tc.preview_hint)
        html += (
            f'<div class="font-semibold mt-2">Result:</div>'
            f"{result_html}"
        )
    html += "</div></div></div>"
    return html


def _render_agent_bubble(
    msg: AgentMessage,
    user_name: str,
    agent_name: str,
    tool_expanded: bool = False,
) -> str:
    """Render a single AgentMessage as a DaisyUI chat bubble."""
    escaped_content = escape(msg.content)

    if msg.role == "user":
        name = escape(msg.name or user_name)
        return (
            f'<div class="chat chat-end">'
            f'<div class="chat-header">{name}</div>'
            f'<div class="chat-bubble chat-bubble-primary">{escaped_content}</div>'
            f"</div>"
        )
    else:
        name = escape(msg.name or agent_name)
        tool_html = "".join(
            _render_tool_collapse(tc, expanded=tool_expanded)
            for tc in msg.tool_calls
        ) if msg.tool_calls else ""

        return (
            f'<div class="chat chat-start">'
            f'<div class="chat-header">{name}</div>'
            f'<div class="chat-bubble prose">'
            f"{tool_html}"
            f"{escaped_content}"
            f"</div>"
            f"</div>"
        )


class AgentView(Component):
    """AI Agent dashboard with tool call visualization.

    Renders a complete agent interface: status bar, message area with
    tool call panels, metrics bar, input form, and inline JavaScript
    for fetch-based SSE streaming with AgentEvent handling.

    Args:
        send_url: POST endpoint URL for sending messages (required).
        messages: Initial messages to display.
        placeholder: Input field placeholder text.
        send_label: Submit button label.
        stop_label: Stop button label shown during streaming.
        agent_name: Display name for agent messages.
        user_name: Display name for user messages.
        height: CSS height for the container.
        show_metrics: Show metrics bar at the bottom.
        show_status: Show status bar at the top.
        tool_expanded: Default expand state for tool panels.
        agent_id: Unique ID prefix; auto-generated if omitted.
    """

    tag = "div"

    def __init__(
        self,
        *,
        send_url: str,
        messages: list[AgentMessage] | None = None,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        stop_label: str = "停止",
        agent_name: str = "Agent",
        user_name: str = "You",
        height: str = "700px",
        show_metrics: bool = True,
        show_status: bool = True,
        tool_expanded: bool = False,
        enable_attachments: bool = False,
        accept: str = "image/*,.pdf,.txt,.csv",
        max_file_size: int = 10 * 1024 * 1024,
        max_files: int = 5,
        agent_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self.send_url = send_url
        self.messages = messages or []
        self.placeholder = placeholder
        self.send_label = send_label
        self.stop_label = stop_label
        self.agent_name = agent_name
        self.user_name = user_name
        self.height = height
        self.show_metrics = show_metrics
        self.show_status = show_status
        self.tool_expanded = tool_expanded
        self.enable_attachments = enable_attachments
        self.accept = accept
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}"

        attrs["cls"] = f"flex flex-col {attrs.get('cls', '')}".strip()
        attrs["style"] = f"height:{self.height}"
        super().__init__(**attrs)

    def render(self) -> str:
        cid = escape(self.agent_id)

        # Render initial messages
        bubble_html = "".join(
            _render_agent_bubble(
                msg, self.user_name, self.agent_name, self.tool_expanded
            )
            for msg in self.messages
        )

        # Escape JS string values
        js_send_url = json.dumps(self.send_url, ensure_ascii=False)
        js_user_name = json.dumps(self.user_name, ensure_ascii=False)
        js_agent_name = json.dumps(self.agent_name, ensure_ascii=False)
        js_send_label = json.dumps(self.send_label, ensure_ascii=False)
        js_stop_label = json.dumps(self.stop_label, ensure_ascii=False)
        js_tool_expanded = "true" if self.tool_expanded else "false"
        js_enable_attach = "true" if self.enable_attachments else "false"
        js_accept = json.dumps(self.accept, ensure_ascii=False)
        js_max_file_size = str(self.max_file_size)
        js_max_files = str(self.max_files)

        # Status bar
        status_html = ""
        if self.show_status:
            status_html = (
                f'<div id="{cid}-status" class="px-4 py-2 border-b border-base-300'
                f' text-sm text-base-content/60 hidden"></div>'
            )

        # Metrics bar
        metrics_html = ""
        if self.show_metrics:
            metrics_html = (
                f'<div id="{cid}-metrics" class="px-4 py-2 border-t border-base-300'
                f' text-sm text-base-content/60 hidden"></div>'
            )

        placeholder_escaped = escape(self.placeholder)
        send_label_escaped = escape(self.send_label)

        script = f"""\
<script>
(function(){{
  var agentId = {json.dumps(self.agent_id)};
  var sendUrl = {js_send_url};
  var userName = {js_user_name};
  var agentName = {js_agent_name};
  var sendLabel = {js_send_label};
  var stopLabel = {js_stop_label};
  var toolExpanded = {js_tool_expanded};
  var enableAttach = {js_enable_attach};
  var acceptTypes = {js_accept};
  var maxFileSize = {js_max_file_size};
  var maxFiles = {js_max_files};
  var form = document.getElementById(agentId + '-form');
  var messagesEl = document.getElementById(agentId + '-messages');
  var input = document.getElementById(agentId + '-input');
  var btn = document.getElementById(agentId + '-btn');
  var statusEl = document.getElementById(agentId + '-status');
  var metricsEl = document.getElementById(agentId + '-metrics');
  var filesInput = document.getElementById(agentId + '-files');
  var attachBtn = document.getElementById(agentId + '-attach');
  var previewEl = document.getElementById(agentId + '-file-preview');

  var toolPanels = {{}};
  var fullText = '';
  var bubbleEl = null;
  var renderPending = false;
  var abortController = null;
  var pendingFiles = [];

  var _escapeEl = document.createElement('div');
  function escapeHtml(s) {{
    _escapeEl.textContent = s;
    return _escapeEl.innerHTML;
  }}

  {JS_PREVIEW_RENDERER}

  function formatSize(bytes) {{
    if (bytes < 1024) return bytes + 'B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB';
    return (bytes / 1048576).toFixed(1) + 'MB';
  }}

  function renderFilePreview() {{
    if (!previewEl) return;
    previewEl.innerHTML = '';
    if (pendingFiles.length === 0) {{ previewEl.classList.add('hidden'); return; }}
    previewEl.classList.remove('hidden');
    for (var i = 0; i < pendingFiles.length; i++) {{
      (function(idx) {{
        var f = pendingFiles[idx];
        var item = document.createElement('div');
        item.className = 'flex items-center gap-2 bg-base-200 rounded px-2 py-1 text-xs';
        var isImg = f.type && f.type.startsWith('image/');
        if (isImg) {{
          var img = document.createElement('img');
          img.className = 'w-8 h-8 object-cover rounded';
          img.src = URL.createObjectURL(f);
          item.appendChild(img);
        }} else {{
          var icon = document.createElement('span');
          icon.textContent = '\\ud83d\\udcc4';
          item.appendChild(icon);
        }}
        var nameSpan = document.createElement('span');
        nameSpan.className = 'truncate max-w-[120px]';
        nameSpan.textContent = f.name;
        item.appendChild(nameSpan);
        var sizeSpan = document.createElement('span');
        sizeSpan.className = 'text-base-content/50';
        sizeSpan.textContent = formatSize(f.size);
        item.appendChild(sizeSpan);
        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-ghost btn-xs';
        removeBtn.textContent = '\\u00d7';
        removeBtn.addEventListener('click', function() {{
          pendingFiles.splice(idx, 1);
          renderFilePreview();
        }});
        item.appendChild(removeBtn);
        previewEl.appendChild(item);
      }})(i);
    }}
  }}

  if (enableAttach && attachBtn && filesInput) {{
    attachBtn.addEventListener('click', function() {{ filesInput.click(); }});
    filesInput.addEventListener('change', function() {{
      var files = filesInput.files;
      for (var i = 0; i < files.length; i++) {{
        if (pendingFiles.length >= maxFiles) break;
        if (files[i].size > maxFileSize) continue;
        pendingFiles.push(files[i]);
      }}
      filesInput.value = '';
      renderFilePreview();
    }});
    form.addEventListener('dragover', function(e) {{ e.preventDefault(); form.classList.add('border-primary'); }});
    form.addEventListener('dragleave', function() {{ form.classList.remove('border-primary'); }});
    form.addEventListener('drop', function(e) {{
      e.preventDefault();
      form.classList.remove('border-primary');
      var files = e.dataTransfer.files;
      for (var i = 0; i < files.length; i++) {{
        if (pendingFiles.length >= maxFiles) break;
        if (files[i].size > maxFileSize) continue;
        pendingFiles.push(files[i]);
      }}
      renderFilePreview();
    }});
    input.addEventListener('paste', function(e) {{
      var items = e.clipboardData && e.clipboardData.items;
      if (!items) return;
      for (var i = 0; i < items.length; i++) {{
        if (items[i].kind === 'file') {{
          var f = items[i].getAsFile();
          if (f && pendingFiles.length < maxFiles && f.size <= maxFileSize) {{
            pendingFiles.push(f);
            renderFilePreview();
          }}
        }}
      }}
    }});
  }}

  function setStreaming(active) {{
    if (active) {{
      btn.textContent = stopLabel;
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-error');
      btn.classList.add('loading');
      btn.disabled = false;
      btn.type = 'button';
    }} else {{
      btn.textContent = sendLabel;
      btn.classList.remove('btn-error');
      btn.classList.add('btn-primary');
      btn.classList.remove('loading');
      btn.disabled = false;
      btn.type = 'submit';
      abortController = null;
    }}
  }}

  function setStatus(text) {{
    if (!statusEl) return;
    if (text) {{
      statusEl.textContent = text;
      statusEl.classList.remove('hidden');
    }} else {{
      statusEl.classList.add('hidden');
    }}
  }}

  function setMetrics(m) {{
    if (!metricsEl || !m) return;
    var parts = [];
    if (m.tokens != null) parts.push('Tokens: ' + m.tokens);
    if (m.duration_ms != null) parts.push('Duration: ' + (m.duration_ms / 1000).toFixed(1) + 's');
    if (m.tool_calls != null) parts.push('Tools: ' + m.tool_calls);
    if (parts.length > 0) {{
      metricsEl.textContent = parts.join('  ');
      metricsEl.classList.remove('hidden');
    }}
  }}

  function addBubble(role, name, content) {{
    var align = role === 'user' ? 'chat-end' : 'chat-start';
    var bubbleCls = role === 'user' ? 'chat-bubble chat-bubble-primary' : 'chat-bubble prose';
    var div = document.createElement('div');
    div.className = 'chat ' + align;
    div.innerHTML = '<div class="chat-header">' + escapeHtml(name) + '</div>'
                  + '<div class="' + bubbleCls + '">' + content + '</div>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div.querySelector('.chat-bubble');
  }}

  function addToolPanel(callId, toolName) {{
    if (!bubbleEl) return;
    var checked = toolExpanded ? ' checked' : '';
    var panel = document.createElement('div');
    panel.className = 'collapse collapse-arrow bg-base-200 my-2';
    panel.id = agentId + '-tool-' + callId;
    panel.innerHTML = '<input type="checkbox"' + checked + ' />'
      + '<div class="collapse-title font-medium text-sm">'
      + '<span class="loading loading-spinner loading-xs mr-2"></span>'
      + '🔧 Tool: ' + escapeHtml(toolName) + '()'
      + '</div>'
      + '<div class="collapse-content"><div class="text-xs">'
      + '<div class="font-semibold">Input:</div>'
      + '<pre class="tool-input bg-base-300 p-2 rounded mt-1 whitespace-pre-wrap"></pre>'
      + '</div></div>';
    bubbleEl.appendChild(panel);
    toolPanels[callId] = panel;
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return panel;
  }}

  function finalize() {{
    renderContent();
    if (typeof hljs !== 'undefined' && bubbleEl) {{
      bubbleEl.querySelectorAll('pre code').forEach(function(el) {{
        hljs.highlightElement(el);
      }});
    }}
    setStreaming(false);
    input.focus();
  }}

  function handleEvent(data) {{
    switch(data.type) {{
      case 'text':
        fullText += (data.content || '');
        scheduleRender();
        break;

      case 'tool_call':
        var panel = addToolPanel(data.call_id, data.tool_name);
        if (panel) {{
          var inputEl = panel.querySelector('.tool-input');
          if (inputEl) {{
            var inputStr = typeof data.tool_input === 'object'
              ? JSON.stringify(data.tool_input, null, 2)
              : String(data.tool_input || '');
            inputEl.textContent = inputStr;
          }}
        }}
        setStatus('🔧 Calling ' + (data.tool_name || 'tool') + '...');
        break;

      case 'tool_result':
        var tp = toolPanels[data.call_id];
        if (tp) {{
          var spinner = tp.querySelector('.loading');
          if (spinner) spinner.remove();
          var contentDiv = tp.querySelector('.collapse-content .text-xs');
          if (contentDiv) {{
            var resultDiv = document.createElement('div');
            resultDiv.innerHTML = '<div class="font-semibold mt-2">Result:</div>'
              + renderPreview(data.result || '', data.preview_hint || '');
            contentDiv.appendChild(resultDiv);
          }}
        }}
        setStatus('');
        break;

      case 'status':
        setStatus(data.content || '');
        break;

      case 'error':
        if (bubbleEl) {{
          var errDiv = document.createElement('div');
          errDiv.className = 'text-error mt-2';
          errDiv.textContent = data.content || 'An error occurred';
          bubbleEl.appendChild(errDiv);
        }}
        setStatus('');
        break;

      case 'done':
        setMetrics(data.metrics);
        setStatus('');
        finalize();
        break;
    }}
  }}

  function scheduleRender() {{
    if (renderPending) return;
    renderPending = true;
    requestAnimationFrame(function() {{
      renderPending = false;
      renderContent();
    }});
  }}

  function renderContent() {{
    if (!bubbleEl) return;
    var textEl = bubbleEl.querySelector('.agent-text');
    if (!textEl) {{
      textEl = document.createElement('div');
      textEl.className = 'agent-text';
      bubbleEl.appendChild(textEl);
    }}
    if (typeof marked !== 'undefined') {{
      textEl.innerHTML = marked.parse(fullText);
    }} else {{
      textEl.innerHTML = escapeHtml(fullText);
    }}
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }}

  btn.addEventListener('click', function() {{
    if (abortController) {{
      abortController.abort();
    }}
  }});

  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var message = input.value.trim();
    if (!message && pendingFiles.length === 0) return;
    input.value = '';

    var userHtml = escapeHtml(message);
    var sentFiles = pendingFiles.slice();
    if (sentFiles.length > 0) {{
      var ph = '<div class="flex flex-wrap gap-2 mt-1">';
      for (var fi = 0; fi < sentFiles.length; fi++) {{
        var sf = sentFiles[fi];
        if (sf.type && sf.type.startsWith('image/')) {{
          ph += '<img src="' + URL.createObjectURL(sf) + '" class="max-w-xs max-h-48 rounded" />';
        }} else {{
          ph += '<div class="badge badge-outline gap-1">\\ud83d\\udcc4 ' + escapeHtml(sf.name) + '</div>';
        }}
      }}
      ph += '</div>';
      userHtml += ph;
    }}
    addBubble('user', userName, userHtml);
    pendingFiles = [];
    renderFilePreview();

    bubbleEl = addBubble('assistant', agentName, '');
    fullText = '';
    toolPanels = {{}};
    abortController = new AbortController();
    setStreaming(true);

    var fetchBody, fetchHeaders;
    if (sentFiles.length > 0) {{
      var fd = new FormData();
      fd.append('message', message);
      for (var fj = 0; fj < sentFiles.length; fj++) fd.append('files', sentFiles[fj]);
      fetchBody = fd;
      fetchHeaders = {{}};
    }} else {{
      fetchBody = JSON.stringify({{message: message}});
      fetchHeaders = {{'Content-Type': 'application/json'}};
    }}

    fetch(sendUrl, {{
      method: 'POST',
      headers: fetchHeaders,
      body: fetchBody,
      signal: abortController.signal
    }}).then(function(response) {{
      if (!response.ok) throw new Error('HTTP ' + response.status);
      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      function read() {{
        return reader.read().then(function(result) {{
          if (result.done) {{
            finalize();
            return;
          }}
          buffer += decoder.decode(result.value, {{stream: true}});
          var lines = buffer.split('\\n');
          buffer = lines.pop();
          for (var i = 0; i < lines.length; i++) {{
            var line = lines[i].trim();
            if (line.startsWith('data: ')) {{
              try {{
                var data = JSON.parse(line.slice(6));
                handleEvent(data);
                if (data.type === 'done') return;
              }} catch(ex) {{}}
            }}
          }}
          return read();
        }});
      }}

      return read();
    }}).catch(function(err) {{
      if (err.name === 'AbortError') {{
        setStatus('');
        finalize();
        return;
      }}
      if (bubbleEl) {{
        var errSpan = document.createElement('span');
        errSpan.className = 'text-error';
        errSpan.textContent = err.message;
        bubbleEl.appendChild(errSpan);
      }}
      setStreaming(false);
    }});
  }});
}})();
</script>"""

        attrs_str = self._render_attrs()

        attach_html = (
            f'<input id="{cid}-files" type="file" multiple accept="{escape(self.accept)}" class="hidden" />'
            f'<button id="{cid}-attach" type="button" class="btn btn-ghost btn-sm"'
            f' title="Attach files">\U0001F4CE</button>'
            if self.enable_attachments else
            f'<input id="{cid}-files" type="file" class="hidden" />'
        )

        return (
            f"<div{attrs_str}>"
            f"{status_html}"
            f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4">'
            f"{bubble_html}"
            f"</div>"
            f"{metrics_html}"
            f'<div id="{cid}-file-preview" class="px-4 pt-2 flex flex-wrap gap-2 hidden"></div>'
            f'<form id="{cid}-form" class="p-4 border-t border-base-300 flex gap-2 items-end">'
            f"{attach_html}"
            f'<input id="{cid}-input" type="text" class="input input-bordered flex-1"'
            f' placeholder="{placeholder_escaped}" autocomplete="off" />'
            f'<button id="{cid}-btn" type="submit" class="btn btn-primary">'
            f"{send_label_escaped}</button>"
            f"</form>"
            f"{script}"
            f"</div>"
        )

    def _render_attrs(self) -> str:
        """Render the component's HTML attributes."""
        return _render_attrs(self.attrs)
