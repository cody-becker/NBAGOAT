import duckdb
 
con = duckdb.connect("goat.duckdb")
 
df = con.execute("""
    select player_name, season, per, bpm, vorp
    from int_player_advanced_join
    where player_name = 'Sun Yue'
""").df()
 
print(df.to_string(index=False))
 