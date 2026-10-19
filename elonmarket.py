import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import re

slug = "elon-musk-of-tweets-october-13-october-20-2026"

output_file = "elon_hourly_prices.xlsx"

# Get event
event = requests.get(
    f"https://gamma-api.polymarket.com/events?slug={slug}"
).json()[0]

markets = event["markets"]
all_data = []
for m in markets:

    question = m["question"]
    range_match = re.search(r'(\d+)\s*-\s*(\d+)', question)
    plus_match = re.search(r'(\d+)\+', question)
    less_match = re.search(r'<\s*(\d+)', question)

    if range_match:
        name = f"{range_match.group(1)}-{range_match.group(2)}"
    elif plus_match:
        name = f"{plus_match.group(1)}+"
    elif less_match:
        name = f"<{less_match.group(1)}"
    else:
        continue
    token_ids = json.loads(m["clobTokenIds"])
    yes_token = token_ids[0]
    start_ts = int(datetime.fromisoformat(m["startDate"]).replace(tzinfo=timezone.utc).timestamp())
    end_ts = int(datetime.fromisoformat(m["endDate"].replace("Z", "+00:00")).timestamp())+14400

    #end_ts = int(datetime.now(timezone.utc).timestamp())

    url = (
        f"https://clob.polymarket.com/prices-history?"
        f"market={yes_token}&startTs={start_ts}&endTs={end_ts}"
        f"&interval=1w&fidelity=60"
    )


    resp = requests.get(url).json()
    if "history" not in resp:
        print(f"Skipping {name} -> no trades")
        continue

    for h in resp["history"]:
        dt = datetime.fromtimestamp(h["t"], timezone.utc).replace(tzinfo=None)
        all_data.append({
            "time": dt.strftime("%Y-%m-%d %H:%M"),
            "range": name,
            "price": h["p"]
        })
df = pd.DataFrame(all_data)

pivot = pivot_table = df.pivot_table(
    index="time",
    columns="range",
    values="price",
    aggfunc="last"
)

def sort_key(col):
    if col.startswith("<"):
        return -1  # pune <40 primul
    elif "+" in col:
        return 9999  # pune 240+ ultimul
    else:
        return int(col.split("-")[0])

pivot = pivot[sorted(pivot.columns, key=sort_key)]

pivot.to_excel(output_file)

print("DONE ->", output_file)