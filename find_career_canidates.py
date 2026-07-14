import duckdb
 
con = duckdb.connect("goat.duckdb")
 
# Old-era players whose career ran late enough to plausibly continue into
# the modern era - using the same normalized key already built for the
# BR-to-BR join, so formatting differences don't cause false negatives here
old_era_late = con.execute("""
    select
        player_name,
        regexp_replace(
            regexp_replace(
                lower(strip_accents(replace(replace(replace(player_name, '.', ''), '''', ''), '-', ''))),
                '\\s+(jr|sr|ii|iii|iv|v)$', ''
            ),
            '\\s[a-z]\\s', ' ', 'g'
        ) as name_key,
        max(season) as last_old_season
    from stg_player_basic_totals_old
    group by player_name
    having max(season) >= '1992-93'
""").df()
 
# Modern players whose career started early enough to plausibly be a
# continuation of an old-era career
modern_early = con.execute("""
    select
        player_name,
        player_name_key as name_key,
        min(season) as first_modern_season
    from stg_player_season_totals
    group by player_name, player_name_key
    having min(season) <= '2000-01'
""").df()
 
candidates = old_era_late.merge(modern_early, on="name_key", suffixes=("_old", "_modern"))
candidates = candidates[["player_name_old", "last_old_season", "player_name_modern", "first_modern_season"]]
 
print(f"Old-era players active late enough to matter: {len(old_era_late)}")
print(f"Modern players active early enough to matter: {len(modern_early)}")
print(f"Actual name-matched candidate pairs: {len(candidates)}")
print()
print(candidates.sort_values("last_old_season").to_string(index=False))