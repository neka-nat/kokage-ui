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
        assistant_name: str = "Assistant",
        user_name: str = "You",
        height: str = "600px",
        chat_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self.send_url = send_url
        self.messages = messages or []
        self.placeholder = placeholder
        self.send_label = send_label
        self.assistant_name = assistant_name
        self.user_name = user_name
        self.height = height
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

        script = f"""\
<script>
(function(){{
  var chatId = {json.dumps(str(self.chat_id))};
  var sendUrl = {js_send_url};
  var userName = {js_user_name};
  var assistantName = {js_assistant_name};
  var form = document.getElementById(chatId + '-form');
  var messagesEl = document.getElementById(chatId + '-messages');
  var input = document.getElementById(chatId + '-input');
  var btn = document.getElementById(chatId + '-btn');

  function escapeHtml(s) {{
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
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

  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var message = input.value.trim();
    if (!message) return;
    input.value = '';

    addBubble('user', userName, escapeHtml(message));

    var bubbleEl = addBubble('assistant', assistantName, '');
    btn.classList.add('loading');
    btn.disabled = true;

    var fullText = '';
    fetch(sendUrl, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{message: message}})
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
        btn.classList.remove('loading');
        btn.disabled = false;
        input.focus();
      }}

      return read();
    }}).catch(function(err) {{
      bubbleEl.innerHTML = '<span class="text-error">' + escapeHtml(err.message) + '</span>';
      btn.classList.remove('loading');
      btn.disabled = false;
    }});
  }});
}})();
</script>"""

        attrs_str = self._render_attrs()
        placeholder_escaped = escape(self.placeholder)
        send_label_escaped = escape(self.send_label)

        return (
            f"<div{attrs_str}>"
            f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4">'
            f"{bubble_html}"
            f"</div>"
            f'<form id="{cid}-form" class="p-4 border-t border-base-300 flex gap-2">'
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
