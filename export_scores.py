import duckdb
import json
import math

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select player_id, player_name, season, peak_z, winning_z, era_score, longevity_z
    from fct_player_scores
    where peak_z is not null
""").df()

records = df.to_dict(orient="records")

# pandas float columns can't hold Python None - df.where(..., None) silently
# reverts back to NaN. Clean it up after converting to plain dicts instead,
# where a NaN can actually become a real None -> valid JSON null.
for row in records:
    for key, val in row.items():
        if isinstance(val, float) and math.isnan(val):
            row[key] = None

with open("player_scores.json", "w") as f:
    json.dump(records, f)

print(f"Exported {len(records)} player-seasons to player_scores.json")
