"""Architecture assessment and AI governance metadata for the control tower.

This is intentionally read-only: it exposes Phase 1/2 findings without changing the
existing optimization, AI, or visualization contracts.
"""
from __future__ import annotations

from typing import Any, Dict, List

from config import settings


def platform_assessment() -> Dict[str, Any]:
    phase_1_findings: List[Dict[str, str]] = [
        {
            "area": "Optimization latency",
            "finding": "Synchronous VRP requests can block API workers on larger France route sets.",
            "recommendation": "Move OR-Tools runs to background jobs with persisted job status and warm starts.",
        },
        {
            "area": "State management",
            "finding": "The demo keeps mutable scenario state in process memory.",
            "recommendation": "Persist orders, vehicles, scenarios, and optimization results in PostgreSQL before horizontal scaling.",
        },
        {
            "area": "Distance matrix cost",
            "finding": "Matrix rebuilds are repeated after disruptions and depend on an external OSRM demo endpoint.",
            "recommendation": "Cache matrices by coordinate hash and deploy a France-focused OSRM/Maps service with traffic overlays.",
        },
        {
            "area": "AI responsibility boundary",
            "finding": "The assistant is useful but must not solve shortest paths or override OR-Tools decisions.",
            "recommendation": "Use Mistral only for RAG-grounded operational reasoning, exception triage, and workflow orchestration.",
        },
        {
            "area": "Security configuration",
            "finding": "Demo defaults should be tightened for enterprise deployments.",
            "recommendation": "Keep CORS, model names, API keys, and routing providers environment-driven and add rate limiting at the API gateway.",
        },
    ]

    target_architecture = [
        "React + Vite control tower with memoized map layers, lazy analytics panels, and SSE Co-Pilot streaming.",
        "FastAPI orchestration API with version-compatible /api endpoints and future /api/v1 expansion.",
        "OR-Tools optimization service for VRP, time windows, capacities, driver shifts, and SLA penalties.",
        "Routing provider adapter for OSRM or Google Maps distance/ETA matrices with traffic-aware cache invalidation.",
        "Mistral AI intelligence service using RAG Pipeline Engineering for recommendations, not mathematical optimization.",
        "PostgreSQL operational store for orders, vehicles, depots, scenarios, job status, audit trails, and analytics snapshots.",
    ]

    ai_governance = {
        "selected_pattern_from_reference": settings.ai_pattern,
        "mistral_model": settings.mistral_model,
        "allowed_responsibilities": [
            "operational reasoning",
            "dispatch recommendations",
            "exception handling",
            "natural language interpretation",
            "workflow orchestration",
        ],
        "blocked_responsibilities": [
            "shortest-path routing",
            "VRP solving",
            "time-window scheduling mathematics",
            "capacity optimization",
            "direct mutation of dispatch plans without API validation",
        ],
        "rag_scope": [
            "current route KPIs",
            "utilization and idle fleet signals",
            "SLA and time-window exceptions",
            "carbon and sustainability metrics",
            "France operating constraints and CEVA brand-safe response guidelines",
        ],
    }

    incremental_roadmap = [
        "Phase 1: expose findings, centralize config, and France-align demo data/branding.",
        "Phase 2: introduce job-backed optimization and PostgreSQL-backed scenario storage.",
        "Phase 3: add traffic-aware matrix caching and telematics ingestion.",
        "Phase 4: expand Mistral RAG workflows for exception playbooks, root-cause summaries, and dispatcher approvals.",
    ]

    return {
        "platform": settings.app_name,
        "region": settings.operating_region,
        "control_tower": settings.control_tower,
        "phase_1_findings": phase_1_findings,
        "target_architecture": target_architecture,
        "ai_governance": ai_governance,
        "incremental_roadmap": incremental_roadmap,
    }
