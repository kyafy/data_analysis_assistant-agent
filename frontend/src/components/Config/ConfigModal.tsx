import React, { useState, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { X, Save, Database, Loader2 } from 'lucide-react';

export const ConfigModal: React.FC = () => {
  const { isConfigOpen, toggleConfig } = useStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    host: '127.0.0.1',
    port: 3306,
    user: 'root',
    password: '',
    db: 'data_analysis'
  });
  const [status, setStatus] = useState<{ type: 'success' | 'error' | null, message: string }>({ type: null, message: '' });

  useEffect(() => {
    if (isConfigOpen) {
      // Fetch current config
      fetch('/api/config/db')
        .then(res => res.json())
        .then(data => {
          if (Object.keys(data).length > 0) {
            setFormData(prev => ({ ...prev, ...data, password: '' })); // Don't show password or show mask
          }
        })
        .catch(err => console.error('Failed to fetch config', err));
    }
  }, [isConfigOpen]);

  if (!isConfigOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: null, message: '' });

    try {
      const res = await fetch('/api/config/db', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await res.json();
      
      if (result.status === 'success') {
        setStatus({ type: 'success', message: '数据库连接已更新并重新加载！' });
        setTimeout(() => {
          toggleConfig(false);
          setStatus({ type: null, message: '' });
        }, 1500);
      } else {
        setStatus({ type: 'error', message: result.message || '连接失败，请检查配置' });
      }
    } catch (err) {
      setStatus({ type: 'error', message: '请求失败，请检查网络' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-2 text-gray-800">
            <Database size={20} className="text-blue-600" />
            <h2 className="font-semibold">数据库配置</h2>
          </div>
          <button 
            onClick={() => toggleConfig(false)}
            className="p-1 hover:bg-gray-200 rounded-full transition-colors text-gray-500"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
              <input
                type="text"
                required
                value={formData.host}
                onChange={e => setFormData({...formData, host: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                placeholder="127.0.0.1"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                <input
                  type="number"
                  required
                  value={formData.port}
                  onChange={e => setFormData({...formData, port: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="3306"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Database</label>
                <input
                  type="text"
                  required
                  value={formData.db}
                  onChange={e => setFormData({...formData, db: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="data_analysis"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input
                type="text"
                required
                value={formData.user}
                onChange={e => setFormData({...formData, user: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                placeholder="root"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={e => setFormData({...formData, password: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                placeholder="Leave empty to keep unchanged"
              />
            </div>
          </div>

          {status.message && (
            <div className={`p-3 rounded-lg text-sm ${status.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {status.message}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => toggleConfig(false)}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              保存并连接
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};