"""
qa_agent/checks/__init__.py — Check registry.

Each check module exposes a `run(snapshot, context) -> list[CheckResult]` function.
"""
from qa_agent.checks.developer import run as run_developer
from qa_agent.checks.designer import run as run_designer
from qa_agent.checks.copywriter import run as run_copywriter


ALL_CHECK_MODULES = [
    ("developer", run_developer),
    ("designer", run_designer),
    ("copywriter", run_copywriter),
]


def run_all(snapshot, context) -> list:
    """Run all check modules and return combined results."""
    results = []
    for _name, run_fn in ALL_CHECK_MODULES:
        results.extend(run_fn(snapshot, context))
    return results
