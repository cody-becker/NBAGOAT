import duckdb
import pandas as pd

con = duckdb.connect("goat.duckdb")

old_df = con.execute("""
    select player_name as name, max(season) as last_season
    from stg_player_basic_totals_old
    group by player_name
    having max(season) >= '1992-93'
""").df()
old_df["year"] = old_df["last_season"].str[:4].astype(int) + 1

modern_df = con.execute("""
    select player_name as name, min(season) as first_season
    from stg_player_season_totals
    group by player_name
    having min(season) <= '2000-01'
""").df()
modern_df["year"] = modern_df["first_season"].str[:4].astype(int) + 1

merged = old_df.merge(modern_df, on="name", suffixes=("_old", "_modern"))
merged["gap"] = merged["year_modern"] - merged["year_old"]

print(merged["gap"].value_counts().sort_index())