"""Print saved LightGBM holdout metrics for the project launcher."""

import warnings
from contextlib import redirect_stderr
from io import StringIO

warnings.filterwarnings(
    "ignore",
    message="Could not find the number of physical cores*",
    category=UserWarning,
)

def main() -> int:
    try:
        with redirect_stderr(StringIO()):
            from app.layer3_model import get_holdout_metrics
        metrics = get_holdout_metrics()
    except Exception as error:
        print(f"MODEL METRICS unavailable: {error}")
        return 1

    print("==============================================")
    print("MODEL METRICS (Holdout Evaluation)")
    print("==============================================")
    print(f"ROC-AUC:    {metrics['roc_auc']:.4f}")
    print(f"Recall:     {metrics['recall']:.1%}")
    print(f"Precision:  {metrics['precision']:.1%}")
    print(f"PR-AUC:     {metrics['pr_auc']:.4f}")
    print(f"Brier score: {metrics['brier_score']:.6f}")
    print("==============================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())