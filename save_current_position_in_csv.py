import csv
import os
import time
from datetime import datetime, timezone

CSV_FILE = "position_history.csv"

data = {
    "t0": 1.2345,
    "t1": 0.9876,
    "t0_fees": 0.0012,
    "t1_fees": 0.0009,
    "t0_t1_name": "BNB/USDT",
    "total_value": 1523.45,
    "value_unclaimed": 12.78,
    "perf_total_value": 0.034,
    "perf_unclaimed": 0.008
}

columns = [
    "unix_time",
    "readable_time",
    "t0",
    "t1",
    "t0_fees",
    "t1_fees",
    "t0_t1_name",
    "total_value",
    "value_unclaimed",
    "perf_total_value",
    "perf_unclaimed"
]

unix_time = int(time.time())
readable_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

row = {
    "unix_time": unix_time,
    "readable_time": readable_time,
    **data
}

file_exists = os.path.isfile(CSV_FILE)
file_empty = not file_exists or os.path.getsize(CSV_FILE) == 0

with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)

    if file_empty:
        writer.writeheader()

    writer.writerow(row)

print(f"Position appended to {CSV_FILE} at {readable_time}")
