import json
import logging
from typing import Any, List, Optional, Iterator, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    ChatMessage
)
from langchain_core.outputs import ChatGeneration, ChatResult, ChatGenerationChunk
import dashscope
from http import HTTPStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatQwen(BaseChatModel):
    """
    Custom LangChain ChatModel wrapper for DashScope Qwen3-Max.
    Handles streaming tool calls aggregation manually as DashScope returns incremental chunks.
    """
    model_name: str = "qwen-max"
    streaming: bool = True
    dashscope_api_key: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.dashscope_api_key:
            self.dashscope_api_key = settings.DASHSCOPE_API_KEY
        dashscope.api_key = self.dashscope_api_key

    @property
    def _llm_type(self) -> str:
        return "dashscope-qwen"

    def bind_tools(
        self,
        tools: List[Any],
        **kwargs: Any,
    ) -> Any:
        """
        Bind tools to the model.
        LangChain's create_tool_calling_agent calls this.
        We need to return a RunnableBinding that passes tools to _generate/_stream.
        """
        from langchain_core.language_models.chat_models import BaseChatModel
        # BaseChatModel implementation usually returns self.bind(tools=formatted_tools)
        # But we need to format them for DashScope first if needed, or just pass them through
        # and let _stream handle conversion.
        # DashScope expects dicts in OpenAI format or its own format.
        # LangChain tools can be converted via convert_to_openai_tool usually.
        
        # Simple implementation: use parent's default bind_tools if available, 
        # or just bind 'tools' kwarg.
        # Since BaseChatModel raises NotImplementedError by default, we must implement it.
        
        from langchain_core.utils.function_calling import convert_to_openai_tool
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        
        return self.bind(tools=formatted_tools, **kwargs)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Sync generation (fallback to streaming implementation for consistency)
        """
        # For simplicity in this implementation, we can reuse _stream logic and collect chunks
        # or call dashscope non-streaming API.
        # Given requirement is heavily on streaming (SSE), let's implement via _stream accumulation.
        stream_iter = self._stream(messages, stop=stop, run_manager=run_manager, **kwargs)
        final_chunk: Optional[AIMessageChunk] = None
        for chunk in stream_iter:
            # chunk is ChatGenerationChunk, chunk.message is AIMessageChunk
            if final_chunk is None:
                final_chunk = chunk.message
            else:
                final_chunk += chunk.message
        
        if final_chunk:
            return ChatResult(generations=[ChatGeneration(message=final_chunk)])
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        
        dashscope_messages = self._convert_messages(messages)
        tools = kwargs.get("tools", None)
        
        # Prepare DashScope parameters
        params = {
            "model": self.model_name,
            "messages": dashscope_messages,
            "result_format": "message",
            "stream": True,
            "incremental_output": True,  # Critical for proper delta handling
        }
        
        # If tools are bound, LangChain passes them in kwargs.
        # We need to ensure they are in the format DashScope expects (dict with type='function').
        if tools:
            # Check if tools are already in DashScope format or need conversion
            # LangChain tools in kwargs usually come as a list of dicts conforming to OpenAI format, which DashScope supports.
            params["tools"] = tools

        try:
            responses = dashscope.Generation.call(**params)
        except Exception as e:
            logger.error(f"DashScope API call failed: {e}")
            raise e

        for response in responses:
            if response.status_code == HTTPStatus.OK:
                output = response.output
                choices = output.choices
                if not choices:
                    continue
                
                choice = choices[0]
                delta = choice.message
                
                # 1. Handle Content Delta
                if 'content' in delta and delta.content:
                    chunk = AIMessageChunk(content=delta.content)
                    if run_manager:
                        run_manager.on_llm_new_token(delta.content)
                    yield ChatGenerationChunk(message=chunk)
                
                # 2. Handle Tool Call Delta
                if 'tool_calls' in delta and delta.tool_calls:
                    # DashScope returns incremental tool_calls list
                    tool_call_chunks = []
                    for tc in delta.tool_calls:
                        index = tc.get('index', 0)
                        t_id = tc.get('id')
                        t_type = tc.get('type')
                        func = tc.get('function', {})
                        t_name = func.get('name')
                        t_args = func.get('arguments')
                        
                        tool_call_chunk = {
                            "index": index,
                            "id": t_id,
                            "type": "tool_call",
                            "name": t_name,
                            "args": t_args
                        }
                        tool_call_chunks.append(tool_call_chunk)
                    
                    chunk = AIMessageChunk(
                        content="",
                        tool_call_chunks=tool_call_chunks
                    )
                    # yield chunk to let LangChain aggregator handle the merge
                    yield ChatGenerationChunk(message=chunk)
                    
            else:
                err_msg = f"Request id: {response.request_id}, Status code: {response.status_code}, error code: {response.code}, error message: {response.message}"
                logger.error(err_msg)
                raise Exception(err_msg)

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Convert LangChain messages to DashScope format."""
        dash_messages = []
        for m in messages:
            if isinstance(m, HumanMessage):
                dash_messages.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                msg = {"role": "assistant", "content": m.content if m.content else ""}
                if m.tool_calls:
                    # If AI message has tool calls (from previous turn), include them
                    # DashScope expects 'tool_calls' field
                    msg["tool_calls"] = [
                        {
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]) if isinstance(tc["args"], dict) else tc["args"]
                            },
                            "id": tc["id"]
                        } for tc in m.tool_calls
                    ]
                dash_messages.append(msg)
            elif isinstance(m, SystemMessage):
                dash_messages.append({"role": "system", "content": m.content})
            elif isinstance(m, ToolMessage):
                # Result of a tool execution
                dash_messages.append({
                    "role": "tool",
                    "content": m.content,
                    "tool_call_id": m.tool_call_id
                })
            elif isinstance(m, ChatMessage):
                dash_messages.append({"role": m.role, "content": m.content})
            else:
                raise ValueError(f"Unsupported message type: {type(m)}")
        return dash_messages
