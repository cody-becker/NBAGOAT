import duckdb
import json
import math

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select
        c.canonical_player_id as player_id,
        c.player_name,
        c.prime_span_start,
        c.prime_span_end,
        c.prime_season_count,
        c.career_peak_z as peak_z,
        c.career_winning_z as winning_z,
        c.career_era_score as era_score,
        l.longevity_z
    from int_player_career_scores c
    join int_player_longevity_score l
        on c.canonical_player_id = l.canonical_player_id
    order by c.career_peak_z desc
""").df()

records = df.to_dict(orient="records")

# Same fix as export_scores.py needed originally - pandas silently reverts
# None back to NaN on float columns, and NaN isn't valid JSON
for r in records:
    for key, val in r.items():
        if isinstance(val, float) and math.isnan(val):
            r[key] = None

with open("career_scores.json", "w") as f:
    json.dump(records, f)

print(f"Exported {len(records)} careers to career_scores.json")
