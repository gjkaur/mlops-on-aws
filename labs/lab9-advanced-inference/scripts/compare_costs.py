"""
Illustrative cost comparison for inference deployment patterns (Lab 9).

Numbers are pedagogical stubs — always reconcile with AWS Pricing Calculator.
"""

from __future__ import annotations


def calculate_costs() -> None:
    print("=" * 60)
    print("INFERENCE PATTERN COST COMPARISON (illustrative)")
    print("=" * 60)

    requests_per_month = 100_000
    avg_processing_seconds = 0.10
    memory_gb = 2.0

    realtime_hourly = 0.115
    realtime_monthly_always_on = realtime_hourly * 24 * 30

    serverless_per_gb_hour = 0.0000175  # order-of-magnitude example
    compute_hours = requests_per_month * avg_processing_seconds / 3600.0
    serverless_compute_month = compute_hours * memory_gb * serverless_per_gb_hour
    serverless_requests_month = requests_per_month * 0.0000002

    batch_hourly = 0.115
    batch_cost_one_job = batch_hourly * 0.5

    mme_single = realtime_monthly_always_on
    without_mme = mme_single * 10

    print("\nScenario assumptions:")
    print(
        f"  • Requests/month={requests_per_month:,}; avg inference CPU time ≈ "
        f"{avg_processing_seconds}s; serverless mem ≈ {memory_gb} GB"
    )
    rows = [
        ("Real-time (1 × ml.m5.large 24×7)", realtime_monthly_always_on),
        ("Serverless sketch (stub formula)", serverless_compute_month + serverless_requests_month),
        ("Async realtime host (still 24×7 until scaled)", realtime_monthly_always_on),
        ("Batch Transform (stub: ~30 min per job)", batch_cost_one_job),
    ]

    print("\nPatterns (estimated monthly stubs, instructor demo only)")
    print("-" * 60)
    for label, val in rows:
        print(f"  • {label}: ${val:.2f}")
    print("-" * 60)

    print("\nMulti-model endpoints (sharing one ml.m5.large):")
    print(f"  • 10 discrete endpoints (~stub): ~${without_mme:.2f}/mo")
    print(f"  • 1 shared MME:                    ~${mme_single:.2f}/mo")
    if without_mme:
        sav = (without_mme - mme_single) / without_mme * 100.0
        print(f"  • Illustrative savings vs 10× hosts: ~{sav:.0f}%")

    print(
        "\nTeaching beats: sporadic workloads → weigh serverless; bursty queues → "
        "async hosts; dozens of lightweight models → MME vs fleet; nightly scoring → Batch."
    )


if __name__ == "__main__":
    calculate_costs()
