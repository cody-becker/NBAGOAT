import re
import unicodedata
import duckdb
import pandas as pd
from splink import Linker, SettingsCreator, DuckDBAPI, block_on
import splink.comparison_library as cl
import splink.comparison_level_library as cll


def normalize_name(name):
    name = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    name = name.replace(".", "").replace("'", "").replace("-", "").lower()
    name = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", name)
    name = re.sub(r"\s[a-z]\s", " ", name)
    return name


con = duckdb.connect("goat.duckdb")

old_df = con.execute("""
    select player_id, player_name as name, max(season) as last_season
    from stg_player_basic_totals_old
    group by player_id, player_name
    having max(season) >= '1992-93'
""").df()
old_df["year"] = old_df["last_season"].str[:4].astype(int) + 1
old_df["unique_id"] = ["old_" + str(i) for i in range(len(old_df))]
old_df["name_key"] = old_df["name"].apply(normalize_name)
old_df = old_df.rename(columns={"player_id": "real_player_id"})
old_df = old_df[["real_player_id", "name", "year", "unique_id", "name_key"]]

modern_df = con.execute("""
    select player_id, player_name as name, min(season) as first_season
    from stg_player_season_totals
    group by player_id, player_name
    having min(season) <= '2000-01'
""").df()
modern_df["year"] = modern_df["first_season"].str[:4].astype(int) + 1
modern_df["unique_id"] = ["mod_" + str(i) for i in range(len(modern_df))]
modern_df["name_key"] = modern_df["name"].apply(normalize_name)
modern_df = modern_df.rename(columns={"player_id": "real_player_id"})
modern_df = modern_df[["real_player_id", "name", "year", "unique_id", "name_key"]]

name_comparison = cl.ExactMatch("name_key").configure(
    term_frequency_adjustments=True,
    m_probabilities=[0.95, 0.05],
    # A random exact match on one SPECIFIC name should be roughly
    # 1/(number of distinct names), not a guessed constant - hardcoding a
    # small toy-scale number here (an earlier version used 0.02) badly
    # under-penalizes how surprising a name match really is once the real
    # population is large, which let name evidence overpower even a bad
    # timeline gap. Compute it from the actual data instead of guessing.
    u_probabilities=[1 / max(len(old_df), len(modern_df)), 1 - 1 / max(len(old_df), len(modern_df))],
)
year_comparison = cl.CustomComparison(
    output_column_name="year",
    comparison_levels=[
        cll.AbsoluteDifferenceLevel("year", 1).configure(m_probability=0.85, u_probability=0.3),
        # Recalibrated - the first version (m=0.10) wasn't harsh enough to
        # pull scores into a visible middle band once name evidence was
        # correctly scaled to real population size. Verified this value
        # actually lands 2-3 year real gaps around ~0.85-0.90, not ~0.98.
        cll.AbsoluteDifferenceLevel("year", 3).configure(m_probability=0.002, u_probability=0.3),
        cll.ElseLevel().configure(m_probability=0.0003, u_probability=0.4),
    ],
)

settings = SettingsCreator(
    link_type="link_only",
    comparisons=[name_comparison, year_comparison],
    blocking_rules_to_generate_predictions=[block_on("name_key")],
    probability_two_random_records_match=0.6,
)

db_api = DuckDBAPI()
linker = Linker([modern_df, old_df], settings, db_api=db_api,
                input_table_aliases=["modern", "old_era"])
linker.table_management.compute_tf_table("name_key")

results = linker.inference.predict().as_pandas_dataframe()

results = results.merge(
    modern_df[["unique_id", "name", "real_player_id"]].rename(
        columns={"unique_id": "unique_id_l", "name": "name_modern", "real_player_id": "modern_player_id"}
    ),
    on="unique_id_l",
).merge(
    old_df[["unique_id", "name", "real_player_id"]].rename(
        columns={"unique_id": "unique_id_r", "name": "name_old", "real_player_id": "old_player_id"}
    ),
    on="unique_id_r",
)

results = results.rename(columns={"year_l": "year_modern", "year_r": "year_old"})

# Names manually verified by hand - either via real career-history research
# (Andrew Gaze, Thurl Bailey, John Amaechi, John Salley) or, more
# authoritatively, by checking nba_api's own FROM_YEAR/TO_YEAR record
# directly for the exact player_id in question (the other six)
manually_confirmed = {
    "Andrew Gaze", "Thurl Bailey", "John Amaechi", "John Salley",
    "Larry Robinson", "Adonis Jordan", "Charles Shackleford",
    "Negele Knight", "Thomas Hamilton", "Fred Vinson",
}
results["manually_reviewed"] = results["name_old"].isin(manually_confirmed)

# Pairs verified as NOT the same person, checked directly against nba_api's
# authoritative record. modern_player_id 1520 is a genuine THIRD Charles
# Smith (guard, FROM_YEAR 1997) - unrelated to either old-era candidate,
# whose careers ran 1988-1997ish and pre-1992 respectively. A real,
# confirmed false positive, not just a low-confidence guess - excluded
# entirely rather than left in the crosswalk at any confidence level.
excluded_pairs = {("smithch01", 1520), ("smithch02", 1520)}
results = results[
    ~results.apply(
        lambda r: (str(r["old_player_id"]), int(r["modern_player_id"])) in excluded_pairs, axis=1
    )
]

results = results[[
    "old_player_id", "modern_player_id", "name_old", "name_modern",
    "year_old", "year_modern", "match_probability", "manually_reviewed"
]]
results = results.sort_values("match_probability", ascending=False)

results.to_csv("player_career_crosswalk.csv", index=False)
print(f"{len(results)} total candidate pairs scored")
print()
print(f"High confidence (>=0.95): {(results['match_probability'] >= 0.95).sum()}")
print(f"Medium (0.80-0.95): {((results['match_probability'] >= 0.80) & (results['match_probability'] < 0.95)).sum()}")
print(f"Worth a human look (<0.80): {(results['match_probability'] < 0.80).sum()}")
print()
print("--- Everything under 0.80, sorted worst first ---")
print(results[results["match_probability"] < 0.80].sort_values("match_probability").to_string(index=False))