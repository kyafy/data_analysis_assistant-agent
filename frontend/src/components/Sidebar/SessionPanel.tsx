import React from 'react';
import { useStore } from '../../store/useStore';
import { Plus, MessageSquare, Trash2, Settings } from 'lucide-react';
import { clsx } from 'clsx';

export const SessionPanel: React.FC = () => {
  const { sessions, activeSessionId, addSession, setActiveSession, deleteSession, toggleConfig } = useStore();

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={addSession}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={18} />
          <span>新建对话</span>
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => setActiveSession(session.id)}
            className={clsx(
              "group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors",
              activeSessionId === session.id 
                ? "bg-blue-100 text-blue-900" 
                : "hover:bg-gray-200 text-gray-700"
            )}
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <MessageSquare size={18} className="shrink-0" />
              <span className="truncate text-sm font-medium">
                {session.title}
              </span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteSession(session.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-600 rounded transition-all"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-200">
        <button
          onClick={() => toggleConfig(true)}
          className="w-full flex items-center justify-center gap-2 text-gray-600 hover:bg-gray-200 px-4 py-2 rounded-lg transition-colors"
        >
          <Settings size={18} />
          <span>数据库设置</span>
        </button>
      </div>
    </div>
  );
};
