import duckdb

con = duckdb.connect("goat.duckdb")

df = con.execute("""
    select season, count(*) as thin_sample_players
    from int_player_advanced_join
    where bpm is not null
      and games_played < 20
    group by season
    order by season
""").df()

print(df)
print()

extremes = con.execute("""
    select player_name, season, games_played, bpm
    from int_player_advanced_join
    where bpm is not null
      and (bpm > 15 or bpm < -10)
    order by bpm
""").df()

print(f"{len(extremes)} players with extreme BPM values (>15 or <-10):")
print(extremes.to_string(index=False))