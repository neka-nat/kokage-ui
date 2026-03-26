"""Threaded agent dashboard with sidebar thread management.

Combines a thread list sidebar (DaisyUI Drawer) with AgentView-equivalent
agent chat, allowing users to maintain multiple persistent conversations.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from markupsafe import escape

from kokage_ui.ai.preview import JS_PREVIEW_RENDERER
from kokage_ui.elements import Component, _render_attrs


class ThreadedAgentView(Component):
    """Agent dashboard with thread sidebar.

    Renders a DaisyUI drawer layout: sidebar with thread list and
    new-thread button, main area with agent chat (status bar, messages,
    metrics, input form). All thread/message operations use fetch against
    the ConversationStore REST API.

    Args:
        send_url: POST endpoint URL for sending agent messages.
        threads_url: ConversationStore REST API prefix (e.g. "/api/threads").
        placeholder: Input field placeholder text.
        send_label: Submit button label.
        stop_label: Stop button label shown during streaming.
        agent_name: Display name for agent messages.
        user_name: Display name for user messages.
        height: CSS height for the container.
        show_metrics: Show metrics bar at the bottom.
        show_status: Show status bar at the top.
        tool_expanded: Default expand state for tool panels.
        new_thread_label: Label for the new thread button.
        agent_id: Unique ID prefix; auto-generated if omitted.
    """

    tag = "div"

    def __init__(
        self,
        *,
        send_url: str,
        threads_url: str,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        stop_label: str = "停止",
        agent_name: str = "Agent",
        user_name: str = "You",
        height: str = "100vh",
        show_metrics: bool = True,
        show_status: bool = True,
        tool_expanded: bool = False,
        new_thread_label: str = "+ New Thread",
        enable_attachments: bool = False,
        accept: str = "image/*,.pdf,.txt,.csv",
        max_file_size: int = 10 * 1024 * 1024,
        max_files: int = 5,
        agent_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self.send_url = send_url
        self.threads_url = threads_url
        self.placeholder = placeholder
        self.send_label = send_label
        self.stop_label = stop_label
        self.agent_name = agent_name
        self.user_name = user_name
        self.height = height
        self.show_metrics = show_metrics
        self.show_status = show_status
        self.tool_expanded = tool_expanded
        self.new_thread_label = new_thread_label
        self.enable_attachments = enable_attachments
        self.accept = accept
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.agent_id = agent_id or f"ta-{uuid.uuid4().hex[:8]}"
        super().__init__(**attrs)

    def render(self) -> str:
        cid = escape(self.agent_id)

        # JS-safe values
        js_send_url = json.dumps(self.send_url, ensure_ascii=False)
        js_threads_url = json.dumps(self.threads_url, ensure_ascii=False)
        js_user_name = json.dumps(self.user_name, ensure_ascii=False)
        js_agent_name = json.dumps(self.agent_name, ensure_ascii=False)
        js_send_label = json.dumps(self.send_label, ensure_ascii=False)
        js_stop_label = json.dumps(self.stop_label, ensure_ascii=False)
        js_tool_expanded = "true" if self.tool_expanded else "false"
        js_enable_attach = "true" if self.enable_attachments else "false"
        js_accept = json.dumps(self.accept, ensure_ascii=False)
        js_max_file_size = str(self.max_file_size)
        js_max_files = str(self.max_files)

        placeholder_escaped = escape(self.placeholder)
        send_label_escaped = escape(self.send_label)
        new_thread_escaped = escape(self.new_thread_label)

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

        script = f"""\
<script>
(function(){{
  var cid = {json.dumps(self.agent_id)};
  var sendUrl = {js_send_url};
  var threadsUrl = {js_threads_url};
  var userName = {js_user_name};
  var agentName = {js_agent_name};
  var sendLabel = {js_send_label};
  var stopLabel = {js_stop_label};
  var toolExpanded = {js_tool_expanded};
  var enableAttach = {js_enable_attach};
  var acceptTypes = {js_accept};
  var maxFileSize = {js_max_file_size};
  var maxFiles = {js_max_files};

  var form = document.getElementById(cid + '-form');
  var messagesEl = document.getElementById(cid + '-messages');
  var input = document.getElementById(cid + '-input');
  var btn = document.getElementById(cid + '-btn');
  var statusEl = document.getElementById(cid + '-status');
  var metricsEl = document.getElementById(cid + '-metrics');
  var threadListEl = document.getElementById(cid + '-thread-list');
  var filesInput = document.getElementById(cid + '-files');
  var attachBtn = document.getElementById(cid + '-attach');
  var previewEl = document.getElementById(cid + '-file-preview');
  var pendingFiles = [];

  var currentThreadId = null;
  var threadMessageCount = 0;
  var toolPanels = {{}};
  var fullText = '';
  var currentToolCalls = [];
  var bubbleEl = null;
  var renderPending = false;
  var abortController = null;

  var _escapeEl = document.createElement('div');
  function escapeHtml(s) {{
    _escapeEl.textContent = s;
    return _escapeEl.innerHTML;
  }}

  {JS_PREVIEW_RENDERER}

  /* --- File attachment helpers --- */

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

  function formatSize(bytes) {{
    if (bytes < 1024) return bytes + 'B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB';
    return (bytes / 1048576).toFixed(1) + 'MB';
  }}

  function renderAttachmentBubble(attachments) {{
    var html = '';
    if (!attachments || !attachments.length) return html;
    for (var i = 0; i < attachments.length; i++) {{
      var a = attachments[i];
      var isImg = a.content_type && a.content_type.startsWith('image/');
      if (isImg) {{
        html += '<img src="' + escapeHtml(a.url) + '" class="max-w-xs max-h-48 rounded mt-1" loading="lazy" />';
      }} else {{
        html += '<a href="' + escapeHtml(a.url) + '" target="_blank" class="link link-primary text-sm">\\ud83d\\udcc4 ' + escapeHtml(a.name) + '</a> ';
      }}
    }}
    return '<div class="flex flex-wrap gap-2 mt-1">' + html + '</div>';
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
    /* Drag and drop on input area */
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
    /* Paste image from clipboard */
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

  /* --- Streaming UI helpers (same as AgentView) --- */

  function setStreaming(active) {{
    if (active) {{
      btn.textContent = stopLabel;
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-error', 'loading');
      btn.disabled = false;
      btn.type = 'button';
    }} else {{
      btn.textContent = sendLabel;
      btn.classList.remove('btn-error', 'loading');
      btn.classList.add('btn-primary');
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
    panel.id = cid + '-tool-' + callId;
    panel.innerHTML = '<input type="checkbox"' + checked + ' />'
      + '<div class="collapse-title font-medium text-sm">'
      + '<span class="loading loading-spinner loading-xs mr-2"></span>'
      + '\\ud83d\\udd27 Tool: ' + escapeHtml(toolName) + '()'
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

  function renderStoredToolCall(tc) {{
    if (!bubbleEl) return;
    var checked = toolExpanded ? ' checked' : '';
    var panel = document.createElement('div');
    panel.className = 'collapse collapse-arrow bg-base-200 my-2';
    var inputStr = typeof tc.input === 'object' ? JSON.stringify(tc.input, null, 2) : String(tc.input || '');
    panel.innerHTML = '<input type="checkbox"' + checked + ' />'
      + '<div class="collapse-title font-medium text-sm">'
      + '\\ud83d\\udd27 Tool: ' + escapeHtml(tc.name) + '()'
      + '</div>'
      + '<div class="collapse-content"><div class="text-xs">'
      + '<div class="font-semibold">Input:</div>'
      + '<pre class="bg-base-300 p-2 rounded mt-1 whitespace-pre-wrap">' + escapeHtml(inputStr) + '</pre>'
      + (tc.result ? '<div class="font-semibold mt-2">Result:</div>' + renderPreview(tc.result, tc.preview_hint || '') : '')
      + '</div></div>';
    bubbleEl.appendChild(panel);
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
        currentToolCalls.push({{
          name: data.tool_name || '',
          input: data.tool_input || '',
          call_id: data.call_id || '',
          result: '',
          preview_hint: ''
        }});
        setStatus('\\ud83d\\udd27 Calling ' + (data.tool_name || 'tool') + '...');
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
        for (var i = 0; i < currentToolCalls.length; i++) {{
          if (currentToolCalls[i].call_id === data.call_id) {{
            currentToolCalls[i].result = data.result || '';
            currentToolCalls[i].preview_hint = data.preview_hint || '';
            break;
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
      case 'attachments':
        try {{ sentAttachmentUrls = JSON.parse(data.content || '[]'); }} catch(ex) {{ sentAttachmentUrls = []; }}
        break;
      case 'done':
        setMetrics(data.metrics);
        setStatus('');
        finalize();
        break;
    }}
  }}

  /* --- Thread management --- */

  function loadThreadList() {{
    fetch(threadsUrl).then(function(r) {{ return r.json(); }}).then(function(threads) {{
      threadListEl.innerHTML = '';
      threads.forEach(function(t) {{
        var li = document.createElement('li');
        var active = t.id === currentThreadId ? ' active' : '';
        li.innerHTML = '<a class="flex justify-between items-center' + active + '" data-thread-id="' + escapeHtml(t.id) + '">'
          + '<span class="truncate flex-1">' + escapeHtml(t.title || 'New Thread') + '</span>'
          + '<button class="btn btn-ghost btn-xs delete-thread" data-thread-id="' + escapeHtml(t.id) + '">\\u00d7</button>'
          + '</a>';
        li.querySelector('a').addEventListener('click', function(e) {{
          if (e.target.classList.contains('delete-thread')) return;
          switchThread(t.id);
        }});
        li.querySelector('.delete-thread').addEventListener('click', function(e) {{
          e.preventDefault();
          e.stopPropagation();
          deleteThread(t.id);
        }});
        threadListEl.appendChild(li);
      }});
    }});
  }}

  function switchThread(threadId) {{
    if (threadId === currentThreadId) return;
    if (abortController) {{
      abortController.abort();
      abortController = null;
      setStreaming(false);
    }}
    currentThreadId = threadId;
    loadThreadMessages(threadId);
    loadThreadList();
  }}

  function loadThreadMessages(threadId) {{
    messagesEl.innerHTML = '';
    if (metricsEl) metricsEl.classList.add('hidden');
    if (statusEl) statusEl.classList.add('hidden');
    fetch(threadsUrl + '/' + threadId + '/messages').then(function(r) {{ return r.json(); }}).then(function(messages) {{
      threadMessageCount = messages.length;
      messages.forEach(function(msg) {{
        if (msg.role === 'user') {{
          var uc = escapeHtml(msg.content || '') + renderAttachmentBubble(msg.attachments);
          addBubble('user', userName, uc);
        }} else {{
          bubbleEl = addBubble('assistant', agentName, '');
          if (msg.tool_calls && msg.tool_calls.length) {{
            msg.tool_calls.forEach(function(tc) {{
              renderStoredToolCall(tc);
            }});
          }}
          if (msg.content) {{
            var textEl = document.createElement('div');
            textEl.className = 'agent-text';
            if (typeof marked !== 'undefined') {{
              textEl.innerHTML = marked.parse(msg.content);
            }} else {{
              textEl.innerHTML = escapeHtml(msg.content);
            }}
            bubbleEl.appendChild(textEl);
          }}
          if (typeof hljs !== 'undefined' && bubbleEl) {{
            bubbleEl.querySelectorAll('pre code').forEach(function(el) {{
              hljs.highlightElement(el);
            }});
          }}
        }}
      }});
      bubbleEl = null;
    }});
  }}

  function createThread() {{
    fetch(threadsUrl, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{title: ''}})
    }}).then(function(r) {{ return r.json(); }}).then(function(thread) {{
      currentThreadId = thread.id;
      threadMessageCount = 0;
      messagesEl.innerHTML = '';
      if (metricsEl) metricsEl.classList.add('hidden');
      if (statusEl) statusEl.classList.add('hidden');
      loadThreadList();
      input.focus();
    }});
  }}

  function deleteThread(threadId) {{
    fetch(threadsUrl + '/' + threadId, {{method: 'DELETE'}}).then(function() {{
      if (threadId === currentThreadId) {{
        currentThreadId = null;
        messagesEl.innerHTML = '';
        if (metricsEl) metricsEl.classList.add('hidden');
      }}
      loadThreadList();
      if (!currentThreadId) {{
        fetch(threadsUrl).then(function(r) {{ return r.json(); }}).then(function(threads) {{
          if (threads.length > 0) {{
            switchThread(threads[0].id);
          }} else {{
            createThread();
          }}
        }});
      }}
    }});
  }}

  function saveMessages(userMessage, assistantContent, toolCalls, attachments) {{
    if (!currentThreadId) return;
    var tcPayload = toolCalls.length > 0 ? toolCalls : null;
    var attPayload = attachments && attachments.length > 0 ? attachments : null;
    fetch(threadsUrl + '/' + currentThreadId + '/messages', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{role: 'user', content: userMessage, attachments: attPayload}})
    }}).then(function() {{
      return fetch(threadsUrl + '/' + currentThreadId + '/messages', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{role: 'assistant', content: assistantContent, tool_calls: tcPayload}})
      }});
    }}).then(function() {{
      threadMessageCount += 2;
      if (threadMessageCount <= 2) {{
        var title = userMessage.substring(0, 30);
        if (userMessage.length > 30) title += '...';
        fetch(threadsUrl + '/' + currentThreadId, {{
          method: 'PUT',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{title: title}})
        }}).then(function() {{ loadThreadList(); }});
      }}
    }});
  }}

  /* --- Form submit --- */

  btn.addEventListener('click', function() {{
    if (abortController) {{
      abortController.abort();
    }}
  }});

  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var message = input.value.trim();
    if ((!message && pendingFiles.length === 0) || !currentThreadId) return;
    input.value = '';

    var userHtml = escapeHtml(message);
    var sentFiles = pendingFiles.slice();
    var sentAttachmentUrls = [];
    if (sentFiles.length > 0) {{
      var previewHtml = '<div class="flex flex-wrap gap-2 mt-1">';
      for (var fi = 0; fi < sentFiles.length; fi++) {{
        var sf = sentFiles[fi];
        if (sf.type && sf.type.startsWith('image/')) {{
          previewHtml += '<img src="' + URL.createObjectURL(sf) + '" class="max-w-xs max-h-48 rounded" />';
        }} else {{
          previewHtml += '<div class="badge badge-outline gap-1">\\ud83d\\udcc4 ' + escapeHtml(sf.name) + '</div>';
        }}
      }}
      previewHtml += '</div>';
      userHtml += previewHtml;
    }}
    addBubble('user', userName, userHtml);
    pendingFiles = [];
    renderFilePreview();

    bubbleEl = addBubble('assistant', agentName, '');
    fullText = '';
    toolPanels = {{}};
    currentToolCalls = [];
    abortController = new AbortController();
    setStreaming(true);

    var fetchBody, fetchHeaders;
    if (sentFiles.length > 0) {{
      var fd = new FormData();
      fd.append('message', message);
      fd.append('thread_id', currentThreadId);
      for (var fj = 0; fj < sentFiles.length; fj++) fd.append('files', sentFiles[fj]);
      fetchBody = fd;
      fetchHeaders = {{}};
    }} else {{
      fetchBody = JSON.stringify({{message: message, thread_id: currentThreadId}});
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
            saveMessages(message, fullText, currentToolCalls, sentAttachmentUrls);
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
                if (data.type === 'done') {{
                  saveMessages(message, fullText, currentToolCalls, sentAttachmentUrls);
                  return;
                }}
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
        saveMessages(message, fullText, currentToolCalls, sentAttachmentUrls);
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

  /* --- New Thread button --- */
  var newThreadBtn = document.getElementById(cid + '-new-thread');
  if (newThreadBtn) {{
    newThreadBtn.addEventListener('click', function() {{
      var drawerToggle = document.getElementById(cid + '-drawer');
      if (drawerToggle) drawerToggle.checked = false;
      createThread();
    }});
  }}

  /* --- Init: load threads or create first one --- */
  fetch(threadsUrl).then(function(r) {{ return r.json(); }}).then(function(threads) {{
    if (threads.length > 0) {{
      currentThreadId = threads[0].id;
      loadThreadList();
      loadThreadMessages(threads[0].id);
    }} else {{
      createThread();
    }}
  }});
}})();
</script>"""

        # Build drawer layout
        return (
            f'<div class="drawer lg:drawer-open" style="height:{escape(self.height)}">'
            # Toggle checkbox for mobile
            f'<input id="{cid}-drawer" type="checkbox" class="drawer-toggle" />'
            # Main content
            f'<div class="drawer-content flex flex-col">'
            # Mobile hamburger + status
            f'<div class="flex items-center border-b border-base-300 lg:hidden">'
            f'<label for="{cid}-drawer" class="btn btn-ghost btn-sm drawer-button">'
            f'\u2630</label>'
            f'</div>'
            f'{status_html}'
            f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4"></div>'
            f'{metrics_html}'
            f'<div id="{cid}-file-preview" class="px-4 pt-2 flex flex-wrap gap-2 hidden"></div>'
            f'<form id="{cid}-form" class="p-4 border-t border-base-300 flex gap-2 items-end">'
            + (
                f'<input id="{cid}-files" type="file" multiple accept="{escape(self.accept)}" class="hidden" />'
                f'<button id="{cid}-attach" type="button" class="btn btn-ghost btn-sm"'
                f' title="Attach files">\U0001F4CE</button>'
                if self.enable_attachments else
                f'<input id="{cid}-files" type="file" class="hidden" />'
            )
            + f'<input id="{cid}-input" type="text" class="input input-bordered flex-1"'
            f' placeholder="{placeholder_escaped}" autocomplete="off" />'
            f'<button id="{cid}-btn" type="submit" class="btn btn-primary">'
            f'{send_label_escaped}</button>'
            f'</form>'
            f'</div>'
            # Sidebar
            f'<div class="drawer-side">'
            f'<label for="{cid}-drawer" class="drawer-overlay"></label>'
            f'<div class="bg-base-200 w-64 min-h-full flex flex-col">'
            f'<div class="p-3">'
            f'<button id="{cid}-new-thread" class="btn btn-primary btn-sm w-full">'
            f'{new_thread_escaped}</button>'
            f'</div>'
            f'<ul id="{cid}-thread-list" class="menu flex-1 overflow-y-auto"></ul>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'{script}'
        )

    def _render_attrs(self) -> str:
        return _render_attrs(self.attrs)
