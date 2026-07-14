import re
import unicodedata
import duckdb
import pandas as pd


def normalize_name(name):
    name = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    name = name.replace(".", "").replace("'", "").replace("-", "").lower()
    name = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", name)
    name = re.sub(r"\s[a-z]\s", " ", name)
    return name


con = duckdb.connect("goat.duckdb")

old_df = con.execute("""
    select player_name as name, max(season) as last_season
    from stg_player_basic_totals_old
    group by player_name
    having max(season) >= '1992-93'
""").df()
old_df["year"] = old_df["last_season"].str[:4].astype(int) + 1
old_df["name_key"] = old_df["name"].apply(normalize_name)

modern_df = con.execute("""
    select player_name as name, min(season) as first_season
    from stg_player_season_totals
    group by player_name
    having min(season) <= '2000-01'
""").df()
modern_df["year"] = modern_df["first_season"].str[:4].astype(int) + 1
modern_df["name_key"] = modern_df["name"].apply(normalize_name)

# Check specific known-gap cases directly - no Splink involved, just the raw numbers
check_names = ["Adonis Jordan", "John Salley", "Michael Jordan", "Fred Vinson"]

for name in check_names:
    old_row = old_df[old_df["name"] == name]
    modern_row = modern_df[modern_df["name"] == name]
    print(f"--- {name} ---")
    print("Old-era row(s):")
    print(old_row[["name", "last_season", "year"]].to_string(index=False))
    print("Modern row(s):")
    print(modern_row[["name", "first_season", "year"]].to_string(index=False))
    print()

print()
print(f"Total distinct old-era name_keys: {old_df['name_key'].nunique()}")
print(f"Total distinct modern name_keys: {modern_df['name_key'].nunique()}")