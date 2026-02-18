"""
LLM usage tracking service for persistent cost monitoring.

Records every LLM API call (tokens, cost) and provides summary queries.
Data is stored in the llm_usage table and never reset.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LlmUsage

logger = logging.getLogger(__name__)

# Pricing per million tokens (input / output)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
}

# Fallback for unknown models
DEFAULT_PRICING = {"input": 3.00, "output": 15.00}


def _compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    return round(cost, 6)


def record_llm_usage(
    db: Session,
    feature: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> LlmUsage:
    """Record a single LLM API call."""
    cost = _compute_cost(model, input_tokens, output_tokens)

    row = LlmUsage(
        feature=feature,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        metadata_=metadata,
    )
    db.add(row)
    db.commit()
    logger.info(
        f"LLM usage recorded: feature={feature} model={model} "
        f"in={input_tokens} out={output_tokens} cost=${cost:.6f}"
    )
    return row


def get_usage_summary(db: Session) -> Dict[str, Any]:
    """Get cumulative LLM usage statistics."""
    # Totals
    totals = db.query(
        func.count(LlmUsage.id).label("total_calls"),
        func.coalesce(func.sum(LlmUsage.input_tokens), 0).label("total_input_tokens"),
        func.coalesce(func.sum(LlmUsage.output_tokens), 0).label("total_output_tokens"),
        func.coalesce(func.sum(LlmUsage.cost_usd), 0).label("total_cost_usd"),
    ).first()

    # Per-feature breakdown
    by_feature_rows = (
        db.query(
            LlmUsage.feature,
            func.count(LlmUsage.id).label("calls"),
            func.sum(LlmUsage.input_tokens).label("input_tokens"),
            func.sum(LlmUsage.output_tokens).label("output_tokens"),
            func.sum(LlmUsage.cost_usd).label("cost_usd"),
        )
        .group_by(LlmUsage.feature)
        .order_by(func.sum(LlmUsage.cost_usd).desc())
        .all()
    )

    by_feature = [
        {
            "feature": row.feature,
            "calls": row.calls,
            "input_tokens": int(row.input_tokens or 0),
            "output_tokens": int(row.output_tokens or 0),
            "cost_usd": round(float(row.cost_usd or 0), 6),
        }
        for row in by_feature_rows
    ]

    # Recent calls (last 20)
    recent_rows = (
        db.query(LlmUsage)
        .order_by(LlmUsage.created_at.desc())
        .limit(20)
        .all()
    )

    recent = [
        {
            "id": row.id,
            "feature": row.feature,
            "model": row.model,
            "input_tokens": row.input_tokens,
            "output_tokens": row.output_tokens,
            "cost_usd": round(row.cost_usd, 6),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in recent_rows
    ]

    return {
        "total_calls": totals.total_calls,
        "total_input_tokens": int(totals.total_input_tokens),
        "total_output_tokens": int(totals.total_output_tokens),
        "total_cost_usd": round(float(totals.total_cost_usd), 6),
        "by_feature": by_feature,
        "recent": recent,
    }
