import { useState, useEffect, useRef, useMemo } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Introduction from './Introduction.jsx'

function HomePage() {
  // Use current browser host/port for API calls
  const serverHost = window.location.hostname;
  const uvicornPort = window.location.port || '8000';

  const [symbolInput, setSymbolInput] = useState('');
  const [period, setPeriod] = useState('medium');
  const [log, setLog] = useState('');
  const [multiResults, setMultiResults] = useState([]);
  const [timing, setTiming] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedPanels, setExpandedPanels] = useState({});
  const [symbolWarning, setSymbolWarning] = useState('');
  const [tickerMapping, setTickerMapping] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [justSelected, setJustSelected] = useState(false);
  const [historyReports, setHistoryReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState('');
  const [viewingHistory, setViewingHistory] = useState(false);
  const abortControllerRef = useRef(null);
  const isSubmittingRef = useRef(false);
  const logEndRef = useRef(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const periodRef = useRef(null);

  // Load ticker mapping on mount
  useEffect(() => {
    fetch(`http://${serverHost}:${uvicornPort}/public/ticket_mapping.json`)
      .then(res => res.json())
      .then(data => setTickerMapping(data))
      .catch(err => console.error('Failed to load ticker mapping:', err));
  }, [serverHost, uvicornPort]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Get current typing symbol (last part after separator)
  const getCurrentSymbol = () => {
    const parts = symbolInput.split(/[,;]/);
    return parts[parts.length - 1].trim();
  };

  // Filter suggestions based on input
  useEffect(() => {
    // Skip if a suggestion was just selected
    if (justSelected) {
      setJustSelected(false);
      return;
    }

    const query = getCurrentSymbol().toLowerCase();
    if (query.length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      setHighlightedIndex(-1);
      return;
    }

    const filtered = tickerMapping.filter(item => {
      if (!item || !item.ticker) return false;
      const matchTicker = item.ticker?.toLowerCase().includes(query);
      const matchName = item.name?.toLowerCase().includes(query);
      const matchAlias = item.aliases?.some(alias => alias?.toLowerCase().includes(query));
      return matchTicker || matchName || matchAlias;
    }).slice(0, 8); // Limit to 8 suggestions

    setSuggestions(filtered);
    setShowSuggestions(filtered.length > 0);
    setHighlightedIndex(-1);
  }, [symbolInput, tickerMapping, justSelected]);

  const selectSuggestion = (ticker) => {
    const parts = symbolInput.split(/[,;]/);
    parts[parts.length - 1] = ticker;
    setJustSelected(true);
    setSymbolInput(parts.join(','));
    setShowSuggestions(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    // Handle Escape to close suggestions
    if (e.key === 'Escape') {
      setShowSuggestions(false);
      setHighlightedIndex(-1);
      return;
    }

    // Handle Tab key - move focus to period select
    if (e.key === 'Tab') {
      e.preventDefault();
      setShowSuggestions(false);
      setHighlightedIndex(-1);
      if (periodRef.current) {
        periodRef.current.focus();
      }
      return;
    }

    // Handle Enter key
    if (e.key === 'Enter') {
      // If suggestions are showing and an item is highlighted, select it
      if (showSuggestions && suggestions.length > 0 && highlightedIndex >= 0) {
        e.preventDefault();
        selectSuggestion(suggestions[highlightedIndex].ticker);
        return;
      }

      // Otherwise, trigger analyze if symbols are inputted
      const symbols = symbolInput
        .split(/[,;]/)
        .map(s => s.trim())
        .filter(s => s.length > 0);

      if (symbols.length > 0 && period) {
        e.preventDefault();
        handleSubmit();
      }
      return;
    }

    // Handle Arrow keys when suggestions are visible
    if (showSuggestions && suggestions.length > 0) {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev =>
            prev > 0 ? prev - 1 : suggestions.length - 1
          );
          break;
        default:
          break;
      }
    }
  };

  const togglePanel = (symbol, key) => {
    const panelId = `${symbol}-${key}`;
    setExpandedPanels(prev => ({ ...prev, [panelId]: !prev[panelId] }));
  };

  const isPanelExpanded = (symbol, key) => {
    // Trading panel (step 7) is expanded by default
    if (key === 'trading') return expandedPanels[`${symbol}-${key}`] !== false;
    return expandedPanels[`${symbol}-${key}`] === true;
  };

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  const validateTicker = (ticker) => {
    if (!ticker || ticker.length === 0) return false;
    return tickerMapping.some(item => item.ticker === ticker.toUpperCase());
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsAnalyzing(false);
    setLoading(false);
    setLog(prev => prev + `\n⏹️ Analysis stopped by user.\n`);
  };

  const fetchHistoryReports = async () => {
    try {
      const response = await fetch(`http://${serverHost}:${uvicornPort}/api/history-reports`);
      if (response.ok) {
        const data = await response.json();
        setHistoryReports(data.reports || []);
      }
    } catch (err) {
      console.error('Failed to fetch history reports:', err);
    }
  };

  const viewReport = () => {
    if (selectedReport) {
      window.open(`http://${serverHost}:${uvicornPort}/static/${selectedReport}`, '_blank');
    }
  };

  // Load history reports on mount
  useEffect(() => {
    fetchHistoryReports();
  }, []);

  const handleSubmit = async () => {
    // Prevent duplicate submissions
    if (loading || isAnalyzing || isSubmittingRef.current) {
      return;
    }

    if (!symbolInput.trim() || !period.trim()) {
      setLog(prev => prev + '⚠️ Please provide symbol(s) and investment period.\n');
      isSubmittingRef.current = false;
      return;
    }

    // Set submitting flag immediately
    isSubmittingRef.current = true;

    // Parse symbols (split by comma or semicolon)
    const symbols = symbolInput
      .split(/[,;]/)
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0);

    // Validate max 5 symbols
    if (symbols.length > 5) {
      setSymbolWarning('⚠️ Maximum 5 symbols allowed. Only the first 5 will be analyzed.');
      symbols.splice(5); // Keep only first 5
    } else {
      setSymbolWarning('');
    }

    // Validate tickers against mapping
    const invalidTickers = symbols.filter(s => !validateTicker(s));
    if (invalidTickers.length > 0) {
      setLog(prev => prev + `❌ Invalid ticker(s): ${invalidTickers.join(', ')}\n`);
      setLog(prev => prev + `💡 Please check the ticker symbol. Example: AAPL, GOOG, MSFT\n`);
      isSubmittingRef.current = false;
      return;
    }

    setLoading(true);
    setIsAnalyzing(true);
    setMultiResults([]);
    setTiming(null);
    setExpandedPanels({});
    setLog(`🚀 Starting analysis for ${symbols.join(', ')} (${period})...\n`);

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`http://${serverHost}:${uvicornPort}/analyze-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols, period }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setMultiResults(data.results);
      // Use timing from first result for display
      if (data.results.length > 0 && data.results[0].timing) {
        setTiming(data.results[0].timing);
      }

      // Log step completion for all results
      let stepLog = '';
      data.results.forEach(result => {
        if (result.step_logs && result.step_logs.length > 0) {
          result.step_logs.forEach(log => {
            stepLog += `${log}\n`;
          });
        }
      });

      if (stepLog) {
        setLog(prev => prev + `\n📊 Step Progress:\n${stepLog}`);
      }

      // Log errors from all results
      let errorLog = '';
      data.results.forEach(result => {
        if (result.errors && result.errors.length > 0) {
          errorLog += `\n📋 ${result.symbol}:\n`;
          result.errors.forEach(err => {
            errorLog += `  ${err}\n`;
          });
        }
      });

      if (errorLog) {
        setLog(prev => prev + `\n⚠️ Pipeline Warnings:${errorLog}`);
      }

      setLog(prev => prev + `\n✅ Analysis complete for ${data.results.length} symbol(s).\n`);
    } catch (err) {
      if (err.name === 'AbortError') {
        setLog(prev => prev + `\n⏹️ Analysis cancelled.\n`);
      } else {
        setLog(prev => prev + `\n❌ Error: ${err.message}\n`);
      }
    } finally {
      setLoading(false);
      setIsAnalyzing(false);
      isSubmittingRef.current = false;
      abortControllerRef.current = null;
    }
  };

  const panelKeys = [
    { key: 'fundamentals', label: 'Fundamentals', icon: '📊', color: 'from-blue-500 to-cyan-500' },
    { key: 'sentiment', label: 'Sentiment & Social', icon: '💬', color: 'from-emerald-500 to-teal-500' },
    { key: 'technical', label: 'Technical', icon: '📈', color: 'from-purple-500 to-pink-500' },
    { key: 'market', label: 'Market Overview', icon: '🌍', color: 'from-orange-500 to-red-500' },
    { key: 'globalEconomic', label: 'Global Economy', icon: '🌐', color: 'from-cyan-500 to-blue-500' },
    { key: 'fundHolding', label: 'Fund Holdings', icon: '🏦', color: 'from-teal-500 to-cyan-500' },
    { key: 'pastLessons', label: 'Past Lessons', icon: '📚', color: 'from-yellow-500 to-amber-500' },
    { key: 'research', label: 'Research Debate', icon: '🧠', color: 'from-amber-500 to-orange-500' },
    { key: 'trading', label: 'Trading Plan', icon: '🎯', color: 'from-indigo-500 to-blue-500' },
  ];

  const markdownComponents = {
    h1: ({children}) => <h1 className="text-xl font-bold mb-5 text-white border-b border-slate-700 pb-3">{children}</h1>,
    h2: ({children}) => <h2 className="text-lg font-semibold mb-4 text-slate-200 mt-6 flex items-center gap-2"><div className="w-2 h-2 bg-purple-500 rounded-full"></div>{children}</h2>,
    h3: ({children}) => <h3 className="text-base font-medium mb-3 text-slate-300 mt-4">{children}</h3>,
    h4: ({children}) => <h4 className="text-sm font-semibold mb-2 text-slate-300 mt-3 uppercase tracking-wide">{children}</h4>,
    p: ({children}) => <p className="mb-4 leading-relaxed text-slate-400 text-sm">{children}</p>,
    ul: ({children}) => <ul className="list-disc ml-5 mb-4 space-y-2 text-slate-400 text-sm">{children}</ul>,
    ol: ({children}) => <ol className="list-decimal ml-5 mb-4 space-y-2 text-slate-400 text-sm">{children}</ol>,
    li: ({children}) => <li className="pl-1 leading-relaxed">{children}</li>,
    strong: ({children}) => <strong className="font-semibold text-white">{children}</strong>,
    em: ({children}) => <em className="italic text-slate-300">{children}</em>,
    code: ({children}) => <code className="bg-slate-800/50 px-2 py-1 rounded-lg font-mono text-cyan-300 text-xs border border-slate-700">{children}</code>,
    pre: ({children}) => <pre className="bg-slate-900/80 p-4 rounded-xl overflow-x-auto font-mono text-slate-300 text-xs my-4 border border-slate-700 shadow-inner">{children}</pre>,
    blockquote: ({children}) => <blockquote className="border-l-4 border-purple-500 bg-gradient-to-r from-slate-900/50 to-transparent pl-4 py-3 italic my-4 text-slate-400 text-sm rounded-r-lg">{children}</blockquote>,
    table: ({children}) => <div className="overflow-x-auto my-4 rounded-lg border border-slate-800"><table className="w-full border-collapse text-sm text-left">{children}</table></div>,
    thead: ({children}) => <thead className="bg-slate-900/50">{children}</thead>,
    tbody: ({children}) => <tbody className="divide-y divide-slate-800">{children}</tbody>,
    th: ({children}) => <th className="border-b border-slate-700 p-3 font-semibold text-slate-300 bg-slate-900/80">{children}</th>,
    td: ({children}) => <td className="border-b border-slate-800 p-3 text-slate-400">{children}</td>,
    hr: () => <hr className="border-slate-800 my-6" />,
    a: ({href, children}) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2">{children}</a>,
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
          <div className="flex items-center justify-between h-16 sm:h-20">
            <Link to="/" className="flex items-center gap-2 sm:gap-3">
              <div>
                <h1 className="text-xl sm:text-2xl bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
                  FinAgent
                </h1>
                <p className="text-[10px] sm:text-xs text-slate-500 font-mono mt-0.5 sm:mt-1 hidden sm:block">AI-Powered Financial Intelligence</p>
              </div>
            </Link>
            <div className="flex items-center gap-2 sm:gap-4">
              <Link
                to="/introduction"
                className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 bg-slate-900/50 rounded-lg border border-slate-800 hover:border-purple-500/50 hover:bg-slate-800/50 transition-all duration-300"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <span className="text-[10px] sm:text-xs font-mono text-slate-400 hidden sm:inline">Introduction</span>
              </Link>
              <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 bg-slate-900/50 rounded-lg border border-slate-800">
                <div className="w-1.5 sm:w-2 h-1.5 sm:h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-[10px] sm:text-xs font-mono text-slate-400 hidden sm:inline">Online</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-12 space-y-6 sm:space-y-12">

        {/* Hero Section */}
        <section className="text-center space-y-4 sm:space-y-6 animate-slide-up">
          <h2 className="text-2xl sm:text-4xl md:text-5xl font-bold text-white">
            Advanced Financial <span className="text-glow bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-cyan-500">Analysis</span> Platform
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto text-base sm:text-xl leading-relaxed">
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
            
            <div className="space-y-4">
              {/* Symbol Input */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-500"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                  Symbols
                </label>
                <div className="relative" ref={suggestionsRef}>
                  <input
                    ref={inputRef}
                    type="text"
                    value={symbolInput}
                    onChange={(e) => {
                      // Auto-convert to uppercase and trim spaces between symbols
                      const value = e.target.value.toUpperCase().replace(/\s+/g, '');
                      setSymbolInput(value);
                    }}
                    onKeyDown={handleKeyDown}
                    onFocus={() => {
                      if (suggestions.length > 0) setShowSuggestions(true);
                    }}
                    className="input-field text-sm sm:text-base tracking-wide uppercase pr-16"
                    placeholder="AAPL,GOOG,MSFT"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500">max 5</span>

                  {/* Suggestions Dropdown */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-64 overflow-y-auto">
                      {suggestions.map((item, index) => (
                        <button
                          key={item.ticker}
                          onClick={() => selectSuggestion(item.ticker)}
                          onTouchEnd={() => selectSuggestion(item.ticker)}
                          onMouseEnter={() => setHighlightedIndex(index)}
                          className={`w-full px-4 py-3 text-left transition-colors flex items-center gap-3 ${
                            index === highlightedIndex
                              ? 'bg-slate-700 text-white'
                              : 'hover:bg-slate-700 text-slate-300'
                          }`}
                        >
                          <span className="font-mono font-bold text-cyan-400 min-w-[60px]">{item.ticker}</span>
                          <span className="text-sm truncate">{item.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {symbolWarning && (
                  <p className="text-amber-500 text-xs">{symbolWarning}</p>
                )}
              </div>

              {/* Period Select + Button Row */}
              <div className="flex flex-col sm:flex-row sm:items-end gap-3">
                {/* Period Select */}
                <div className="flex-1 space-y-2">
                  <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    Period
                  </label>
                  <select
                    ref={periodRef}
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="input-field appearance-none cursor-pointer"
                  >
                    <option value="short+">Short+</option>
                    <option value="short">Short</option>
                    <option value="medium">Medium</option>
                    <option value="long">Long</option>
                  </select>
                </div>

                {/* Submit/Stop Button */}
                <div className="flex-shrink-0">
                  {isAnalyzing ? (
                    <button
                      onClick={handleStop}
                      className="h-[52px] px-8 flex items-center justify-center gap-2 text-base font-semibold bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white rounded-xl shadow-lg transition-all duration-300"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12" rx="2"/>
                      </svg>
                      <span>Stop</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleSubmit}
                      disabled={loading || !symbolInput.trim()}
                      className="h-[52px] px-8 flex items-center justify-center gap-3 text-base font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white rounded-xl shadow-lg transition-all duration-300"
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
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Period Description */}
            <div className="pt-4 border-t border-slate-800/50">
              <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></span>
                  Short+: 1-7 days
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></span>
                  Short: 1-4 weeks
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></span>
                  Medium: 1-6 months
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></span>
                  Long: 6+ months
                </span>
              </div>
            </div>
          </div>
          </div>
        </section>

        {/* Log Section */}
        <section className="glass-panel rounded-2xl overflow-hidden border-l-4 border-l-cyan-500/50 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="bg-gradient-to-b from-slate-950 to-slate-900 p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-5">
              <h3 className="text-lg sm:text-xl font-semibold text-white flex items-center gap-2 sm:gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
                System Logs
              </h3>
              <div className="text-xs sm:text-sm font-mono text-slate-500 bg-slate-900/50 px-3 sm:px-4 py-1 sm:py-1.5 rounded-full">
                Real-time
              </div>
            </div>
            <div className="bg-black/40 rounded-xl p-3 sm:p-5 font-mono text-xs sm:text-sm text-slate-300 h-40 sm:h-48 overflow-y-auto scrollbar-hide border border-slate-800/50">
              <div className="whitespace-pre-wrap leading-relaxed">
                {log || <span className="text-slate-600 italic">// System ready. Enter a stock symbol and click Analyze to begin...</span>}
              </div>
              <div ref={logEndRef} />
            </div>
          </div>
        </section>

        {/* Results Grid */}
        {multiResults.length > 0 && (
          <div className="space-y-6 sm:space-y-10 animate-slide-up" style={{ animationDelay: '0.3s' }}>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-3 sm:gap-4">
                  <div className="w-3 sm:w-4 h-8 sm:h-10 bg-gradient-to-b from-purple-500 to-cyan-500 rounded-full"></div>
                  Analysis Report
                </h2>
                <p className="text-slate-500 text-base mt-2">
                  {multiResults.length} symbol(s) analyzed • Click headers to expand/collapse
                </p>
              </div>
            </div>

            {/* Symbol Sessions */}
            {multiResults.map((result, resultIndex) => (
              <div key={result.symbol} className="space-y-4">
                {/* Symbol Session Header */}
                <div className="glass-panel rounded-2xl p-6 border border-slate-800/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
                        <span className="text-2xl font-bold text-white">{result.symbol[0]}</span>
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white">{result.symbol}</h3>
                        <p className="text-slate-500 text-sm">
                          Session {resultIndex + 1} of {multiResults.length}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {result.timing && (
                        <div className="text-right text-sm text-slate-400">
                          <div>Duration: <span className="text-slate-300 font-mono">{result.timing.duration_minutes} min</span></div>
                          <div className="text-xs text-slate-500">{result.timing.start}</div>
                        </div>
                      )}
                      {result.reports?.trading && (
                        <a
                          href={`http://${serverHost}:${uvicornPort}${result.report_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-sm font-medium transition-all duration-300 border border-slate-700 hover:border-cyan-500/30"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                          View Report
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* Panels for this symbol */}
                {result.reports && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pl-4">
                    {panelKeys.map(({ key, label, icon, color }, index) => {
                      const panelId = `${result.symbol}-${key}`;
                      const isExpanded = isPanelExpanded(result.symbol, key);
                      return (
                        <div
                          key={panelId}
                          className={`glass-panel rounded-2xl overflow-hidden flex flex-col border border-slate-800/50 hover:border-slate-700/50 transition-all duration-500 hover:scale-[1.02]`}
                          style={{ animationDelay: `${(resultIndex * 7 + index) * 50}ms` }}
                        >
                          <button
                            onClick={() => togglePanel(result.symbol, key)}
                            className={`px-5 py-3 bg-gradient-to-r ${color} flex items-center justify-between cursor-pointer w-full text-left`}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-xl">{icon}</span>
                              <h4 className="font-bold text-white text-base">{label}</h4>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="text-white/80 text-xs font-mono bg-black/20 px-2 py-0.5 rounded-full">
                                {index + 1}/{panelKeys.length}
                              </div>
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="18"
                                height="18"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className={`text-white/80 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                              >
                                <polyline points="6 9 12 15 18 9"></polyline>
                              </svg>
                            </div>
                          </button>
                          {isExpanded && (
                            <div className={`p-5 text-slate-300 bg-gradient-to-b from-slate-950/50 to-slate-900/30 flex-1 markdown-content`}>
                              {result.reports[key] ? (
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={markdownComponents}
                                >
                                  {result.reports[key]}
                                </ReactMarkdown>
                              ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-600 italic text-sm py-12">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-4 opacity-50"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                                  No data available for this section
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Error state */}
                {result.error && (
                  <div className="glass-panel rounded-2xl p-6 border border-red-500/30 bg-red-500/10 ml-4">
                    <p className="text-red-400">Error analyzing {result.symbol}: {result.error}</p>
                  </div>
                )}

                {/* Divider between sessions */}
                {resultIndex < multiResults.length - 1 && (
                  <div className="border-t border-slate-800/50 my-6"></div>
                )}
              </div>
            ))}

            {/* Overall Timing Info */}
            {timing && multiResults.length > 1 && (
              <div className="glass-panel rounded-2xl p-6 border border-slate-800/50 animate-slide-up" style={{ animationDelay: '0.4s' }}>
                <h4 className="text-center text-slate-400 mb-4 font-medium">Batch Analysis Summary</h4>
                <div className="flex items-center justify-center gap-8 text-sm text-slate-400">
                  <div className="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span>Started: <span className="text-slate-300 font-mono">{timing.start}</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span>Ended: <span className="text-slate-300 font-mono">{timing.end}</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span>Total Duration: <span className="text-slate-300 font-mono">{timing.duration_minutes} min</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-purple-500">📊</span>
                    <span>Symbols: <span className="text-slate-300 font-mono">{multiResults.length}</span></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* History Reports Section */}
        <section className="glass-panel rounded-2xl p-6 border border-slate-800/50 animate-slide-up" style={{ animationDelay: '0.5s' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-white flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-500">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              History Reports
            </h3>
            <button
              onClick={fetchHistoryReports}
              className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
              </svg>
              Refresh
            </button>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedReport}
              onChange={(e) => setSelectedReport(e.target.value)}
              className="input-field flex-1 text-sm"
            >
              <option value="">-- Select a report --</option>
              {historyReports.map((report) => (
                <option key={report.filename} value={report.filename}>
                  {report.display}
                </option>
              ))}
            </select>
            <button
              onClick={viewReport}
              disabled={!selectedReport}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-all duration-300 flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              View Report
            </button>
          </div>
        </section>
      </main>

      <footer className="relative z-10 mt-auto py-6 sm:py-10 text-center text-slate-600 text-sm sm:text-base border-t border-slate-900/50">
        <div className="max-w-7xl mx-auto px-4">
          <p>© 2026 FinAgent. AI-Powered Financial Analysis Platform.</p>
          <p className="mt-2 sm:mt-3 text-xs sm:text-sm text-slate-700">All analysis is generated by AI and should be used for informational purposes only.</p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/introduction" element={<Introduction />} />
    </Routes>
  );
}

export default App;
