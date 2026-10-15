from typing import Literal, TypedDict


class AgentState(TypedDict, total=False):
    alert_id: str
    alert: dict
    messages: list
    controller_visits: int
    node_visits: int
    next: Literal["tools", "submit"]
    status: str
    classification: str
    label: int
    rationale: str
    evidence: list[dict]
    observations: list[dict]
