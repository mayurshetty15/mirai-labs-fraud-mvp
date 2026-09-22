# Calibrated Threshold Analysis

The true time-based holdout contains 56,962 transactions and 75 known fraud cases (0.1317%). The calibrated model's scores were swept from 0.01 to 0.50, then through the observed score range because every score in the first range produced an empty queue.

|         Threshold | Precision |     Recall |      Queue |
| ----------------: | --------: | ---------: | ---------: |
| 0.000001-0.000250 |     0.13% |    100.00% |    100.00% |
|      **0.000300** | **0.67%** | **81.33%** | **16.05%** |
|          0.005255 |     0.67% |     81.33% |     16.04% |
| 0.006000-0.500000 |     0.00% |      0.00% |      0.00% |

At threshold 0.0003, we catch 81.33% of known fraud while sending 16.05% of all transactions to review (61 of 75 fraud cases and 9,140 of 56,962 transactions).

The calibrated scores are highly quantized on this holdout, so there is no measured threshold in the tested range that catches 70-80% of fraud with a smaller queue. This operating point is centralized as `app.thresholds.GBT_REVIEW_THRESHOLD`.

Model-only blocking is disabled for calibrated probabilities because the holdout does not support a distinct high-confidence block threshold. Transactions can still be blocked when both velocity and device-card graph rules flag them; model scores at or above the operating threshold enter review.
