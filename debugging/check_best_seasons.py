import duckdb

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select player_name, season, peak_z
    from fct_player_scores
    where player_name in ('Michael Jordan', 'LeBron James')
      and peak_z is not null
    order by player_name, peak_z desc
""").df()

print(df.to_string(index=False))