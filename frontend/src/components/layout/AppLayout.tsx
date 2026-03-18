import React from 'react';
import { SessionPanel } from '../Sidebar/SessionPanel';
import { ChatPanel } from '../Chat/ChatPanel';
import { ChartPanel } from '../Chart/ChartPanel';
import { ConfigModal } from '../Config/ConfigModal';

export const AppLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-full bg-white overflow-hidden text-sm md:text-base">
      <SessionPanel />
      <ChatPanel />
      <ChartPanel />
      <ConfigModal />
    </div>
  );
};
