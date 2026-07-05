import { Link } from 'react-router-dom'

function Introduction() {
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
            <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div>
                <h1 className="text-2xl bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
                  FinAgent
                </h1>
                <p className="text-xs text-slate-500 font-mono mt-1">Pipeline Introduction</p>
              </div>
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Title Section */}
        <section className="text-center space-y-6 animate-slide-up">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            FinAgent <span className="text-glow bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-cyan-500">Pipeline</span>
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto text-xl leading-relaxed">
            AI-Powered Financial Analysis Platform with Multi-Stock Parallel Processing
          </p>
        </section>

        {/* Key Features */}
        <section className="glass-panel rounded-2xl p-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="text-3xl">🚀</span> Key Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
              <h4 className="font-semibold text-cyan-400 mb-2">Parallel Processing</h4>
              <p className="text-slate-400 text-sm">Analyze 1-5 stocks simultaneously with ThreadPoolExecutor</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
              <h4 className="font-semibold text-purple-400 mb-2">Multi-Provider LLM</h4>
              <p className="text-slate-400 text-sm">ZenMux, Agnes AI, NVIDIA - auto-selected by URL</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
              <h4 className="font-semibold text-emerald-400 mb-2">10-Step Pipeline</h4>
              <p className="text-slate-400 text-sm">Comprehensive analysis from fundamentals to trading</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
              <h4 className="font-semibold text-amber-400 mb-2">Searchable Input</h4>
              <p className="text-slate-400 text-sm">Type company name to find tickers with autocomplete</p>
            </div>
          </div>
        </section>

        {/* Pipeline Diagram */}
        <section className="glass-panel rounded-2xl p-8 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="text-3xl">🔄</span> Analysis Pipeline
          </h3>

          <div className="space-y-4">
            {/* Phase 1 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h4 className="font-bold text-cyan-400 mb-4 text-lg">Phase 1: Data Collection (Steps 1-7) - PARALLEL</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StepCard number="1" name="Fundamentals" source="yfinance" color="blue" />
                <StepCard number="2" name="Sentiment & Social" source="yfinance + Reddit" color="emerald" />
                <StepCard number="3" name="Technical" source="yfinance" color="purple" />
                <StepCard number="4" name="Market Overview" source="yfinance" color="orange" />
                <StepCard number="5" name="Global Economy" source="World Bank API" color="cyan" />
                <StepCard number="6" name="Fund Holdings" source="LLM (agnes-2.0-flash)" color="teal" />
                <StepCard number="7" name="Past Lessons" source="Qdrant DB" color="yellow" />
              </div>
              <div className="mt-4 text-center text-slate-500 text-sm">
                ↓ Wait all steps complete ↓
              </div>
            </div>

            {/* Phase 2 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h4 className="font-bold text-purple-400 mb-4 text-lg">Phase 2: Analysis (Steps 8.1 & 8.2) - PARALLEL</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg p-4 border border-green-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🐂</span>
                    <span className="font-bold text-green-400">Step 8.1: Bull Analysis</span>
                  </div>
                  <p className="text-sm text-slate-400">Model: xiaomi/mimo-v2.5</p>
                  <p className="text-xs text-slate-500">Source: zenmux.ai</p>
                </div>
                <div className="bg-gradient-to-br from-red-500/20 to-rose-500/20 rounded-lg p-4 border border-red-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🐻</span>
                    <span className="font-bold text-red-400">Step 8.2: Bear Analysis</span>
                  </div>
                  <p className="text-sm text-slate-400">Model: claude-sonnet-5-free</p>
                  <p className="text-xs text-slate-500">Source: zenmux.ai</p>
                </div>
              </div>
              <div className="mt-4 text-center text-slate-500 text-sm">
                ↓ Wait both complete ↓
              </div>
            </div>

            {/* Phase 3 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h4 className="font-bold text-amber-400 mb-4 text-lg">Phase 3: Debate & Decision (Steps 8.3 & 9)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-lg p-4 border border-amber-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">⚖️</span>
                    <span className="font-bold text-amber-400">Step 8.3: Research Debate</span>
                  </div>
                  <p className="text-sm text-slate-400">Model: claude-fable-5-free</p>
                  <p className="text-xs text-slate-500">Source: zenmux.ai</p>
                  <p className="text-xs text-cyan-400 mt-1">+ Warren Buffett principles (long period)</p>
                </div>
                <div className="bg-gradient-to-br from-indigo-500/20 to-blue-500/20 rounded-lg p-4 border border-indigo-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🎯</span>
                    <span className="font-bold text-indigo-400">Step 9: Trading Plan</span>
                  </div>
                  <p className="text-sm text-slate-400">Model: claude-fable-5-free</p>
                  <p className="text-xs text-slate-500">Source: zenmux.ai</p>
                  <p className="text-xs text-emerald-400 mt-1">Output: BUY/SELL/HOLD, Target Price</p>
                </div>
              </div>
              <div className="mt-4 text-center text-slate-500 text-sm">
                ↓ Response returned to UI ↓
              </div>
            </div>

            {/* Phase 4 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h4 className="font-bold text-emerald-400 mb-4 text-lg">Phase 4: Lesson Summary (Step 10) - BACKGROUND</h4>
              <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-lg p-4 border border-emerald-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">📝</span>
                  <span className="font-bold text-emerald-400">Step 10: Lesson Summary</span>
                </div>
                <p className="text-sm text-slate-400">Model: agnes-2.0-flash</p>
                <p className="text-xs text-slate-500">Source: agnes-ai.com</p>
                <p className="text-xs text-purple-400 mt-1">Stores lesson in Qdrant DB for future reference</p>
              </div>
            </div>
          </div>
        </section>

        {/* LLM Configuration */}
        <section className="glass-panel rounded-2xl p-8 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="text-3xl">🤖</span> LLM Configuration
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-slate-400">Step</th>
                  <th className="text-left py-3 px-4 text-slate-400">Model</th>
                  <th className="text-left py-3 px-4 text-slate-400">Provider</th>
                  <th className="text-left py-3 px-4 text-slate-400">URL</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-slate-300">6. Fund Holdings</td>
                  <td className="py-3 px-4 text-cyan-400">agnes-2.0-flash</td>
                  <td className="py-3 px-4 text-slate-400">Agnes AI</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">apihub.agnes-ai.com</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-slate-300">8.1 Bull Analysis</td>
                  <td className="py-3 px-4 text-green-400">xiaomi/mimo-v2.5</td>
                  <td className="py-3 px-4 text-slate-400">ZenMux</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">zenmux.ai</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-slate-300">8.2 Bear Analysis</td>
                  <td className="py-3 px-4 text-red-400">claude-sonnet-5-free</td>
                  <td className="py-3 px-4 text-slate-400">ZenMux</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">zenmux.ai</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-slate-300">8.3 Research Debate</td>
                  <td className="py-3 px-4 text-amber-400">claude-fable-5-free</td>
                  <td className="py-3 px-4 text-slate-400">ZenMux</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">zenmux.ai</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-slate-300">9. Trading Plan</td>
                  <td className="py-3 px-4 text-indigo-400">claude-fable-5-free</td>
                  <td className="py-3 px-4 text-slate-400">ZenMux</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">zenmux.ai</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-300">10. Lesson Summary</td>
                  <td className="py-3 px-4 text-emerald-400">agnes-2.0-flash</td>
                  <td className="py-3 px-4 text-slate-400">Agnes AI</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">apihub.agnes-ai.com</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400">
              <span className="font-semibold text-slate-300">API Key Routing:</span>{' '}
              <span className="text-cyan-400">zenmux*</span> → ZENMUX_API_KEY |{' '}
              <span className="text-purple-400">agnes-ai*</span> → AGNES_API_KEY |{' '}
              <span className="text-green-400">nvidia*</span> → NVIDIA_API_KEY
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center py-8 text-slate-600 text-sm">
          <p>© 2026 FinAgent. AI-Powered Financial Analysis Platform.</p>
        </footer>
      </main>
    </div>
  )
}

function StepCard({ number, name, source, color }) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    emerald: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30',
    purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
    orange: 'from-orange-500/20 to-red-500/20 border-orange-500/30',
    cyan: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30',
    teal: 'from-teal-500/20 to-cyan-500/20 border-teal-500/30',
    yellow: 'from-yellow-500/20 to-amber-500/20 border-yellow-500/30',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-lg p-3 border`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400">{number}</span>
        <span className="font-medium text-white text-sm">{name}</span>
      </div>
      <p className="text-xs text-slate-500">{source}</p>
    </div>
  )
}

export default Introduction
