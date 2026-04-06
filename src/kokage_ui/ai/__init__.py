"""AI integration components for kokage-ui.

Provides ChatView for streaming LLM chat interfaces
and AgentView for AI agent dashboards with tool call visualization.
"""

from kokage_ui.ai.agent import AgentEvent, AgentMessage, AgentView, ToolCall, agent_stream
from kokage_ui.ai.chat import ChatMessage, ChatView, chat_stream
from kokage_ui.ai.conversation import Attachment, ConversationStore, InMemoryConversationStore, Message, Thread
from kokage_ui.ai.preview import FilePreview
from kokage_ui.ai.threaded import ThreadedAgentView
from kokage_ui.ai.tools import ToolInfo, ToolRegistry

# LangChain-dependent exports are lazy-loaded below.
_LANGCHAIN_EXPORTS = {
    "langchain_agent_stream": "langchain",
    "LangChainCallbackHandler": "langchain",
    "to_langchain_tools": "langchain",
    "langgraph_agent_stream": "langgraph",
    "deep_agent_stream": "deepagents",
    "deep_agent_resume": "deepagents",
    "DeepAgentConfig": "deepagents",
    "to_deep_agent_tools": "deepagents",
}


def __getattr__(name: str):
    """Lazy import for optional LangChain/LangGraph adapters."""
    module = _LANGCHAIN_EXPORTS.get(name)
    if module is not None:
        import importlib

        mod = importlib.import_module(f"kokage_ui.ai.{module}")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentEvent",
    "AgentMessage",
    "AgentView",
    "Attachment",
    "ChatMessage",
    "ChatView",
    "ConversationStore",
    "FilePreview",
    "InMemoryConversationStore",
    "LangChainCallbackHandler",
    "Message",
    "Thread",
    "ToolCall",
    "ToolInfo",
    "ToolRegistry",
    "ThreadedAgentView",
    "agent_stream",
    "chat_stream",
    "langchain_agent_stream",
    "langgraph_agent_stream",
    "to_langchain_tools",
    "deep_agent_stream",
    "deep_agent_resume",
    "DeepAgentConfig",
    "to_deep_agent_tools",
]
