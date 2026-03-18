export interface Session {
  id: string;
  title: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status?: 'thinking' | 'sql' | 'query' | 'chart' | 'answer' | 'error' | 'data';
  sql?: string;
  chartSpec?: any; // ECharts option type
  rawData?: any[]; // Array of rows/tuples returned from SQL query
}

export interface Session {
  id: string;
  title: string;
  updatedAt: string;
}

export interface AppState {
  sessions: Session[];
  activeSessionId: string | null;
  messages: Record<string, Message[]>;
  isGenerating: boolean;
  isConfigOpen: boolean;
  addSession: () => void;
  deleteSession: (id: string) => void;
  setActiveSession: (id: string) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateMessage: (sessionId: string, messageId: string, updates: Partial<Message>) => void;
  setGenerating: (status: boolean) => void;
  toggleConfig: (isOpen?: boolean) => void;
}
