import duckdb

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


def tier(z, high=3.0, mid=1.5):
    if z >= high:
        return "elite"
    elif z >= mid:
        return "strong"
    else:
        return "solid"


def describe(row):
    peak_tier = tier(row["career_peak_z"])
    win_tier = tier(row["career_winning_z"])
    era_tier = tier(row["career_era_score"])

    sentence1 = (
        f"During a {row['prime_season_count']}-season prime "
        f"({row['prime_span_start']}-{row['prime_span_end']}), "
        f"{row['player_name']} posted {peak_tier} peak dominance "
        f"(z={row['career_peak_z']:.2f}) and {win_tier} winning impact "
        f"(z={row['career_winning_z']:.2f})."
    )

    if row["longevity_z"] is not None and row["longevity_z"] >= 3.0:
        longevity_clause = "an unusually long stretch of sustained excellence, longer than almost any peer"
    elif row["longevity_z"] is not None and row["longevity_z"] >= 1.0:
        longevity_clause = "a genuinely durable run at an elite level"
    else:
        longevity_clause = "a shorter but still genuinely elite window"

    sentence2 = (
        f"Measured against the entire history of the league, their efficiency "
        f"ranks as {era_tier} (era z={row['career_era_score']:.2f}), "
        f"across {longevity_clause}."
    )

    return sentence1 + " " + sentence2


for _, row in df.iterrows():
    print(f"--- {row['player_name']} ---")
    print(describe(row))
    print()