import os
from datetime import datetime
from src.workflow import run_workflow
from src.utils.qdrant_utils import store_entry

def main(symbol: str, period: str):
    state = run_workflow(symbol, period)
    
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    result_file = f'results/result_{timestamp}.md'
    timestampInReport = datetime.now().strftime('%Y-%m-%d %H:%M')

    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"# <span style='color: #cfa923;'>FinAgent Analysis Report</span> \\n")
        f.write(f"Symbol: {symbol}, ")
        f.write(f"Period: {period}, ")
        f.write(f"Timestamp: {timestampInReport}\\n\\n")
        f.write("## <span style='color: #cfa923;'>1. Analyst Insights</span> \\n")
        for key, value in state['analyst_insights'].items():
            f.write(f"### <span style='color: #326ba8;'>{key.title()}</span>\\n")
            f.write(f"<hr style='height: 1px; background-color: #ccc; opacity: 0.5;' />\\n")
            f.write(f"{value}\\n\\n")
        f.write("## <span style='color: #cfa923;'>2. Researcher Debate</span>\\n")
        for key, value in state['researcher_results'].items():
            f.write(f"### <span style='color: #326ba8;'>{key.title()}</span>\\n")
            f.write(f"<hr style='height: 1px; background-color: #ccc; opacity: 0.5;' />\\n")
            f.write(f"{value}\\n\\n")
        f.write("## <span style='color: #cfa923;'>3. Trading Plan</span>\\n")
        f.write(f"{state['trader_plan']}\\n\\n")
        f.write("## <span style='color: #cfa923;'>4. Risk Management</span>\\n")
        f.write(f"{state['risk_plan']}")
    
    store_entry(
        symbol, 
        'report', 
        state['risk_plan'], 
        state['timestamp'], 
        {
            'period': period,
            'analyst_insights': state['analyst_insights'],
            'researcher_results': state['researcher_results'],
            'trader_plan': state['trader_plan'],
            'risk_plan': state['risk_plan']
        }
    )
    return state, result_file