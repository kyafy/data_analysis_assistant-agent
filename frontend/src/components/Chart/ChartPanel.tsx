import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { useStore } from '../../store/useStore';
import { LineChart, LayoutDashboard, Table as TableIcon } from 'lucide-react';

export const ChartPanel: React.FC = () => {
  const { activeSessionId, messages } = useStore();

  // Find the latest visualization data (either chart or raw data)
  const currentVisual = useMemo(() => {
    if (!activeSessionId) return null;
    const sessionMessages = messages[activeSessionId] || [];
    // Traverse backwards to find the most recent chart or raw data
    for (let i = sessionMessages.length - 1; i >= 0; i--) {
      if (sessionMessages[i].chartSpec || sessionMessages[i].rawData) {
        return {
          chartSpec: sessionMessages[i].chartSpec,
          rawData: sessionMessages[i].rawData
        };
      }
    }
    return null;
  }, [activeSessionId, messages]);

  if (!activeSessionId) {
    return (
      <div className="w-96 bg-gray-50 border-l border-gray-200 h-full hidden lg:flex flex-col items-center justify-center text-gray-400">
        <LayoutDashboard size={48} className="text-gray-300 mb-4" />
        <p>暂无可视化内容</p>
      </div>
    );
  }

  const renderDataGrid = (data: any[]) => {
    if (!data || data.length === 0) return <div className="text-gray-400 text-center p-4">无数据返回</div>;
    
    // Check if it's a list of tuples/arrays or list of dicts
    const firstRow = data[0];
    let headers: string[] = [];
    let rows: any[][] = [];

    if (Array.isArray(firstRow)) {
      // List of tuples
      headers = firstRow.map((_, i) => `Column ${i + 1}`);
      rows = data;
    } else if (typeof firstRow === 'object' && firstRow !== null) {
      // List of dicts (if we ever get dicts)
      headers = Object.keys(firstRow);
      rows = data.map(item => headers.map(h => item[h]));
    } else {
      // Simple list of values
      headers = ['Value'];
      rows = data.map(item => [item]);
    }

    return (
      <div className="overflow-x-auto w-full max-h-[400px]">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {headers.map((header, i) => (
                <th key={i} className="px-6 py-3 text-left font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <bg-white className="divide-y divide-gray-200">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                {row.map((cell, j) => (
                  <td key={j} className="px-6 py-4 whitespace-nowrap text-gray-800">
                    {String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </bg-white>
        </table>
      </div>
    );
  };

  return (
    <div className="w-1/3 min-w-[320px] max-w-lg bg-gray-50 border-l border-gray-200 h-full hidden lg:flex flex-col">
      <div className="h-14 border-b border-gray-200 flex items-center px-4 bg-white shrink-0">
        <LineChart size={18} className="text-blue-600 mr-2" />
        <h2 className="font-semibold text-gray-800">可视化展示</h2>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {!currentVisual ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <LayoutDashboard size={48} className="text-gray-300 mb-4" />
            <p className="text-sm">对话中生成的数据图表将显示在这里</p>
          </div>
        ) : (
          <>
            {currentVisual.chartSpec && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-[400px]">
                <ReactECharts 
                  option={currentVisual.chartSpec} 
                  style={{ height: '100%', width: '100%' }} 
                  opts={{ renderer: 'canvas' }}
                />
              </div>
            )}
            
            {currentVisual.rawData && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col">
                <div className="px-4 py-3 border-b border-gray-100 flex items-center bg-gray-50/50 rounded-t-xl">
                  <TableIcon size={16} className="text-gray-500 mr-2" />
                  <span className="font-medium text-gray-700 text-sm">查询结果数据</span>
                  <span className="ml-auto text-xs text-gray-400">{currentVisual.rawData.length} 条记录</span>
                </div>
                {renderDataGrid(currentVisual.rawData)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
