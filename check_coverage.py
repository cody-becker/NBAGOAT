import duckdb

con = duckdb.connect("goat.duckdb")

by_season = con.execute("""
    select season, count(*) as total, count(per) as matched
    from int_player_advanced_join
    group by season
    order by season
""").df()
print(by_season)
print()

seasons = by_season["season"].tolist()
for season in seasons:
    unmatched = con.execute("""
        select player_name
        from int_player_advanced_join
        where season = ? and per is null
        order by player_name
    """, [season]).df()
    print(f"{len(unmatched)} unmatched in {season}: {unmatched['player_name'].tolist()}")
