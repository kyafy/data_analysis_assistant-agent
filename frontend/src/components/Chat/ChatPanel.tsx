import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { Send, Square, Bot, User, Database, LineChart, Code2 } from 'lucide-react';
import { clsx } from 'clsx';
import type { Message } from '../../types';

const StatusIcon = ({ status }: { status: Message['status'] }) => {
  switch (status) {
    case 'thinking': return <Bot className="animate-pulse text-blue-500" size={16} />;
    case 'sql': return <Code2 className="text-purple-500" size={16} />;
    case 'query': return <Database className="text-orange-500" size={16} />;
    case 'chart': return <LineChart className="text-green-500" size={16} />;
    case 'answer': return <Bot className="text-blue-600" size={16} />;
    case 'error': return <Bot className="text-red-500" size={16} />;
    default: return <Bot className="text-blue-600" size={16} />;
  }
};

const MessageItem = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={clsx("flex gap-4 p-4", isUser ? "bg-white" : "bg-gray-50")}>
      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
        isUser ? "bg-gray-200 text-gray-700" : "bg-blue-100 text-blue-600"
      )}>
        {isUser ? <User size={20} /> : <StatusIcon status={message.status} />}
      </div>
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="font-medium text-sm text-gray-900">
          {isUser ? '我' : '数据分析助手'}
        </div>
        
        {/* Status indicator for assistant */}
        {!isUser && message.status && message.status !== 'answer' && message.status !== 'error' && (
          <div className="text-xs text-gray-500 flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            {message.status === 'thinking' && '正在理解意图...'}
            {message.status === 'sql' && '正在生成查询...'}
            {message.status === 'query' && '正在执行数据库查询...'}
            {message.status === 'chart' && '正在编排图表...'}
          </div>
        )}

        {/* Generated SQL if exists */}
        {message.sql && (
          <div className="bg-gray-800 text-gray-100 p-3 rounded-md text-sm font-mono overflow-x-auto">
            <div className="text-xs text-gray-400 mb-1 select-none">执行的 SQL:</div>
            {message.sql}
          </div>
        )}

        <div className={clsx("text-gray-800 leading-relaxed whitespace-pre-wrap", message.status === 'error' && "text-red-500")}>
          {message.content}
        </div>
      </div>
    </div>
  );
};

export const ChatPanel: React.FC = () => {
  const { activeSessionId, messages, isGenerating, addMessage, setGenerating } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentMessages = activeSessionId ? (messages[activeSessionId] || []) : [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentMessages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeSessionId || isGenerating) return;

    const currentInput = input.trim();
    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: currentInput,
    };
    addMessage(activeSessionId, userMsg);
    setInput('');
    setGenerating(true);

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      status: 'thinking'
    };
    addMessage(activeSessionId, assistantMsg);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          question: currentInput
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let fullContent = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (!dataStr) continue;

              try {
                const data = JSON.parse(dataStr);
                
                if (data.status === 'error') {
                   useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                     status: 'error',
                     content: data.delta || 'An error occurred'
                   });
                   break;
                }

                if (data.status === 'answer') {
                  fullContent += (data.delta || '');
                  useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                    status: 'answer',
                    content: fullContent
                  });
                } else if (data.status === 'sql') {
                  useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                    status: 'sql',
                    sql: data.sql
                  });
                } else if (data.status === 'chart') {
                  useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                    status: 'chart',
                    chartSpec: data.chart_spec
                  });
                } else if (data.status === 'data') {
                  useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                    rawData: data.data
                  });
                } else if (data.status) {
                  useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
                    status: data.status as any
                  });
                }

                if (data.final) {
                  break;
                }
              } catch (e) {
                console.error('Error parsing SSE JSON:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error fetching chat stream:', error);
      useStore.getState().updateMessage(activeSessionId, assistantMsgId, { 
        status: 'error',
        content: 'Failed to connect to the server.'
      });
    } finally {
      setGenerating(false);
    }
  };

  if (!activeSessionId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-gray-400">请选择或新建一个对话</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white min-w-0">
      {/* Header */}
      <div className="h-14 border-b border-gray-200 flex items-center px-4 shrink-0">
        <h2 className="font-semibold text-gray-800">数据分析会话</h2>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto">
        {currentMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
            <Bot size={48} className="text-gray-300" />
            <p>你好！我是数据分析助手。请告诉我你想了解什么数据？</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {currentMessages.map(msg => (
              <MessageItem key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-200">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="输入自然语言查询，例如：上个月各地区销售额对比"
            className="w-full pl-4 pr-12 py-3 rounded-xl border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none shadow-sm min-h-[52px] max-h-32"
            rows={1}
            disabled={isGenerating}
          />
          <div className="absolute right-2 bottom-2">
            {isGenerating ? (
              <button
                type="button"
                className="p-2 bg-red-100 text-red-600 hover:bg-red-200 rounded-lg transition-colors"
                title="停止生成"
              >
                <Square size={18} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="p-2 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                <Send size={18} />
              </button>
            )}
          </div>
        </form>
        <div className="text-center mt-2 text-xs text-gray-400">
          按 Enter 发送，Shift + Enter 换行
        </div>
      </div>
    </div>
  );
};
