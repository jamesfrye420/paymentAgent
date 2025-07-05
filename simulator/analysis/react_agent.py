import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from langgraph.graph import StateGraph, END
from langgraph.graph import MessageGraph
from langchain_aws import ChatBedrock
from langchain.tools import BaseTool
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from log_analyzer import PaymentLogsProcessor, PatternAnalysisResult
from config_agent import AgentConfig
from pydantic import BaseModel, Field
import sys


class ActionDecision(BaseModel):
    """Structured output for agent decisions"""

    tool_name: str = Field(
        description="Name of the tool to use: log_analyzer, failure_analyzer, or provider_health"
    )

    reasoning: str = Field(description="Why this tool was chosen")

    parameters: Dict[str, Any] = Field(description="Parameters for the tool")

    continue_analysis: bool = Field(
        description="Whether more analysis is needed after this action"
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """State for the ReAct agent"""

    user_query: str
    thoughts: List[str]
    actions_taken: List[Dict[str, Any]]
    observations: List[str]
    final_answer: Optional[str] = None
    file_path: Optional[str] = AgentConfig.DEFAULT_LOG_FILE
    analysis_results: Optional[Dict[str, PatternAnalysisResult]] = None


class LogAnalyzerTool(BaseTool):
    """Tool for analyzing payment logs"""

    name: str = "log_analyzer"
    description: str = (
        "Analyze payment logs to identify failure patterns, provider performance, fraud indicators, and temporal patterns"
    )

    def _run(self, file_path: str, analysis_type: str = "comprehensive") -> str:
        processor = PaymentLogsProcessor()
        """Run log analysis"""
        try:
            if analysis_type == "comprehensive":
                results = processor.run_comprehensive_analysis(file_path)
                return json.dumps(
                    {
                        "status": "success",
                        "analysis_count": len(results),
                        "analyses": {
                            k: {
                                "confidence": v.confidence,
                                "risk_score": v.risk_score,
                                "description": v.description,
                                "recommendations": v.recommendations,
                            }
                            for k, v in results.items()
                        },
                    },
                    indent=2,
                )
            else:
                # Single analysis
                processor.process_data(file_path)
                if analysis_type == "failure_patterns":
                    result = processor.extract_failure_patterns()
                elif analysis_type == "provider_performance":
                    result = processor.analyze_provider_performance()
                elif analysis_type == "fraud_detection":
                    result = processor.detect_fraud_patterns()
                elif analysis_type == "temporal_patterns":
                    result = processor.analyze_temporal_patterns()
                else:
                    return json.dumps(
                        {"status": "error", "message": "Unknown analysis type"}
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "pattern_type": result.pattern_type,
                        "confidence": result.confidence,
                        "risk_score": result.risk_score,
                        "description": result.description,
                        "recommendations": result.recommendations,
                        "metrics": result.metrics,
                    },
                    indent=2,
                    default=str,
                )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


class FailureAnalyzerTool(BaseTool):
    """Tool for deep failure analysis"""

    name: str = "failure_analyzer"
    description: str = "Analyze specific failure patterns and categorize root causes"

    def _run(
        self, file_path: str, provider: str = None, failure_reason: str = None
    ) -> str:
        processor = PaymentLogsProcessor()
        """Analyze failures with specific filters"""
        try:
            processor.process_data(file_path)
            failed_transactions = [t for t in processor.transactions if not t.success]

            # Apply filters
            if provider:
                failed_transactions = [
                    t for t in failed_transactions if t.provider == provider
                ]
            if failure_reason:
                failed_transactions = [
                    t
                    for t in failed_transactions
                    if failure_reason.lower() in (t.failure_reason or "").lower()
                ]

            # Categorize failures
            categories = {}
            for t in failed_transactions:
                reason = t.failure_reason or "UNKNOWN"
                if reason not in categories:
                    categories[reason] = []
                categories[reason].append(
                    {
                        "transaction_id": t.transaction_id,
                        "provider": t.provider,
                        "amount": t.amount,
                        "currency": t.currency,
                        "timestamp": t.timestamp.isoformat(),
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "total_failures": len(failed_transactions),
                    "failure_categories": {
                        k: {"count": len(v), "examples": v[:3]}
                        for k, v in categories.items()
                    },
                    "top_failure_reason": (
                        max(categories.items(), key=lambda x: len(x[1]))[0]
                        if categories
                        else None
                    ),
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


class ProviderHealthTool(BaseTool):
    """Tool for checking provider health"""

    name: str = "provider_health"
    description: str = "Check provider health metrics and circuit breaker states"

    def _run(self, file_path: str, provider: str = None) -> str:
        processor = PaymentLogsProcessor()
        """Check provider health"""
        try:
            processor.process_data(file_path)
            providers_health = {}

            for t in processor.transactions:
                if provider and t.provider != provider:
                    continue

                if t.provider not in providers_health:
                    providers_health[t.provider] = {
                        "total": 0,
                        "success": 0,
                        "failed": 0,
                        "circuit_breaker_open": 0,
                        "health_scores": [],
                    }

                providers_health[t.provider]["total"] += 1
                if t.success:
                    providers_health[t.provider]["success"] += 1
                else:
                    providers_health[t.provider]["failed"] += 1

                if t.circuit_breaker_state == "OPEN":
                    providers_health[t.provider]["circuit_breaker_open"] += 1

                if t.provider_health:
                    providers_health[t.provider]["health_scores"].append(
                        t.provider_health
                    )

            # Calculate metrics
            for p, data in providers_health.items():
                data["success_rate"] = (
                    data["success"] / data["total"] if data["total"] > 0 else 0
                )
                data["avg_health_score"] = (
                    sum(data["health_scores"]) / len(data["health_scores"])
                    if data["health_scores"]
                    else 0
                )
                data["circuit_breaker_issues"] = data["circuit_breaker_open"] > 0

            return json.dumps(
                {
                    "status": "success",
                    "provider_health": providers_health,
                    "recommendations": self._generate_health_recommendations(
                        providers_health
                    ),
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _generate_health_recommendations(self, providers_health: Dict) -> List[str]:
        recommendations = []
        for provider, data in providers_health.items():
            if data["success_rate"] < 0.8:
                recommendations.append(
                    f"Provider {provider} has low success rate ({data['success_rate']:.2%})"
                )
            if data["circuit_breaker_issues"]:
                recommendations.append(
                    f"Provider {provider} has circuit breaker issues"
                )
            if data["avg_health_score"] < 0.7:
                recommendations.append(
                    f"Provider {provider} has low health score ({data['avg_health_score']:.2f})"
                )
        return recommendations


class RootCauseReActAgent:
    """ReAct agent for root cause analysis"""

    def __init__(self, aws_region: str = AgentConfig.AWS_REGION):
        # Initialize Bedrock client
        self.bedrock_client = AgentConfig.session.client(
            "bedrock-runtime", region_name=aws_region
        )

        # Initialize LLM
        self.llm = ChatBedrock(
            client=self.bedrock_client,
            model_id=AgentConfig.BEDROCK_MODEL_ID,
            provider="anthropic",
            model_kwargs={"temperature": 0.1},
        )

        # Initialize tools
        self.tools = {
            "log_analyzer": LogAnalyzerTool(),
            "failure_analyzer": FailureAnalyzerTool(),
            "provider_health": ProviderHealthTool(),
        }

        # Create graph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the ReAct agent graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("conclude", self._conclude_node)

        # Add edges
        workflow.set_entry_point("think")
        workflow.add_edge("think", "act")
        workflow.add_edge("act", "observe")
        workflow.add_conditional_edges(
            "observe",
            self._should_continue,
            {"continue": "think", "conclude": "conclude"},
        )
        workflow.add_edge("conclude", END)

        return workflow.compile()

    def _think_node(self, state: AgentState) -> AgentState:
        """Reasoning node - decide what to do next"""
        structured_llm = self.llm.with_structured_output(ActionDecision)
        system_prompt = """You are a payment system expert analyzing transaction logs for root cause analysis.

Available tools and their purposes:
1. log_analyzer: Comprehensive analysis (failure_patterns, provider_performance, fraud_detection, temporal_patterns)
   - Use when: Need overall analysis or specific pattern analysis
   - Params: file_path (required), analysis_type (optional: "comprehensive", "failure_patterns", "provider_performance", "fraud_detection", "temporal_patterns")

2. failure_analyzer: Deep dive into specific failures  
   - Use when: Need to focus on specific provider failures or failure reasons
   - Params: file_path (required), provider (optional), failure_reason (optional)

3. provider_health: Check provider health and circuit breaker states
   - Use when: Need to assess provider performance and health metrics
   - Params: file_path (required), provider (optional)

Current query: "{query}"
Previous actions: {actions}
Previous observations: {observations}
file_path: {file_path}

Choose the most appropriate tool and parameters to answer the user's query. Always include file_path parameter.
"""

        prompt = system_prompt.format(
            query=state.user_query,
            actions=[a.get("tool", "none") for a in state.actions_taken],
            observations=[
                obs[:100] + "..." if len(obs) > 100 else obs
                for obs in state.observations
            ],
            file_path=(
                sys.argv[1] if len(sys.argv) > 1 else AgentConfig.DEFAULT_LOG_FILE
            ),
        )
        try:

            decision = structured_llm.invoke([HumanMessage(content=prompt)])

            # Ensure file_path is always included

            if "file_path" not in decision.parameters:

                decision.parameters["file_path"] = (
                    state.file_path or AgentConfig.DEFAULT_LOG_FILE
                )

            # Store the structured decision

            state.thoughts.append(f"REASONING: {decision.reasoning}")

            state.thoughts.append(
                f"ACTION: {decision.tool_name} PARAMS: {decision.parameters}"
            )

        except Exception as e:

            logger.error(f"Error in structured decision: {e}")

            # Fallback to simple decision

            state.thoughts.append("REASONING: Using fallback analysis")

            state.thoughts.append(
                f"ACTION: log_analyzer PARAMS: {{'file_path': '{state.file_path}'}}"
            )

    def _act_node(self, state: AgentState) -> AgentState:
        """Action node - execute the chosen tool"""
        if not state.thoughts:
            return state

        latest_thought = state.thoughts[-1]

        # Parse action from thought
        action_info = self._parse_action(latest_thought)
        if not action_info:
            action_info = {
                "tool": "log_analyzer",
                "params": {"file_path": state.file_path},
            }
        logger.info(f"Action: {action_info}")

        tool_name = action_info["tool"]
        params = action_info["params"]

        if tool_name in self.tools:
            tool = self.tools[tool_name]
            result = tool._run(**params)

            state.actions_taken.append(
                {
                    "tool": tool_name,
                    "params": params,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Store the result for observation
            state.observations.append(result)

        return state

    def _observe_node(self, state: AgentState) -> AgentState:
        """Observation node - process tool results"""
        if state.observations:
            latest_observation = state.observations[-1]
            logger.info(f"Observation: {latest_observation[:200]}...")

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue thinking or conclude"""
        # Continue if we haven't taken many actions and don't have a clear answer
        if len(state.actions_taken) < 3 and not self._has_sufficient_info(state):
            return "continue"
        return "conclude"

    def _has_sufficient_info(self, state: AgentState) -> bool:
        """Check if we have sufficient information for a conclusion"""
        # Simple heuristic: if we have observations and some analysis results
        return len(state.observations) >= 1 and any(
            "failure" in obs.lower() for obs in state.observations
        )

    def _conclude_node(self, state: AgentState) -> AgentState:
        """Conclusion node - generate final answer"""
        conclusion_prompt = """Based on the analysis performed, provide a comprehensive root cause analysis.
        
        User Query: {query}
        
        Analysis performed:
        {observations}
        
        Provide a structured response with:
        1. Root Cause(s)
        2. Contributing Factors
        3. Impact Assessment
        4. Immediate Recommendations
        5. Long-term Prevention Strategies
        
        Format as clear, actionable insights.
        """

        observations_summary = "\n".join([f"- {obs}" for obs in state.observations])

        prompt = conclusion_prompt.format(
            query=state.user_query, observations=observations_summary
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        state.final_answer = response.content

        return state

    def _parse_action(self, thought: str) -> Optional[Dict[str, Any]]:
        """Parse action from agent's thought - now handles structured decisions"""
        try:
            # Look for structured action format
            if "ACTION:" in thought and "PARAMS:" in thought:
                action_part = thought.split("ACTION:")[1].split("PARAMS:")[0].strip()
                params_part = thought.split("PARAMS:")[1].strip()
                print("action_part", action_part)
                print("params_part", params_part)
                # Parse parameters - handle both dict string and JSON
                params = {}
                try:
                    # Try to evaluate as dict/JSON
                    if params_part.startswith("{") and params_part.endswith("}"):
                        params = eval(params_part)  # Safe since we control the input
                    else:
                        # Fallback parsing
                        params = {"file_path": AgentConfig.DEFAULT_LOG_FILE}

                        # Extract provider if mentioned
                        for provider in ["stripe", "adyen", "razorpay", "paypal"]:
                            if provider in params_part.lower():
                                params["provider"] = provider
                                break

                        # Extract analysis type if mentioned
                        for analysis_type in [
                            "failure_patterns",
                            "provider_performance",
                            "fraud_detection",
                            "temporal_patterns",
                            "comprehensive",
                        ]:
                            if analysis_type in params_part.lower():
                                params["analysis_type"] = analysis_type
                                break
                except:
                    params = {"file_path": AgentConfig.DEFAULT_LOG_FILE}

                return {"tool": action_part.lower().replace(" ", "_"), "params": params}
            else:
                # No structured format found - return default
                return {
                    "tool": "log_analyzer",
                    "params": {"file_path": AgentConfig.DEFAULT_LOG_FILE},
                }
        except Exception as e:
            logger.error(f"Error parsing action: {e}")
            return {
                "tool": "log_analyzer",
                "params": {"file_path": AgentConfig.DEFAULT_LOG_FILE},
            }

    def analyze(self, query: str, file_path: str = None) -> str:
        """Run the ReAct agent analysis"""
        initial_state = AgentState(
            user_query=query,
            thoughts=[],
            actions_taken=[],
            observations=[],
            file_path=file_path or AgentConfig.DEFAULT_LOG_FILE,
        )

        final_state = self.graph.invoke(initial_state)
        return final_state.get("final_answer") or "Analysis could not be completed"


# Usage example
def main():
    """Example usage of the ReAct agent"""

    if len(sys.argv) < 3:
        print("Usage: python react_agent.py <file_path> <query>")
        sys.exit(1)

    file_path = sys.argv[1]  # Get the file path from the system arguments
    query = sys.argv[2]
    agent = RootCauseReActAgent()

    # Example queries

    result = agent.analyze(query, file_path)
    print(result)


if __name__ == "__main__":
    main()
