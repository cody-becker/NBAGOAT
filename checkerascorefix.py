import duckdb
 
con = duckdb.connect("goat.duckdb")
 
# These are known thin-sample players from the earlier check - they should
# now show NULL era_score, since games_played < 20 excludes them
check_names = ["Bruce Bowen", "Sun Yue", "Nate Hinton", "Ahmad Caver"]
 
df = con.execute("""
    select player_name, season, era_score
    from int_player_era_score
    where player_name in ?
""", [check_names]).df()
 
print("Thin-sample players (should be absent - no row means correctly excluded):")
print(df.to_string(index=False) if len(df) else "(none found - correctly excluded)")
print()
 
counts = con.execute("""
    select
        (select count(*) from int_player_advanced_join where bpm is not null) as pre_filter_count,
        (select count(*) from int_player_era_score) as post_filter_count
""").df()
print(counts)