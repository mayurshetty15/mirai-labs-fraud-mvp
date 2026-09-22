"""Layer 5 decision logic combining rules, graph, and model signals."""

from app.thresholds import GBT_REVIEW_THRESHOLD


def combine_scores(rules_flag: bool, graph_flag: bool, gbt_score: float) -> dict:
    """Return a block, review, or allow decision with its signal explanation."""
    gbt_score = float(gbt_score)
    signals = []
    if rules_flag:
        signals.append("velocity rule flagged the transaction")
    if graph_flag:
        signals.append("device-card graph rule flagged the transaction")
    if gbt_score >= GBT_REVIEW_THRESHOLD:
        signals.append(
            f"GBT score {gbt_score:.6f} reached {GBT_REVIEW_THRESHOLD:.6f} review threshold"
        )

    if rules_flag and graph_flag:
        decision = "block"
    elif gbt_score >= GBT_REVIEW_THRESHOLD or rules_flag or graph_flag:
        decision = "review"
    else:
        decision = "allow"

    reason = "; ".join(signals) if signals else "no fraud signals triggered"
    return {
        "decision": decision,
        "reason": reason,
        "gbt_score": gbt_score,
        "rules_flag": bool(rules_flag),
        "graph_flag": bool(graph_flag),
    }


if __name__ == "__main__":
    print(combine_scores(True, True, 0.82))
