import duckdb
import ollama

MODEL = "qwen2.5:14b"

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select
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
    where c.player_name in ('Michael Jordan', 'LeBron James', 'Mookie Blaylock')
""").df()

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

for _, row in df.iterrows():
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

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    print(f"--- {row['player_name']} ---")
    print(response["message"]["content"])
    print()