"""Deep Agent dashboard with task plan sidebar.

Combines AgentView-equivalent agent chat with a right-side drawer
showing real-time task plan progress and file activity tracking.
Designed for use with ``deep_agent_stream()`` which emits ``plan``
events from the Deep Agents ``write_todos`` tool.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from markupsafe import escape

from kokage_ui.ai.agent import AgentMessage, ToolCall, _render_agent_bubble
from kokage_ui.ai.preview import JS_PREVIEW_RENDERER
from kokage_ui.elements import Component, _render_attrs

# Deep Agents filesystem tools tracked in file activity.
_FILESYSTEM_TOOLS = {"read_file", "write_file", "edit_file", "ls", "glob", "grep"}


class DeepAgentView(Component):
    """Agent dashboard with task plan sidebar.

    Renders a DaisyUI drawer-end layout: main area with agent chat
    (status bar, messages, metrics, input form) and a right-side
    sidebar showing task plan progress and file activity.

    The plan sidebar updates in real-time from ``plan`` SSE events
    emitted by ``deep_agent_stream()`` when the agent calls
    ``write_todos``. File activity tracks filesystem tool calls.

    Args:
        send_url: POST endpoint URL for sending agent messages.
        interrupt_url: POST endpoint for resuming after interrupt.
        messages: Initial messages to display.
        placeholder: Input field placeholder text.
        send_label: Submit button label.
        stop_label: Stop button label shown during streaming.
        approve_label: Approve button label in interrupt modal.
        reject_label: Reject button label in interrupt modal.
        agent_name: Display name for agent messages.
        user_name: Display name for user messages.
        height: CSS height for the container.
        show_metrics: Show metrics bar at the bottom.
        show_status: Show status bar at the top.
        show_plan: Show task plan in the sidebar.
        show_files: Show file activity in the sidebar.
        tool_expanded: Default expand state for tool panels.
        plan_label: Heading for the plan section.
        files_label: Heading for the file activity section.
        agent_id: Unique ID prefix; auto-generated if omitted.
    """

    tag = "div"

    def __init__(
        self,
        *,
        send_url: str,
        interrupt_url: str | None = None,
        messages: list[AgentMessage] | None = None,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        stop_label: str = "停止",
        approve_label: str = "承認",
        reject_label: str = "拒否",
        agent_name: str = "Agent",
        user_name: str = "You",
        height: str = "100vh",
        show_metrics: bool = True,
        show_status: bool = True,
        show_plan: bool = True,
        show_files: bool = True,
        tool_expanded: bool = False,
        plan_label: str = "Task Plan",
        files_label: str = "File Activity",
        enable_attachments: bool = False,
        accept: str = "image/*,.pdf,.txt,.csv",
        max_file_size: int = 10 * 1024 * 1024,
        max_files: int = 5,
        agent_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self.send_url = send_url
        self.interrupt_url = interrupt_url
        self.messages = messages or []
        self.placeholder = placeholder
        self.send_label = send_label
        self.stop_label = stop_label
        self.approve_label = approve_label
        self.reject_label = reject_label
        self.agent_name = agent_name
        self.user_name = user_name
        self.height = height
        self.show_metrics = show_metrics
        self.show_status = show_status
        self.show_plan = show_plan
        self.show_files = show_files
        self.tool_expanded = tool_expanded
        self.plan_label = plan_label
        self.files_label = files_label
        self.enable_attachments = enable_attachments
        self.accept = accept
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.agent_id = agent_id or f"da-{uuid.uuid4().hex[:8]}"
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

        # JS-safe values
        js_send_url = json.dumps(self.send_url, ensure_ascii=False)
        js_interrupt_url = json.dumps(self.interrupt_url, ensure_ascii=False) if self.interrupt_url else "null"
        js_user_name = json.dumps(self.user_name, ensure_ascii=False)
        js_agent_name = json.dumps(self.agent_name, ensure_ascii=False)
        js_send_label = json.dumps(self.send_label, ensure_ascii=False)
        js_stop_label = json.dumps(self.stop_label, ensure_ascii=False)
        js_approve_label = json.dumps(self.approve_label, ensure_ascii=False)
        js_reject_label = json.dumps(self.reject_label, ensure_ascii=False)
        js_tool_expanded = "true" if self.tool_expanded else "false"
        js_enable_attach = "true" if self.enable_attachments else "false"
        js_accept = json.dumps(self.accept, ensure_ascii=False)
        js_max_file_size = str(self.max_file_size)
        js_max_files = str(self.max_files)
        js_show_plan = "true" if self.show_plan else "false"
        js_show_files = "true" if self.show_files else "false"
        js_filesystem_tools = json.dumps(sorted(_FILESYSTEM_TOOLS))

        placeholder_escaped = escape(self.placeholder)
        send_label_escaped = escape(self.send_label)
        plan_label_escaped = escape(self.plan_label)
        files_label_escaped = escape(self.files_label)

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
  var interruptUrl = {js_interrupt_url};
  var userName = {js_user_name};
  var agentName = {js_agent_name};
  var sendLabel = {js_send_label};
  var stopLabel = {js_stop_label};
  var approveLabel = {js_approve_label};
  var rejectLabel = {js_reject_label};
  var toolExpanded = {js_tool_expanded};
  var enableAttach = {js_enable_attach};
  var acceptTypes = {js_accept};
  var maxFileSize = {js_max_file_size};
  var maxFiles = {js_max_files};
  var showPlan = {js_show_plan};
  var showFiles = {js_show_files};
  var filesystemTools = new Set({js_filesystem_tools});

  var form = document.getElementById(cid + '-form');
  var messagesEl = document.getElementById(cid + '-messages');
  var input = document.getElementById(cid + '-input');
  var btn = document.getElementById(cid + '-btn');
  var statusEl = document.getElementById(cid + '-status');
  var metricsEl = document.getElementById(cid + '-metrics');
  var filesInput = document.getElementById(cid + '-files');
  var attachBtn = document.getElementById(cid + '-attach');
  var previewEl = document.getElementById(cid + '-file-preview');
  var planListEl = document.getElementById(cid + '-plan-list');
  var fileListEl = document.getElementById(cid + '-file-list');

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

  /* --- Plan sidebar --- */

  function renderPlan(content) {{
    if (!planListEl || !showPlan) return;
    var todos;
    try {{
      todos = JSON.parse(content);
    }} catch(e) {{
      return;
    }}
    if (!Array.isArray(todos)) {{
      if (todos && Array.isArray(todos.todos)) todos = todos.todos;
      else return;
    }}
    planListEl.innerHTML = '';
    for (var i = 0; i < todos.length; i++) {{
      var todo = todos[i];
      var status = (todo.status || 'pending').toLowerCase();
      var icon = '\\u2b1c';
      if (status === 'in_progress' || status === 'in-progress' || status === 'running') icon = '\\ud83d\\udd04';
      else if (status === 'completed' || status === 'done') icon = '\\u2705';
      var li = document.createElement('li');
      li.className = 'flex items-start gap-2 py-1';
      li.innerHTML = '<span class="flex-shrink-0">' + icon + '</span>'
        + '<span class="text-sm">' + escapeHtml(todo.task || todo.title || todo.description || '') + '</span>';
      planListEl.appendChild(li);
    }}
  }}

  function addFileActivity(toolName, toolInput) {{
    if (!fileListEl || !showFiles) return;
    if (!filesystemTools.has(toolName)) return;
    var path = '';
    if (typeof toolInput === 'object' && toolInput !== null) {{
      path = toolInput.path || toolInput.file_path || toolInput.pattern || '';
    }} else if (typeof toolInput === 'string') {{
      path = toolInput;
    }}
    var li = document.createElement('li');
    li.className = 'flex items-center gap-2 py-1 text-xs';
    var actionIcon = '\\ud83d\\udcc4';
    if (toolName === 'write_file') actionIcon = '\\u270f\\ufe0f';
    else if (toolName === 'edit_file') actionIcon = '\\u270f\\ufe0f';
    else if (toolName === 'read_file') actionIcon = '\\ud83d\\udc41';
    else if (toolName === 'ls' || toolName === 'glob') actionIcon = '\\ud83d\\udcc2';
    else if (toolName === 'grep') actionIcon = '\\ud83d\\udd0d';
    li.innerHTML = '<span>' + actionIcon + '</span>'
      + '<span class="truncate" title="' + escapeHtml(path) + '">' + escapeHtml(path || toolName) + '</span>';
    fileListEl.appendChild(li);
    fileListEl.scrollTop = fileListEl.scrollHeight;
  }}

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

  /* --- Streaming UI helpers --- */

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

  /* --- Interrupt modal (HITL) --- */

  function showInterruptModal(data) {{
    var modalId = cid + '-interrupt-modal';
    var existing = document.getElementById(modalId);
    if (existing) existing.remove();

    var actions = (data.metrics && data.metrics.action_requests) || [];

    var toolName = data.tool_name || 'tool';
    var toolInput = typeof data.tool_input === 'object'
      ? JSON.stringify(data.tool_input, null, 2)
      : String(data.tool_input || '');

    var actionsHtml = '';
    for (var i = 0; i < actions.length; i++) {{
      var a = actions[i];
      var aInput = typeof a.args === 'object' ? JSON.stringify(a.args, null, 2) : String(a.args || '');
      actionsHtml += '<div class="mb-3">'
        + '<div class="font-semibold text-sm">\\ud83d\\udd27 ' + escapeHtml(a.name || 'tool') + '()</div>'
        + '<pre class="bg-base-300 p-2 rounded mt-1 text-xs whitespace-pre-wrap">' + escapeHtml(aInput) + '</pre>'
        + '</div>';
    }}
    if (!actionsHtml) {{
      actionsHtml = '<div class="mb-3">'
        + '<div class="font-semibold text-sm">\\ud83d\\udd27 ' + escapeHtml(toolName) + '()</div>'
        + '<pre class="bg-base-300 p-2 rounded mt-1 text-xs whitespace-pre-wrap">' + escapeHtml(toolInput) + '</pre>'
        + '</div>';
    }}

    var modal = document.createElement('dialog');
    modal.id = modalId;
    modal.className = 'modal modal-open';
    modal.innerHTML = '<div class="modal-box">'
      + '<h3 class="font-bold text-lg mb-4">\\u26a0\\ufe0f ' + escapeHtml(data.content || 'Approval required') + '</h3>'
      + '<div class="max-h-60 overflow-y-auto">' + actionsHtml + '</div>'
      + '<div class="modal-action">'
      + '<button class="btn btn-error" data-decision="reject">' + escapeHtml(rejectLabel) + '</button>'
      + '<button class="btn btn-success" data-decision="approve">' + escapeHtml(approveLabel) + '</button>'
      + '</div></div>';

    document.body.appendChild(modal);

    modal.querySelectorAll('[data-decision]').forEach(function(b) {{
      b.addEventListener('click', function() {{
        var decision = b.getAttribute('data-decision');
        modal.remove();
        var decisions = [];
        var count = actions.length || 1;
        for (var j = 0; j < count; j++) {{
          decisions.push({{type: decision}});
        }}
        resumeAgent(decisions);
      }});
    }});
  }}

  function resumeAgent(decisions) {{
    if (!interruptUrl) return;
    setStreaming(true);
    setStatus(decisions[0] && decisions[0].type === 'approve' ? 'Resuming...' : 'Rejecting...');

    abortController = new AbortController();
    fetch(interruptUrl, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{decisions: decisions}}),
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
                var evData = JSON.parse(line.slice(6));
                handleEvent(evData);
                if (evData.type === 'done') return;
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
  }}

  /* --- Event handler --- */

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
        addFileActivity(data.tool_name, data.tool_input);
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
        setStatus('');
        break;

      case 'plan':
        renderPlan(data.content || '');
        break;

      case 'status':
        setStatus(data.content || '');
        break;

      case 'interrupt':
        if (interruptUrl && bubbleEl) {{
          setStatus('');
          showInterruptModal(data);
        }}
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

  /* --- Stop button --- */

  btn.addEventListener('click', function() {{
    if (abortController) {{
      abortController.abort();
    }}
  }});

  /* --- Form submit --- */

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

        # Build sidebar content
        plan_section = ""
        if self.show_plan:
            plan_section = (
                f'<div class="p-3">'
                f'<h3 class="font-bold text-sm mb-2">{plan_label_escaped}</h3>'
                f'<ul id="{cid}-plan-list" class="space-y-1">'
                f'<li class="text-xs text-base-content/50">Waiting for plan...</li>'
                f'</ul>'
                f'</div>'
            )

        files_section = ""
        if self.show_files:
            files_section = (
                f'<div class="collapse collapse-arrow border-t border-base-300">'
                f'<input type="checkbox" checked />'
                f'<div class="collapse-title font-bold text-sm">{files_label_escaped}</div>'
                f'<div class="collapse-content">'
                f'<ul id="{cid}-file-list" class="space-y-0 max-h-48 overflow-y-auto"></ul>'
                f'</div>'
                f'</div>'
            )

        attach_html = (
            f'<input id="{cid}-files" type="file" multiple accept="{escape(self.accept)}" class="hidden" />'
            f'<button id="{cid}-attach" type="button" class="btn btn-ghost btn-sm"'
            f' title="Attach files">\U0001F4CE</button>'
            if self.enable_attachments else
            f'<input id="{cid}-files" type="file" class="hidden" />'
        )

        show_sidebar = self.show_plan or self.show_files

        if show_sidebar:
            return (
                f'<div class="drawer drawer-end lg:drawer-open" style="height:{escape(self.height)}">'
                # Toggle checkbox for mobile
                f'<input id="{cid}-drawer" type="checkbox" class="drawer-toggle" />'
                # Main content
                f'<div class="drawer-content flex flex-col">'
                # Mobile toggle + status
                f'<div class="flex items-center border-b border-base-300 lg:hidden">'
                f'<div class="flex-1"></div>'
                f'<label for="{cid}-drawer" class="btn btn-ghost btn-sm drawer-button">'
                f'\u2630</label>'
                f'</div>'
                f'{status_html}'
                f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4">'
                f'{bubble_html}'
                f'</div>'
                f'{metrics_html}'
                f'<div id="{cid}-file-preview" class="px-4 pt-2 flex flex-wrap gap-2 hidden"></div>'
                f'<form id="{cid}-form" class="p-4 border-t border-base-300 flex gap-2 items-end">'
                f'{attach_html}'
                f'<input id="{cid}-input" type="text" class="input input-bordered flex-1"'
                f' placeholder="{placeholder_escaped}" autocomplete="off" />'
                f'<button id="{cid}-btn" type="submit" class="btn btn-primary">'
                f'{send_label_escaped}</button>'
                f'</form>'
                f'</div>'
                # Sidebar
                f'<div class="drawer-side">'
                f'<label for="{cid}-drawer" class="drawer-overlay"></label>'
                f'<div class="bg-base-200 w-72 min-h-full flex flex-col">'
                f'{plan_section}'
                f'{files_section}'
                f'</div>'
                f'</div>'
                f'</div>'
                f'{script}'
            )
        else:
            # No sidebar — render like a plain AgentView
            attrs_str = self._render_attrs()
            return (
                f'<div class="flex flex-col" style="height:{escape(self.height)}"{attrs_str}>'
                f'{status_html}'
                f'<div id="{cid}-messages" class="flex-1 overflow-y-auto p-4 space-y-4">'
                f'{bubble_html}'
                f'</div>'
                f'{metrics_html}'
                f'<div id="{cid}-file-preview" class="px-4 pt-2 flex flex-wrap gap-2 hidden"></div>'
                f'<form id="{cid}-form" class="p-4 border-t border-base-300 flex gap-2 items-end">'
                f'{attach_html}'
                f'<input id="{cid}-input" type="text" class="input input-bordered flex-1"'
                f' placeholder="{placeholder_escaped}" autocomplete="off" />'
                f'<button id="{cid}-btn" type="submit" class="btn btn-primary">'
                f'{send_label_escaped}</button>'
                f'</form>'
                f'{script}'
                f'</div>'
            )

    def _render_attrs(self) -> str:
        return _render_attrs(self.attrs)
