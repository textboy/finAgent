import { useEffect, useRef } from 'react';

function LogComponent({ log }) {
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log]);

  return (
    <div className="bg-black/40 rounded-xl p-4 font-mono text-sm text-slate-300 h-40 overflow-y-auto scrollbar-hide border border-slate-800/50">
      <div className="whitespace-pre-wrap leading-relaxed">
        {log || <span className="text-slate-600 italic">// System ready. Enter a stock symbol and click Analyze to begin...</span>}
      </div>
      <div ref={logEndRef} />
    </div>
  );
}

export default LogComponent;