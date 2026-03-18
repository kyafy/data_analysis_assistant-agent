import { create } from 'zustand';
import type { AppState, Message, Session } from '../types';

const MOCK_SESSIONS: Session[] = [
  { id: '1', title: '销售数据分析', updatedAt: new Date().toISOString() },
  { id: '2', title: '用户增长趋势', updatedAt: new Date(Date.now() - 86400000).toISOString() },
];

const MOCK_MESSAGES: Record<string, Message[]> = {
  '1': [
    { id: 'm1', role: 'user', content: '帮我分析一下上个月的销售数据，按地区分布展示。' },
    { 
      id: 'm2', 
      role: 'assistant', 
      content: '根据您的要求，我查询了上个月的销售数据。华东地区的销售额最高，达到了 150 万，占比约 45%。其次是华南地区，销售额为 80 万。以下是各地区的具体销售额分布图表。',
      status: 'answer',
      sql: 'SELECT region, SUM(amount) as total_sales FROM sales WHERE month = "2023-09" GROUP BY region;',
      chartSpec: {
        title: { text: '各地区销售额分布', left: 'center' },
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left' },
        series: [
          {
            name: '销售额',
            type: 'pie',
            radius: '50%',
            data: [
              { value: 1500000, name: '华东' },
              { value: 800000, name: '华南' },
              { value: 600000, name: '华北' },
              { value: 400000, name: '西部' }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    }
  ],
  '2': []
};

export const useStore = create<AppState>((set) => ({
  sessions: MOCK_SESSIONS,
  activeSessionId: '1',
  messages: MOCK_MESSAGES,
  isGenerating: false,
  isConfigOpen: false,

  addSession: () => set((state) => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: '新对话',
      updatedAt: new Date().toISOString(),
    };
    return {
      sessions: [newSession, ...state.sessions],
      activeSessionId: newSession.id,
      messages: { ...state.messages, [newSession.id]: [] }
    };
  }),

  deleteSession: (id) => set((state) => {
    const newSessions = state.sessions.filter(s => s.id !== id);
    const newMessages = { ...state.messages };
    delete newMessages[id];
    
    return {
      sessions: newSessions,
      activeSessionId: state.activeSessionId === id 
        ? (newSessions[0]?.id || null) 
        : state.activeSessionId,
      messages: newMessages
    };
  }),

  setActiveSession: (id) => set({ activeSessionId: id }),

  addMessage: (sessionId, message) => set((state) => ({
    messages: {
      ...state.messages,
      [sessionId]: [...(state.messages[sessionId] || []), message]
    }
  })),

  updateMessage: (sessionId, messageId, updates) => set((state) => {
    const sessionMessages = state.messages[sessionId] || [];
    const messageIndex = sessionMessages.findIndex(m => m.id === messageId);
    
    if (messageIndex === -1) return state;

    const newMessages = [...sessionMessages];
    newMessages[messageIndex] = { ...newMessages[messageIndex], ...updates };

    return {
      messages: {
        ...state.messages,
        [sessionId]: newMessages
      }
    };
  }),

  setGenerating: (status) => set({ isGenerating: status }),
  
  toggleConfig: (isOpen) => set((state) => ({ 
    isConfigOpen: isOpen !== undefined ? isOpen : !state.isConfigOpen 
  })),
}));
