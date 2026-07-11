import duckdb
 
con = duckdb.connect("goat.duckdb")
 
print("--- Total rows now, both eras combined ---")
total = con.execute("select count(*) from fct_player_scores").fetchone()[0]
print(f"{total} player-seasons total")
 
print()
print("--- Checking for the players this whole build was about ---")
names_to_check = [
    "Wilt Chamberlain", "Bill Russell", "Oscar Robertson",
    "Michael Jordan", "Kareem Abdul-Jabbar", "Larry Bird", "Magic Johnson",
]
df = con.execute("""
    select player_name, season, peak_z, winning_z, era_score
    from fct_player_scores
    where player_name in ?
    order by player_name, season
""", [names_to_check]).df()
print(df.to_string(index=False))
 
print()
print("--- Michael Jordan specifically, EVERY season now available ---")
jordan = con.execute("""
    select season, peak_z, winning_z, era_score
    from fct_player_scores
    where player_name = 'Michael Jordan'
    order by season
""").df()
print(jordan.to_string(index=False))