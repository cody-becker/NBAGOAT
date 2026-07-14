import duckdb

con = duckdb.connect("goat.duckdb")

print("--- Jordan's longevity_z across a few of his individual seasons ---")
df = con.execute("""
    select player_id, season, peak_z, longevity_z
    from fct_player_scores
    where player_name = 'Michael Jordan'
    order by season
""").df()
print(df.to_string(index=False))

print()
print("--- Top 10 longevity_z league-wide, to see who actually sustained the longest ---")
top = con.execute("""
    select distinct player_name, longevity_z
    from fct_player_scores
    where longevity_z is not null
    order by longevity_z desc
    limit 10
""").df()
print(top.to_string(index=False))