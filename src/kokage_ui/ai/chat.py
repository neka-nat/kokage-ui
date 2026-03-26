"""Streaming chat UI component using DaisyUI chat bubbles.

Provides ChatView for rendering a chat interface with SSE streaming support,
ChatMessage dataclass for message representation, and chat_stream helper
for converting async generators to SSE StreamingResponse.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from pydantic import BaseModel
from typing import Any

from markupsafe import escape
from starlette.responses import StreamingResponse

from kokage_ui.elements import Component, Div, Raw


class ChatMessage(BaseModel):
    """A single chat message.

    Args:
        role: Message role — "user", "assistant", or "system".
        content: Message text content.
        name: Optional display name override.
    """

    role: str
    content: str
    name: str | None = None


def chat_stream(generator: AsyncIterator[str]) -> StreamingResponse:
    """Convert an async token generator to an SSE StreamingResponse.

    Each token is sent as a Server-Sent Event with JSON payload.
    A final event with ``{"done": true}`` signals completion.

    Args:
        generator: Async iterator yielding string tokens.

    Returns:
        A StreamingResponse with ``text/event-stream`` content type.
    """

    async def event_stream():
        async for token in generator:
            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _render_bubble(msg: ChatMessage, user_name: str, assistant_name: str) -> str:
    """Render a single ChatMessage as a DaisyUI chat bubble."""
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
        name = escape(msg.name or assistant_name)
        return (
            f'<div class="chat chat-start">'
            f'<div class="chat-header">{name}</div>'
            f'<div class="chat-bubble prose">{escaped_content}</div>'
            f"</div>"
        )


class ChatView(Component):
    """Streaming chat UI component with DaisyUI chat bubbles.

    Renders a complete chat interface: message area with initial messages,
    input form, and inline JavaScript for fetch-based SSE streaming.

    Supports Markdown rendering via ``marked.js`` (load with
    ``Page(include_marked=True)``) and code highlighting via
    ``highlight.js`` (load with ``Page(include_highlightjs=True)``).

    Args:
        send_url: POST endpoint URL for sending messages (required).
        messages: Initial messages to display.
        placeholder: Input field placeholder text.
        send_label: Submit button label.
        stop_label: Stop button label shown during streaming.
        assistant_name: Display name for assistant messages.
        user_name: Display name for user messages.
        height: CSS height for the chat container.
        chat_id: Unique ID prefix; auto-generated if omitted.
    """

    tag = "div"

    def __init__(
        self,
        *,
        send_url: str,
        messages: list[ChatMessage] | None = None,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        stop_label: str = "停止",
        assistant_name: str = "Assistant",
        user_name: str = "You",
        height: str = "600px",
        enable_attachments: bool = False,
        accept: str = "image/*,.pdf,.txt,.csv",
        max_file_size: int = 10 * 1024 * 1024,
        max_files: int = 5,
        chat_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self.send_url = send_url
        self.messages = messages or []
        self.placeholder = placeholder
        self.send_label = send_label
        self.stop_label = stop_label
        self.assistant_name = assistant_name
        self.user_name = user_name
        self.height = height
        self.enable_attachments = enable_attachments
        self.accept = accept
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.chat_id = chat_id or f"chat-{uuid.uuid4().hex[:8]}"

        attrs["cls"] = f"flex flex-col {attrs.get('cls', '')}".strip()
        attrs["style"] = f"height:{self.height}"
        super().__init__(**attrs)

    def render(self) -> str:
        cid = escape(self.chat_id)
        send_url_escaped = escape(self.send_url)

        # Render initial messages
        bubble_html = ""
        for msg in self.messages:
            bubble_html += _render_bubble(msg, self.user_name, self.assistant_name)

        # Escape JS string values
        js_send_url = json.dumps(self.send_url, ensure_ascii=False)
        js_user_name = json.dumps(self.user_name, ensure_ascii=False)
        js_assistant_name = json.dumps(self.assistant_name, ensure_ascii=False)
        js_send_label = json.dumps(self.send_label, ensure_ascii=False)
        js_stop_label = json.dumps(self.stop_label, ensure_ascii=False)

        script = f"""\
<script>
(function(){{
  var chatId = {json.dumps(self.chat_id)};
  var sendUrl = {js_send_url};
  var userName = {js_user_name};
  var assistantName = {js_assistant_name};
  var sendLabel = {js_send_label};
  var stopLabel = {js_stop_label};
  var enableAttach = {json.dumps(self.enable_attachments)};
  var maxFileSize = {self.max_file_size};
  var maxFiles = {self.max_files};
  var form = document.getElementById(chatId + '-form');
  var messagesEl = document.getElementById(chatId + '-messages');
  var input = document.getElementById(chatId + '-input');
  var btn = document.getElementById(chatId + '-btn');
  var filesInput = document.getElementById(chatId + '-files');
  var attachBtn = document.getElementById(chatId + '-attach');
  var previewEl = document.getElementById(chatId + '-file-preview');
  var abortController = null;
  var pendingFiles = [];

  function escapeHtml(s) {{
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }}

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
        if (f.type && f.type.startsWith('image/')) {{
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

    var bubbleEl = addBubble('assistant', assistantName, '');
    abortController = new AbortController();
    setStreaming(true);

    var fullText = '';
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
            finish();
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
                if (data.done) {{
                  finish();
                  return;
                }}
                if (data.token != null) {{
                  fullText += data.token;
                  renderContent();
                }}
              }} catch(ex) {{}}
            }}
          }}
          return read();
        }});
      }}

      function renderContent() {{
        if (typeof marked !== 'undefined') {{
          bubbleEl.innerHTML = marked.parse(fullText);
        }} else {{
          bubbleEl.innerHTML = escapeHtml(fullText);
        }}
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }}

      function finish() {{
        renderContent();
        if (typeof hljs !== 'undefined') {{
          bubbleEl.querySelectorAll('pre code').forEach(function(el) {{
            hljs.highlightElement(el);
          }});
        }}
        setStreaming(false);
        input.focus();
      }}

      return read();
    }}).catch(function(err) {{
      if (err.name === 'AbortError') {{
        renderContent();
        setStreaming(false);
        input.focus();
        return;
      }}
      bubbleEl.innerHTML = '<span class="text-error">' + escapeHtml(err.message) + '</span>';
      setStreaming(false);
    }});
  }});
}})();
</script>"""

        attrs_str = self._render_attrs()
        placeholder_escaped = escape(self.placeholder)
        send_label_escaped = escape(self.send_label)

        attach_html = (
            f'<input id="{cid}-files" type="file" multiple accept="{escape(self.accept)}" class="hidden" />'
            f'<button id="{cid}-attach" type="button" class="btn btn-ghost btn-sm"'
            f' title="Attach files">\U0001F4CE</button>'
            if self.enable_attachments else
            f'<input id="{cid}-files" type="file" class="hidden" />'
        )

        return (
            f"<div{attrs_str}>"
            f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4">'
            f"{bubble_html}"
            f"</div>"
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
        from kokage_ui.elements import _render_attrs

        return _render_attrs(self.attrs)
