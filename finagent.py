import os
from datetime import datetime
from dotenv import load_dotenv
from src.workflow_parallel import run_single_ticket_pipeline
from src.utils.qdrant_utils import store_entry

load_dotenv(os.path.join('config', '.env'))
RUN_MODE = os.getenv("RUN_MODE", "local")

def main(symbol: str, period: str):
    """Run analysis pipeline for a single symbol."""
    result = run_single_ticket_pipeline(symbol, period)

    # Convert result to state format for compatibility
    state = {
        'analyst_insights': {
            'fundamentals': result['steps'].get('fundamentals', ''),
            'sentiment': result['steps'].get('sentiment', ''),
            'technical': result['steps'].get('technical', ''),
            'market': result['steps'].get('market', ''),
        },
        'researcher_results': {
            'bull': result['steps'].get('bull', ''),
            'bear': result['steps'].get('bear', ''),
            'debate': result['steps'].get('debate', ''),
        },
        'trader_plan': result['steps'].get('trading', ''),
        'risk_plan': '',
        'timestamp': result.get('start_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    }

    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    result_file = f'results/result_{symbol}_{timestamp}.md'
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

    # Store lesson in Qdrant
    try:
        store_entry(
            symbol,
            'report',
            state['trader_plan'],
            state['timestamp'],
            {
                'period': period,
                'analyst_insights': state['analyst_insights'],
                'researcher_results': state['researcher_results'],
                'trader_plan': state['trader_plan']
            }
        )
    except Exception as e:
        print(f"Warning: Could not store lesson in Qdrant: {e}")

    return state, result_file