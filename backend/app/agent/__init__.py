"""
AI Agent Module

This module contains the LangGraph-based AI agent for payroll automation.

Components:
- graph.py: Main LangGraph workflow definition
- policies.py: Business rules and policies
- nodes/: Individual workflow nodes
  - node_ingest.py: Data ingestion
  - node_clean.py: Data cleaning and validation
  - node_compute.py: Salary computation
  - node_detect.py: Anomaly detection
  - node_summarize.py: AI-powered summarization
  - node_propose.py: Prepare approval request
  - node_approve_gate.py: Wait for human approval
  - node_onchain.py: Execute blockchain transactions
  - node_writeback.py: Write results to expense system
  - node_reconcile.py: Reconciliation and reporting

Workflow Flow:
    ingest → clean → compute → detect → summarize →
    propose → approve_gate → onchain → writeback → reconcile → done
"""

