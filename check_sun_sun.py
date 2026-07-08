import duckdb

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select *
    from raw_player_season_totals
    where player_name = 'Sun Sun'
""").df()

print(df.to_string(index=False))
