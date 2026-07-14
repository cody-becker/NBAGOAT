import duckdb
 
con = duckdb.connect("goat.duckdb")
 
df = con.execute("""
    select player_name, peak_z
    from fct_player_scores
    where season = '1996-97'
    order by peak_z desc
    limit 10
""").df()
 
print(df.to_string(index=False))
 