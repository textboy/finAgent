import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function App() {
  const [model, setModel] = useState('');
  const [symbol, setSymbol] = useState('');
  const [period, setPeriod] = useState('medium');
  const [log, setLog] = useState('');
  const [results, setResults] = useState({});
  const [reportPath, setReportPath] = useState('');
  const [loading, setLoading] = useState(false);
  const logEndRef = useRef(null);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  const handleSubmit = async (data) => {
    if (!symbol.trim() || !period.trim()) {
      setLog(prev => prev + '⚠️ Please provide symbol and investment period.\n');
      return;
    }
    setLoading(true);
    setResults({});
    setReportPath('');
    setLog(`🚀 Starting analysis for ${symbol.toUpperCase()} (${period})...\n`);
    
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: model.trim() || undefined, symbol: symbol.trim(), period }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setLog(data.log);
      setResults(data.reports);
      setReportPath(`http://localhost:8000${data.report_path}`);
    } catch (err) {
      setLog(prev => prev + `\n❌ Error: ${err.message}\n`);
    } finally {
      setLoading(false);
    }
  };

  const panelKeys = [
    { key: 'fundamentals', label: 'Fundamentals', icon: '📊', color: 'from-blue-500 to-cyan-500' },
    { key: 'sentiment', label: 'Sentiment', icon: '💬', color: 'from-emerald-500 to-teal-500' },
    { key: 'technical', label: 'Technical', icon: '📈', color: 'from-purple-500 to-pink-500' },
    { key: 'research', label: 'Research Debate', icon: '🧠', color: 'from-amber-500 to-orange-500' },
    { key: 'trading', label: 'Trading Plan', icon: '🎯', color: 'from-indigo-500 to-blue-500' },
    { key: 'risk', label: 'Risk Management', icon: '🛡️', color: 'from-rose-500 to-red-500' },
    { key: 'finalEval', label: 'Final Evaluation', icon: '🏁', color: 'from-violet-500 to-purple-500' },
  ];

  const markdownComponents = {
    h1: ({children}) => <h1 className="text-xl font-bold mb-4 text-white border-b border-slate-700 pb-3">{children}</h1>,
    h2: ({children}) => <h2 className="text-lg font-semibold mb-3 text-slate-200 mt-4 flex items-center gap-2"><div className="w-2 h-2 bg-purple-500 rounded-full"></div>{children}</h2>,
    h3: ({children}) => <h3 className="text-base font-medium mb-2 text-slate-300 mt-3">{children}</h3>,
    p: ({children}) => <p className="mb-4 leading-relaxed text-slate-400 text-sm">{children}</p>,
    ul: ({children}) => <ul className="list-disc ml-5 mb-4 space-y-2 text-slate-400 text-sm">{children}</ul>,
    ol: ({children}) => <ol className="list-decimal ml-5 mb-4 space-y-2 text-slate-400 text-sm">{children}</ol>,
    li: ({children}) => <li className="pl-1">{children}</li>,
    strong: ({children}) => <strong className="font-semibold text-white">{children}</strong>,
    code: ({children}) => <code className="bg-slate-800/50 px-2 py-1 rounded-lg font-mono text-cyan-300 text-xs border border-slate-700">{children}</code>,
    pre: ({children}) => <pre className="bg-slate-900/80 p-4 rounded-xl overflow-x-auto font-mono text-slate-300 text-xs my-4 border border-slate-700 shadow-inner">{children}</pre>,
    blockquote: ({children}) => <blockquote className="border-l-4 border-purple-500 bg-gradient-to-r from-slate-900/50 to-transparent pl-4 py-3 italic my-4 text-slate-400 text-sm rounded-r-lg">{children}</blockquote>,
    table: ({children}) => <div className="overflow-x-auto my-4 rounded-lg border border-slate-800"><table className="w-full border-collapse text-sm text-left">{children}</table></div>,
    th: ({children}) => <th className="border-b border-slate-700 p-3 font-semibold text-slate-300 bg-slate-900/80">{children}</th>,
    td: ({children}) => <td className="border-b border-slate-800 p-3 text-slate-400">{children}</td>,
    hr: () => <hr className="border-slate-800 my-6" />,
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-200 font-sans">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse-glow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-float"></div>
      </div>

      {/* Navbar */}
      <nav className="sticky top-0 z-50 glass-panel border-b border-slate-800/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-purple-900/50 border border-purple-500/30">
                  <span className="text-white font-bold text-2xl">F</span>
                </div>
                <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl blur opacity-30 -z-10"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
                  FinAgent
                </h1>
                <p className="text-xs text-slate-500 font-mono mt-1">AI-Powered Financial Intelligence</p>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/50 rounded-lg border border-slate-800">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-mono text-slate-400">System Online</span>
              </div>
              <div className="text-xs font-mono text-slate-500 bg-slate-900/30 px-3 py-1.5 rounded border border-slate-800">
                v1.0
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        
        {/* Hero Section */}
        <section className="text-center space-y-6 animate-slide-up">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Advanced Financial <span className="text-glow bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-cyan-500">Analysis</span> Platform
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto text-xl leading-relaxed">
            Get comprehensive AI-driven insights for any stock symbol with detailed fundamentals, sentiment, technical, and risk analysis.
          </p>
        </section>

        {/* Input Section */}
        <section className="glass-panel rounded-2xl p-1 border-glow animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="bg-gradient-to-br from-slate-900/80 to-slate-950/80 rounded-2xl p-8 sm:p-10 space-y-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-4 h-4 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-full"></div>
              <h3 className="text-xl font-semibold text-white">Analysis Configuration</h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-6">
              
              {/* Symbol Input */}
              <div className="lg:col-span-4 space-y-2">
                <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-500"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
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
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                  </div>
                </div>
              </div>

              {/* Period Select */}
              <div className="lg:col-span-4 space-y-2">
                <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
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
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                  </div>
                </div>
              </div>

              {/* Model Input */}
              <div className="lg:col-span-3 space-y-2">
                <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500"><path d="M12 2v4"></path><path d="m16.2 7.8 2.9-2.9"></path><path d="M18 12h4"></path><path d="m16.2 16.2 2.9 2.9"></path><path d="M12 18v4"></path><path d="m4.9 19.1 2.9-2.9"></path><path d="M2 12h4"></path><path d="m4.9 4.9 2.9 2.9"></path></svg>
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

              {/* Submit Button */}
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
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Log Section */}
        <section className="glass-panel rounded-2xl overflow-hidden border-l-4 border-l-cyan-500/50 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="bg-gradient-to-b from-slate-950 to-slate-900 p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-xl font-semibold text-white flex items-center gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
                System Logs
              </h3>
              <div className="text-sm font-mono text-slate-500 bg-slate-900/50 px-4 py-1.5 rounded-full">
                Real-time
              </div>
            </div>
            <div className="bg-black/40 rounded-xl p-5 font-mono text-sm text-slate-300 h-48 overflow-y-auto scrollbar-hide border border-slate-800/50">
              <div className="whitespace-pre-wrap leading-relaxed">
                {log || <span className="text-slate-600 italic">// System ready. Enter a stock symbol and click Analyze to begin...</span>}
              </div>
              <div ref={logEndRef} />
            </div>
          </div>
        </section>

        {/* Results Grid */}
        {Object.keys(results).length > 0 && (
          <div className="space-y-10 animate-slide-up" style={{ animationDelay: '0.3s' }}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold text-white flex items-center gap-4">
                  <div className="w-4 h-10 bg-gradient-to-b from-purple-500 to-cyan-500 rounded-full"></div>
                  Analysis Report
                </h2>
                <p className="text-slate-500 text-base mt-2">Comprehensive insights generated by AI</p>
              </div>
              {reportPath && (
                <a
                  href={reportPath}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-slate-900 to-slate-800 hover:from-slate-800 hover:to-slate-700 text-cyan-400 rounded-xl text-base font-medium transition-all duration-300 border border-slate-700 hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-900/20"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                  View Full Report
                </a>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {panelKeys.map(({ key, label, icon, color }, index) => (
                <div 
                  key={key} 
                  className={`glass-panel rounded-2xl overflow-hidden flex flex-col border border-slate-800/50 hover:border-slate-700/50 transition-all duration-500 hover:scale-[1.02] ${key === 'finalEval' ? 'lg:col-span-2' : ''}`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className={`px-6 py-4 bg-gradient-to-r ${color} flex items-center justify-between`}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{icon}</span>
                      <h3 className="font-bold text-white text-lg">{label}</h3>
                    </div>
                    <div className="text-white/80 text-xs font-mono bg-black/20 px-3 py-1 rounded-full">
                      {index + 1}/{panelKeys.length}
                    </div>
                  </div>
                  <div className="p-6 text-slate-300 bg-gradient-to-b from-slate-950/50 to-slate-900/30 flex-1">
                    {results[key] ? (
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={markdownComponents}
                      >
                        {results[key]}
                      </ReactMarkdown>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-slate-600 italic text-sm py-12">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-4 opacity-50"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        No data available for this section
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
      
      <footer className="relative z-10 mt-auto py-10 text-center text-slate-600 text-base border-t border-slate-900/50">
        <div className="max-w-7xl mx-auto px-4">
          <p>© 2026 FinAgent. AI-Powered Financial Analysis Platform.</p>
          <p className="mt-3 text-sm text-slate-700">All analysis is generated by AI and should be used for informational purposes only.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
