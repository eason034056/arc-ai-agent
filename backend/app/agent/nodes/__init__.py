"""
Agent Nodes Module

This module contains all individual nodes for the LangGraph workflow.

Each node is a pure function that:
1. Takes AgentState as input
2. Performs a specific operation
3. Returns updated AgentState

Nodes should be:
- Pure functions (no side effects except via injected dependencies)
- Testable in isolation
- Focused on a single responsibility
"""


"""Node package for the Arc AI Agent workflow.

This package dynamically loads either mock or real node modules
depending on the environment setting (ENV=dev or ENV=prod).
"""

import os
import importlib


def load_node(module_name: str):
    """Dynamically import a node module by name."""
    return importlib.import_module(f"app.agent.nodes.{module_name}")


# ─────────────────────────────────────────────
# Dynamically load node modules
# ─────────────────────────────────────────────

# Common nodes (always real)
detect = load_node("node_detect")
summarize = load_node("node_summarize")

# Slack integration
propose = load_node("node_propose")
approve_gate = load_node("node_approve_gate")

# Onchain node: choose mock or real version based on ENV
if os.getenv("ENV") == "dev":
    print("[DEV MODE] Loading mock onchain node.")
    onchain = load_node("node_onchain")  # ← mock version
else:
    print("[PROD MODE] Loading real onchain node.")
    try:
        onchain = load_node("onchain")  # ← real version (if exists)
    except ModuleNotFoundError:
        print("[WARN] Real onchain module not found. Using mock instead.")
        onchain = load_node("node_onchain")

