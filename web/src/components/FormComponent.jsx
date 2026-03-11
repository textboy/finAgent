import { useState, useEffect } from 'react';

function FormComponent({ onSubmit }) {
  const [symbol, setSymbol] = useState('');
  const [period, setPeriod] = useState('medium');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!symbol.trim() || !period.trim()) {
      alert('Please provide symbol and investment period');
      return;
    }
    setLoading(true);
    try {
      await onSubmit({ symbol, period, model });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/80 to-slate-950/80 rounded-2xl p-6 sm:p-8 space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-3 h-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-full"></div>
        <h3 className="text-lg font-semibold text-white">Analysis Configuration</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4 space-y-2">
          <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-500">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
            Stock Symbol
          </label>
          <div className="relative">
            <input 
              type="text" 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="input-field text-lg font-bold tracking-wide uppercase pl-12"
              placeholder="AAPL"
            />
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-purple-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="16"></line>
                <line x1="8" y1="12" x2="16" y2="12"></line>
              </svg>
            </div>
          </div>
        </div>
        <div className="lg:col-span-3 space-y-2">
          <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            Time Horizon
          </label>
          <div className="relative">
            <select 
              value={period} 
              onChange={(e) => setPeriod(e.target.value)}
              className="input-field appearance-none cursor-pointer pl-10"
            >
              <option value="short+">Short+</option>
              <option value="short">Short</option>
              <option value="medium">Medium</option>
              <option value="long">Long</option>
            </select>
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
          </div>
        </div>
        <div className="lg:col-span-3 space-y-2">
          <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500">
              <path d="M12 2v4"></path>
              <path d="m16.2 7.8 2.9-2.9"></path>
              <path d="M18 12h4"></path>
              <path d="m16.2 16.2 2.9 2.9"></path>
              <path d="M12 18v4"></path>
              <path d="m4.9 19.1 2.9-2.9"></path>
              <path d="M2 12h4"></path>
              <path d="m4.9 4.9 2.9 2.9"></path>
            </svg>
            AI Model
          </label>
          <input 
            type="text" 
            value={model} 
            onChange={(e) => setModel(e.target.value)}
            className="input-field text-sm pl-10"
            placeholder="Default"
          />
        </div>
        <div className="lg:col-span-2 flex items-end">
          <button 
            onClick={handleSubmit}
            disabled={loading || !symbol.trim()}
            className="btn-primary h-[52px] flex items-center justify-center gap-3 text-base font-semibold"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Processing</span>
              </>
            ) : (
              <>
                <span>Analyze</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14"></path>
                  <path d="m12 5 7 7-7 7"></path>
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default FormComponent;