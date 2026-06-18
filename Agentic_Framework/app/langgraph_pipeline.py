from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.extractor import extract_all_cases
from app.guidelines import run_guideline_checks
from app.human_review import route_human_review_from_outputs
from app.medication_safety import run_medication_safety_checks
from app.panel_decision import make_panel_decision_from_outputs
from app.risk_scoring import calculate_risk_scores
from app.schemas import ClinicalExtraction
from app.specialist_agents import run_specialist_agents


class CaseReviewState(TypedDict, total=False):
    extraction: ClinicalExtraction
    guideline_result: Any
    medication_safety_result: Any
    risk_scores: Any
    specialist_bundle: Any
    human_route: Any
    panel_decision: Any


def guideline_node(state: CaseReviewState) -> CaseReviewState:
    extraction = state["extraction"]
    return {"guideline_result": run_guideline_checks(extraction)}


def medication_safety_node(state: CaseReviewState) -> CaseReviewState:
    extraction = state["extraction"]
    return {"medication_safety_result": run_medication_safety_checks(extraction)}


def risk_scoring_node(state: CaseReviewState) -> CaseReviewState:
    extraction = state["extraction"]
    return {
        "risk_scores": calculate_risk_scores(
            extraction,
            state["guideline_result"],
            state["medication_safety_result"],
        )
    }


def specialist_agents_node(state: CaseReviewState) -> CaseReviewState:
    return {"specialist_bundle": run_specialist_agents(state["extraction"])}


def human_review_node(state: CaseReviewState) -> CaseReviewState:
    return {
        "human_route": route_human_review_from_outputs(
            state["extraction"],
            state["guideline_result"],
            state["medication_safety_result"],
            state["risk_scores"],
            state["specialist_bundle"],
        )
    }


def panel_decision_node(state: CaseReviewState) -> CaseReviewState:
    return {
        "panel_decision": make_panel_decision_from_outputs(
            state["extraction"],
            state["guideline_result"],
            state["medication_safety_result"],
            state["risk_scores"],
            state["specialist_bundle"],
            state["human_route"],
        )
    }


def build_case_review_graph():
    graph = StateGraph(CaseReviewState)
    graph.add_node("guidelines", guideline_node)
    graph.add_node("medication_safety", medication_safety_node)
    graph.add_node("risk_scoring", risk_scoring_node)
    graph.add_node("specialist_agents", specialist_agents_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("panel_decision", panel_decision_node)

    graph.set_entry_point("guidelines")
    graph.add_edge("guidelines", "medication_safety")
    graph.add_edge("medication_safety", "risk_scoring")
    graph.add_edge("risk_scoring", "specialist_agents")
    graph.add_edge("specialist_agents", "human_review")
    graph.add_edge("human_review", "panel_decision")
    graph.add_edge("panel_decision", END)
    return graph.compile()


CASE_REVIEW_GRAPH = build_case_review_graph()


def review_case_with_graph(extraction: ClinicalExtraction) -> CaseReviewState:
    return CASE_REVIEW_GRAPH.invoke({"extraction": extraction})


def review_all_cases_with_graph() -> dict[str, CaseReviewState]:
    return {
        extraction.case_id: review_case_with_graph(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    results = review_all_cases_with_graph()
    urgent_cases = [
        case_id
        for case_id, state in results.items()
        if state["panel_decision"].decision == "Urgent Review"
    ]
    print(f"langgraph_reviewed_cases={len(results)}")
    print(f"langgraph_urgent_cases={len(urgent_cases)}")
    print(f"first_case={next(iter(results))}")


if __name__ == "__main__":
    main()
