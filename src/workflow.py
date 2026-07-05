import os
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime
from .agents.analyst_agents import analyst_team
from .agents.global_economic_agent import get_global_economic_analysis
from .agents.fund_holding_agent import FundHoldingAnalyst
from .agents.researcher_agents import researcher_team
from .agents.trading_risk_agents import TradingAgent
from .utils.qdrant_utils import get_past_lessons
from .utils.data_fetchers import DataFetcher

fetcher = DataFetcher()

class AgentState(TypedDict):
    symbol: str
    investment_period: str
    analyst_insights: Dict[str, str]
    global_economic: str
    fund_holding: str
    researcher_results: Dict[str, str]
    trader_plan: str
    past_lessons: str
    timestamp: str

def analyst_node(state: AgentState) -> Dict[str, Any]:
    insights = analyst_team(state["symbol"], state["investment_period"])
    return {"analyst_insights": insights}

def global_economic_node(state: AgentState) -> Dict[str, Any]:
    global_economic = get_global_economic_analysis(state["investment_period"])
    return {"global_economic": global_economic}

def fund_holding_node(state: AgentState) -> Dict[str, Any]:
    fund_holding = FundHoldingAnalyst.analyze(state["symbol"])
    return {"fund_holding": fund_holding}

def researcher_node(state: AgentState) -> Dict[str, Any]:
    # Include global economic and fund_holding in the context for researcher
    global_economic_context = f"\n\nGLOBAL ECONOMIC DATA:\n{state.get('global_economic', 'No data')}"
    fund_holding_context = f"\n\nFUND HOLDING CHANGES:\n{state.get('fund_holding', 'No data')}"
    past_lessons_with_context = state["past_lessons"] + global_economic_context + fund_holding_context
    results = researcher_team(state["analyst_insights"], state["symbol"], state["investment_period"], past_lessons_with_context)
    return {"researcher_results": results}

def trading_node(state: AgentState) -> Dict[str, Any]:
    plan = TradingAgent.decide(state["symbol"], state["investment_period"], state["researcher_results"]["debate"])
    return {"trader_plan": plan}

def create_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("analyst", analyst_node)
    workflow.add_node("global_economic", global_economic_node)
    workflow.add_node("fund_holding", fund_holding_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("trading", trading_node)

    workflow.set_entry_point("analyst")
    workflow.add_edge("analyst", "global_economic")
    workflow.add_edge("global_economic", "fund_holding")
    workflow.add_edge("fund_holding", "researcher")
    workflow.add_edge("researcher", "trading")
    workflow.add_edge("trading", END)

    return workflow.compile()

def run_workflow(symbol: str, investment_period: str) -> AgentState:
    past_lessons_list = get_past_lessons(symbol)
    past_lessons = '\\n'.join(past_lessons_list)

    initial_state = {
        "symbol": symbol,
        "investment_period": investment_period,
        "past_lessons": past_lessons,
        "timestamp": datetime.now().isoformat(),
        "analyst_insights": {},
        "global_economic": "",
        "fund_holding": "",
        "researcher_results": {},
        "trader_plan": "",
    }

    app = create_workflow()
    final_state = app.invoke(initial_state)
    return final_state