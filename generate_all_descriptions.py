import duckdb
import ollama
import json
import os

MODEL = "qwen2.5:14b"
OUTPUT_FILE = "player_descriptions.json"

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select
        c.canonical_player_id as player_id,
        c.player_name,
        c.prime_span_start,
        c.prime_span_end,
        c.prime_season_count,
        c.career_peak_z,
        c.career_winning_z,
        c.career_era_score,
        l.longevity_z
    from int_player_career_scores c
    join int_player_longevity_score l
        on c.canonical_player_id = l.canonical_player_id
""").df()

# Resume support - if this got interrupted partway through, rerunning picks
# up exactly where it left off instead of starting over from zero
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE) as f:
        descriptions = json.load(f)
    print(f"Resuming - {len(descriptions)} descriptions already done")
else:
    descriptions = {}

PROMPT_TEMPLATE = """Write 2-3 sentences about what makes this NBA player's
statistical profile distinctive. Explain what the COMBINATION of these
numbers says about their career shape - don't just restate each number in
turn. Base this ONLY on the stats given - do not mention team names, draft
position, specific games, or awards.

For context on the scale: a z-score above 3 is exceptionally rare (roughly
top 0.1% of this dataset), above 1.5 is rare and genuinely elite, and
around 1.0 is a meaningful but more common threshold.

Player: {name}
Prime seasons: {span_start} to {span_end} ({season_count} elite seasons)
Peak dominance z-score (per-minute dominance at their best): {peak_z:.2f}
Winning impact z-score (share of a winning team's production): {winning_z:.2f}
Era-adjusted efficiency z-score (vs. the entire history of the league): {era_score:.2f}
Longevity z-score (sustained elite seasons vs. typical peers): {longevity_z}
"""

total = len(df)

for i, row in df.iterrows():
    player_id = str(row["player_id"])
    if player_id in descriptions:
        continue

    prompt = PROMPT_TEMPLATE.format(
        name=row["player_name"],
        span_start=row["prime_span_start"],
        span_end=row["prime_span_end"],
        season_count=row["prime_season_count"],
        peak_z=row["career_peak_z"],
        winning_z=row["career_winning_z"],
        era_score=row["career_era_score"],
        longevity_z=f"{row['longevity_z']:.2f}" if row["longevity_z"] is not None else "not enough data",
    )

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 250},
        )
        descriptions[player_id] = response["message"]["content"].strip()
    except Exception as e:
        print(f"  Failed on {row['player_name']}: {e}")
        continue

    # Save after every single player - a crash never costs more than the
    # one currently in progress, given how long this whole run takes
    with open(OUTPUT_FILE, "w") as f:
        json.dump(descriptions, f, indent=2)

    if (i + 1) % 10 == 0 or (i + 1) == total:
        print(f"{i + 1}/{total} done...")

print(f"\nFinished - {len(descriptions)} total descriptions saved to {OUTPUT_FILE}")