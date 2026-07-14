import duckdb
 
con = duckdb.connect("goat.duckdb")
 
by_season = con.execute("""
    select season, count(*) as total, count(bpm) as matched
    from int_player_advanced_join
    where season < '1996-97'
    group by season
    order by season
""").df()
print(by_season)
print()
 
overall = con.execute("""
    select count(*) as total, count(bpm) as matched
    from int_player_advanced_join
    where season < '1996-97'
""").fetchone()
total, matched = overall
print(f"Overall old-era match rate: {matched}/{total} ({matched/total:.1%})")
print()
 
unmatched = con.execute("""
    select season, player_name
    from int_player_advanced_join
    where season < '1996-97' and bpm is null
    order by season, player_name
""").df()
print(f"{len(unmatched)} unmatched old-era rows:")
print(unmatched.to_string(index=False))
 