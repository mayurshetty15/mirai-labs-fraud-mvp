"""Layer 5 decision logic combining rules, graph, and model signals."""


def combine_scores(rules_flag: bool, graph_flag: bool, gbt_score: float) -> dict:
    """Return a block, review, or allow decision with its signal explanation."""
    gbt_score = float(gbt_score)
    signals = []
    if rules_flag:
        signals.append("velocity rule flagged the transaction")
    if graph_flag:
        signals.append("device-card graph rule flagged the transaction")
    if gbt_score > 0.7:
        signals.append(f"GBT score {gbt_score:.3f} exceeded 0.7")
    elif gbt_score > 0.4:
        signals.append(f"GBT score {gbt_score:.3f} exceeded 0.4")

    if gbt_score > 0.7 or (rules_flag and graph_flag):
        decision = "block"
    elif gbt_score > 0.4 or rules_flag or graph_flag:
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
