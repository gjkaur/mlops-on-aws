"""
Query offline store using Athena SQL.
"""

import time

import boto3
import pandas as pd


def run_athena_query(query, database, s3_output_location):
    """Run an Athena query and wait for results."""
    athena = boto3.client("athena", region_name="us-east-1")

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": s3_output_location},
    )

    query_execution_id = response["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = status["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            print("Query completed successfully!")
            break
        if state == "FAILED":
            reason = status["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            print(f"Query failed: {reason}")
            return None
        if state == "CANCELLED":
            print("Query was cancelled")
            return None

        print("   Waiting for query to complete...")
        time.sleep(5)

    results = athena.get_query_results(QueryExecutionId=query_execution_id)

    cols = []
    header_row = results["ResultSet"]["Rows"][0]["Data"]
    for col in header_row:
        cols.append(col.get("VarCharValue", "") or "")
    rows = []
    for row in results["ResultSet"]["Rows"][1:]:
        rows.append([c.get("VarCharValue", "") for c in row["Data"]])

    return pd.DataFrame(rows, columns=cols)


if __name__ == "__main__":
    import os

    bucket_name = os.environ.get("BUCKET_NAME")

    if not bucket_name:
        print("ERROR: Set BUCKET_NAME environment variable")
        raise SystemExit(1)

    with open("customer_fg_name.txt", "r", encoding="utf-8") as f:
        customer_fg_name = f.read().strip()
    with open("order_fg_name.txt", "r", encoding="utf-8") as f:
        order_fg_name = f.read().strip()

    customer_table = customer_fg_name.lower().replace("-", "_")
    order_table = order_fg_name.lower().replace("-", "_")

    database = "sagemaker_featurestore"
    s3_output = f"s3://{bucket_name}/athena-results/"

    print("=" * 50)
    print("Offline Store Query with Athena")
    print("=" * 50)

    query1 = f"""
    SELECT customer_id, age, avg_monthly_spend, tenure_months, support_tickets
    FROM "{database}"."{customer_table}"
    LIMIT 10
    """

    print("\n1. Customer Features:")
    df1 = run_athena_query(query1, database, s3_output)
    if df1 is not None:
        print(df1.to_string(index=False))

    query2 = f"""
    SELECT
        c.customer_id,
        c.age,
        c.avg_monthly_spend,
        COUNT(o.order_id) as total_orders,
        SUM(o.order_amount) as total_spend
    FROM "{database}"."{customer_table}" c
    LEFT JOIN "{database}"."{order_table}" o
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.age, c.avg_monthly_spend
    """

    print("\n2. Customer Summary with Order Aggregates:")
    df2 = run_athena_query(query2, database, s3_output)
    if df2 is not None:
        print(df2.to_string(index=False))

    print("\n✅ Offline store queries complete!")
