import { useState, useEffect, useRef, useMemo, useCallback, lazy, Suspense } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Lazy load Introduction component
const Introduction = lazy(() => import('./Introduction.jsx'))

// Constants - defined outside component to avoid recreation on every render
const PANEL_KEYS = [
  { key: 'fundamentals', label: 'Fundamentals', icon: '📊', color: 'from-slate-700 to-slate-600' },
  { key: 'sentiment', label: 'Sentiment & Social', icon: '💬', color: 'from-slate-700 to-slate-600' },
  { key: 'technical', label: 'Technical', icon: '📈', color: 'from-slate-700 to-slate-600' },
  { key: 'market', label: 'Market Overview', icon: '🌍', color: 'from-slate-700 to-slate-600' },
  { key: 'globalEconomic', label: 'Global Economy', icon: '🌐', color: 'from-slate-700 to-slate-600' },
  { key: 'fundHolding', label: 'Fund Holdings', icon: '🏦', color: 'from-slate-700 to-slate-600' },
  { key: 'pastLessons', label: 'Past Lessons', icon: '📚', color: 'from-slate-700 to-slate-600' },
  { key: 'research', label: 'Research Debate', icon: '🧠', color: 'from-slate-700 to-slate-600' },
  { key: 'quant', label: 'Quant Signals', icon: '📐', color: 'from-slate-700 to-cyan-600' },
  { key: 'trading', label: 'Trading Plan', icon: '🎯', color: 'from-slate-600 to-cyan-600' },
];

const MARKDOWN_COMPONENTS = {
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

// Pre-compute default dates (only once)
const DEFAULT_START_DATE = (() => {
  const d = new Date();
  d.setDate(d.getDate() - 10);
  return d.toISOString().split('T')[0];
})();
const DEFAULT_END_DATE = new Date().toISOString().split('T')[0];

function HomePage({ onLogout }) {
  // Use current browser protocol/host/port for API calls
  const protocol = window.location.protocol; // http: or https:
  const serverHost = window.location.hostname;
  const serverPort = window.location.port || (protocol === 'https:' ? '443' : '8000');
  const apiUrl = `${protocol}//${serverHost}${serverPort !== '443' && serverPort !== '80' ? ':' + serverPort : ''}`;

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
  const [historyReports, setHistoryReports] = useState([]);
  const justSelectedRef = useRef(false);
  const [selectedReport, setSelectedReport] = useState('');
  const [viewingHistory, setViewingHistory] = useState(false);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState(DEFAULT_END_DATE);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const abortControllerRef = useRef(null);
  const isSubmittingRef = useRef(false);
  const logEndRef = useRef(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const periodRef = useRef(null);

  // Load ticker mapping on mount
  useEffect(() => {
    fetch(`${apiUrl}/public/ticket_mapping.json`)
      .then(res => res.json())
      .then(data => setTickerMapping(data))
      .catch(err => console.error('Failed to load ticker mapping:', err));
  }, [serverHost, apiUrl]);

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
    if (justSelectedRef.current) {
      justSelectedRef.current = false;
      setSuggestions([]);
      setShowSuggestions(false);
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
  }, [symbolInput, tickerMapping]);

  const selectSuggestion = useCallback((ticker) => {
    setSymbolInput(prev => {
      const parts = prev.split(/[,;]/);
      parts[parts.length - 1] = ticker;
      return parts.join(',');
    });
    justSelectedRef.current = true;
    setShowSuggestions(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback((e) => {
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
  }, [symbolInput, period, showSuggestions, suggestions, highlightedIndex, selectSuggestion]);

  const togglePanel = useCallback((symbol, key) => {
    const panelId = `${symbol}-${key}`;
    setExpandedPanels(prev => ({ ...prev, [panelId]: !prev[panelId] }));
  }, []);

  const isPanelExpanded = useCallback((symbol, key) => {
    // Trading panel (step 7) is expanded by default
    if (key === 'trading') return expandedPanels[`${symbol}-${key}`] !== false;
    return expandedPanels[`${symbol}-${key}`] === true;
  }, [expandedPanels]);

  // Scroll to top on page load/refresh
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Show/hide scroll to top button based on scroll position (throttled)
  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setShowScrollTop(window.scrollY > 300);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Auto-scroll log (only when there's content)
  useEffect(() => {
    if (log && log.length > 10) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [log]);

  const validateTicker = useCallback((ticker) => {
    if (!ticker || ticker.length === 0) return false;
    return tickerMapping.some(item => item.ticker === ticker.toUpperCase());
  }, [tickerMapping]);

  const handleStop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsAnalyzing(false);
    setLoading(false);
    setLog(prev => prev + `\n⏹️ Analysis stopped by user.\n`);
  }, []);

  const fetchHistoryReports = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/history-reports`);
      if (response.ok) {
        const data = await response.json();
        setHistoryReports(data.reports || []);
      }
    } catch (err) {
      console.error('Failed to fetch history reports:', err);
    }
  }, [serverHost, apiUrl]);

  const viewReport = useCallback(() => {
    if (selectedReport) {
      window.open(`${apiUrl}/static/${selectedReport}`, '_blank');
    }
  }, [selectedReport, serverHost, apiUrl]);

  // Load history reports on mount
  useEffect(() => {
    fetchHistoryReports();
  }, []);

  // Filter reports by date range
  const filteredReports = useMemo(() => {
    return historyReports.filter((report) => {
      if (!report.date || report.date === 'Unknown') return false;
      if (startDate && report.date < startDate) return false;
      if (endDate && report.date > endDate) return false;
      return true;
    });
  }, [historyReports, startDate, endDate]);

  const handleSubmit = useCallback(async () => {
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

    // Create new AbortController for this request with 10-minute timeout
    abortControllerRef.current = new AbortController();
    const fetchTimeout = setTimeout(() => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    }, 600000); // 10 minutes

    try {
      // Start analysis job (returns immediately with job_id)
      const startResponse = await fetch(`${apiUrl}/analyze-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols, period }),
      });

      if (!startResponse.ok) {
        throw new Error(`API error: ${startResponse.status}`);
      }

      const { job_id } = await startResponse.json();
      setLog(prev => prev + `\n⏳ Job started. Polling for results...\n`);

      // Poll for results every 5 seconds
      const pollInterval = 5000;
      const maxPolls = 120; // 10 minutes max
      let polls = 0;

      while (polls < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        polls++;

        // Check if cancelled
        if (abortControllerRef.current?.signal?.aborted) {
          setLog(prev => prev + `\n⏹️ Analysis cancelled by user.\n`);
          return;
        }

        try {
          // Add cache-busting timestamp to prevent mobile browser caching
          const statusResponse = await fetch(`${apiUrl}/analyze-status/${job_id}?t=${Date.now()}`, {
            cache: 'no-store',
          });
          if (!statusResponse.ok) continue;

          const statusData = await statusResponse.json();

          if (statusData.status === 'completed') {
            // Process results
            const data = { results: statusData.results };
            setMultiResults(data.results);
            if (data.results.length > 0 && data.results[0].timing) {
              setTiming(data.results[0].timing);
            }

            // Log step completion
            let stepLog = '';
            data.results.forEach(result => {
              if (result.step_logs && result.step_logs.length > 0) {
                result.step_logs.forEach(log => { stepLog += `${log}\n`; });
              }
            });
            if (stepLog) setLog(prev => prev + `\n📊 Step Progress:\n${stepLog}`);

            // Log errors
            let errorLog = '';
            data.results.forEach(result => {
              if (result.errors && result.errors.length > 0) {
                errorLog += `\n📋 ${result.symbol}:\n`;
                result.errors.forEach(err => { errorLog += `  ${err}\n`; });
              }
            });
            if (errorLog) setLog(prev => prev + `\n⚠️ Pipeline Warnings:${errorLog}`);

            // Log cost summary
            let totalCost = 0, totalInputTokens = 0, totalOutputTokens = 0, costByModel = {};
            data.results.forEach(result => {
              if (result.cost_summary) {
                totalCost += result.cost_summary.total_cost || 0;
                totalInputTokens += result.cost_summary.total_input_tokens || 0;
                totalOutputTokens += result.cost_summary.total_output_tokens || 0;
                if (result.cost_summary.by_model) {
                  Object.entries(result.cost_summary.by_model).forEach(([model, info]) => {
                    if (!costByModel[model]) costByModel[model] = { input: 0, output: 0, cost: 0 };
                    costByModel[model].input += info.input_tokens || 0;
                    costByModel[model].output += info.output_tokens || 0;
                    costByModel[model].cost += info.cost || 0;
                  });
                }
              }
            });
            if (totalCost > 0 || totalInputTokens > 0) {
              let costLog = `\n💰 LLM Cost Summary:\n`;
              costLog += `   Total: HK$${totalCost.toFixed(1)} (${totalInputTokens.toLocaleString()} input, ${totalOutputTokens.toLocaleString()} output tokens)\n`;
              Object.entries(costByModel).forEach(([model, info]) => {
                costLog += `   ${model}: HK$${info.cost.toFixed(1)} (${info.input.toLocaleString()} in / ${info.output.toLocaleString()} out)\n`;
              });
              setLog(prev => prev + costLog);
            }

            setLog(prev => prev + `\n✅ Analysis complete for ${data.results.length} symbol(s).\n`);
            return;
          } else if (statusData.status === 'failed') {
            setLog(prev => prev + `\n❌ Analysis failed: ${statusData.error}\n`);
            return;
          }
          // else status is "running", continue polling
        } catch (pollErr) {
          // Poll request failed, continue trying
          console.error('Poll error:', pollErr);
        }
      }

      setLog(prev => prev + `\n⏱️ Polling timed out. The server may still be processing.\n`);
    } catch (err) {
      if (err.name === 'AbortError') {
        setLog(prev => prev + `\n⏹️ Analysis cancelled by user.\n`);
      } else if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
        setLog(prev => prev + `\n❌ Connection failed: Server may be down or crashed.\n`);
        setLog(prev => prev + `   URL: ${apiUrl}/analyze-batch\n`);
      } else {
        setLog(prev => prev + `\n❌ Error: ${err.message}\n`);
      }
    } finally {
      clearTimeout(fetchTimeout);
      setLoading(false);
      setIsAnalyzing(false);
      isSubmittingRef.current = false;
      abortControllerRef.current = null;
    }
  }, [loading, isAnalyzing, symbolInput, period, validateTicker, serverHost, apiUrl]);

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
              {/* Profile & Logout */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 bg-slate-900/50 rounded-lg border border-slate-800">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <span className="text-[10px] sm:text-xs font-mono text-slate-400 hidden sm:inline">carina666</span>
                </div>
                <button
                  onClick={onLogout}
                  className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 bg-slate-900/50 rounded-lg border border-slate-800 hover:border-red-500/50 hover:bg-slate-800/50 transition-all duration-300 cursor-pointer"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-400">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                  <span className="text-[10px] sm:text-xs font-mono text-slate-400 hidden sm:inline">Logout</span>
                </button>
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
                      // Only show suggestions if not just selected and there are suggestions
                      if (!justSelectedRef.current && suggestions.length > 0) {
                        setShowSuggestions(true);
                      }
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
              <div key={result.symbol} className="space-y-3">
                {/* Symbol Session Header */}
                <div className="glass-panel rounded-xl p-3 sm:p-4 border border-slate-800/50">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                        <span className="text-base sm:text-lg font-bold text-white">{result.symbol[0]}</span>
                      </div>
                      <div>
                        <h3 className="text-lg sm:text-xl font-bold text-white">{result.symbol}</h3>
                        <p className="text-slate-500 text-[10px] sm:text-xs">
                          {resultIndex + 1}/{multiResults.length}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 sm:gap-3">
                      {result.timing && (
                        <div className="text-right text-[10px] sm:text-xs text-slate-400">
                          <span className="font-mono">{result.timing.duration_minutes}m</span>
                        </div>
                      )}
                      {result.reports?.trading && (
                        <a
                          href={`${apiUrl}${result.report_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 sm:px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-[10px] sm:text-xs font-medium transition-all duration-300 border border-slate-700 hover:border-cyan-500/30"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                          Report
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* Panels for this symbol */}
                {result.reports && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 pl-0 sm:pl-4">
                    {PANEL_KEYS.map(({ key, label, icon, color }, index) => {
                      const panelId = `${result.symbol}-${key}`;
                      const isExpanded = isPanelExpanded(result.symbol, key);
                      return (
                        <div
                          key={panelId}
                          className={`glass-panel rounded-xl overflow-hidden flex flex-col border border-slate-800/50 hover:border-slate-700/50 transition-all duration-300`}
                          style={{ animationDelay: `${(resultIndex * 7 + index) * 50}ms` }}
                        >
                          <button
                            onClick={() => togglePanel(result.symbol, key)}
                            className={`px-3 py-2 sm:py-2.5 bg-gradient-to-r ${color} flex items-center justify-between cursor-pointer w-full text-left`}
                          >
                            <div className="flex items-center gap-1.5 sm:gap-2">
                              <span className="text-sm sm:text-base">{icon}</span>
                              <h4 className="font-bold text-white text-[11px] sm:text-xs">{label}</h4>
                            </div>
                            <div className="flex items-center gap-1">
                              <div className="text-white/80 text-[9px] font-mono bg-black/20 px-1 py-0.5 rounded">
                                {index + 1}/{PANEL_KEYS.length}
                              </div>
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="14"
                                height="14"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className={`text-white/80 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                              >
                                <polyline points="6 9 12 15 18 9"></polyline>
                              </svg>
                            </div>
                          </button>
                          {isExpanded && (
                            <div className={`p-4 sm:p-5 text-slate-300 bg-gradient-to-b from-slate-950/50 to-slate-900/30 flex-1 markdown-content`}>
                              {result.reports[key] ? (
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={MARKDOWN_COMPONENTS}
                                >
                                  {result.reports[key]}
                                </ReactMarkdown>
                              ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-600 italic text-xs sm:text-sm py-8 sm:py-12">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-3 sm:mb-4 opacity-50"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                                  No data available
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
          {/* Date Range Filter */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400 whitespace-nowrap">From</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="input-field text-sm px-3 py-1.5"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400 whitespace-nowrap">To</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="input-field text-sm px-3 py-1.5"
              />
            </div>
            <span className="text-xs text-slate-500 whitespace-nowrap">
              {filteredReports.length} report{filteredReports.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedReport}
              onChange={(e) => setSelectedReport(e.target.value)}
              className="input-field flex-1 text-sm"
            >
              <option value="">-- Select a report --</option>
              {filteredReports.map((report) => (
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

      {/* Floating Go To Top Button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-50 w-12 h-12 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white rounded-full shadow-lg shadow-purple-900/50 flex items-center justify-center transition-all duration-300 hover:scale-110 animate-fade-in"
          aria-label="Go to top"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="18 15 12 9 6 15"></polyline>
          </svg>
        </button>
      )}

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
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [checkingSession, setCheckingSession] = useState(true)

  // Check session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        const protocol = window.location.protocol
        const host = window.location.hostname
        const port = window.location.port || (protocol === 'https:' ? '443' : '8000')
        const apiUrl = `${protocol}//${host}${port !== '443' && port !== '80' ? ':' + port : ''}`

        const response = await fetch(`${apiUrl}/api/session`)
        if (response.ok) {
          setIsLoggedIn(true)
        }
      } catch (err) {
        // Not logged in
      } finally {
        setCheckingSession(false)
      }
    }
    checkSession()
  }, [])

  const handleLogin = (username) => {
    setIsLoggedIn(true)
  }

  const handleLogout = async () => {
    try {
      const protocol = window.location.protocol
      const host = window.location.hostname
      const port = window.location.port || (protocol === 'https:' ? '443' : '8000')
      const apiUrl = `${protocol}//${host}${port !== '443' && port !== '80' ? ':' + port : ''}`

      await fetch(`${apiUrl}/api/logout`, { method: 'POST' })
    } catch (err) {
      // Ignore error
    }
    setIsLoggedIn(false)
  }

  if (checkingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isLoggedIn) {
    const LoginPage = lazy(() => import('./LoginPage.jsx'))
    return (
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">Loading...</p>
          </div>
        </div>
      }>
        <LoginPage onLogin={handleLogin} />
      </Suspense>
    )
  }

  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    }>
      <Routes>
        <Route path="/" element={<HomePage onLogout={handleLogout} />} />
        <Route path="/introduction" element={<Introduction />} />
      </Routes>
    </Suspense>
  );
}

export default App;
