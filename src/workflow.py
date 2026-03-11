from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime
from .agents.analyst_agents import analyst_team
from .agents.researcher_agents import researcher_team
from .agents.trading_risk_agents import TradingAgent, RiskManagementAgent
from .utils.qdrant_utils import get_past_lessons
from .utils.data_fetchers import DataFetcher
from .agents.analyst_agents import llm  # for lesson

fetcher = DataFetcher()

class AgentState(TypedDict):
    symbol: str
    investment_period: str
    analyst_insights: Dict[str, str]
    researcher_results: Dict[str, str]
    trader_plan: str
    risk_plan: str
    past_lessons: str
    timestamp: str

def analyst_node(state: AgentState) -> Dict[str, Any]:
    insights = analyst_team(state["symbol"], state["investment_period"])
    return {"analyst_insights": insights}

def researcher_node(state: AgentState) -> Dict[str, Any]:
    results = researcher_team(state["analyst_insights"], state["symbol"], state["past_lessons"])
    return {"researcher_results": results}

def trading_node(state: AgentState) -> Dict[str, Any]:
    plan = TradingAgent.decide(state["symbol"], state["investment_period"], state["researcher_results"]["debate"], state["past_lessons"])
    return {"trader_plan": plan}

def risk_node(state: AgentState) -> Dict[str, Any]:
    plan = RiskManagementAgent.evaluate(state["symbol"], state["investment_period"], state["analyst_insights"], state["researcher_results"], state["trader_plan"], state["past_lessons"])
    return {"risk_plan": plan}

def create_workflow():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("trading", trading_node)
    workflow.add_node("risk", risk_node)
    
    workflow.set_entry_point("analyst")
    workflow.add_edge("analyst", "researcher")
    workflow.add_edge("researcher", "trading")
    workflow.add_edge("trading", "risk")
    workflow.add_edge("risk", END)
    
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
        "researcher_results": {},
        "trader_plan": "",
        "risk_plan": "",
    }
    
    app = create_workflow()
    final_state = app.invoke(initial_state)
    return final_state