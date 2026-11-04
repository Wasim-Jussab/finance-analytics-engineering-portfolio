"""Swappable local proposal producer with existing governed routing as a veto."""

from typing import Protocol

from operations_assistant.intent import LocalIntentModel, QuestionRequest
from operations_assistant.proposals import authorize_proposal


class ProposalAdapter(Protocol):
    adapter_name: str

    def propose(self, scope: QuestionRequest) -> str:
        """Return untrusted JSON; never execute a tool."""
        ...


class ClassifierProposalAdapter:
    """Executed classifier baseline, not a generative language model."""

    adapter_name = "local-classifier-proposal-v1"

    def __init__(self, router: LocalIntentModel):
        self.router = router

    def propose(self, scope: QuestionRequest) -> str:
        request, _ = self.router.plan(scope)
        return request.model_dump_json()


def plan_with_adapter(scope: QuestionRequest, adapter: ProposalAdapter, router: LocalIntentModel):
    """Produce, validate and authorise a request; do not execute or release it."""
    raw = adapter.propose(scope)
    if not isinstance(raw, str):
        raise ValueError("Proposal adapter must return JSON text")
    request, routing = authorize_proposal(raw, scope, router)
    return request, {**routing, "proposal_adapter": adapter.adapter_name}
