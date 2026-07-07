import duckdb
from basketball_reference_web_scraper import client

# Names we know exist in your nba_api pull for 2021-22 (accented, tricky ones on purpose)
check_names = ["Nikola Jokić", "Luka Dončić", "Nikola Jović"]

con = duckdb.connect("goat.duckdb")
nba_api_names = con.execute(
    "select distinct player_name from raw_player_season_totals where season = '2021-22'"
).df()["player_name"].tolist()

br_stats = client.players_advanced_season_totals(season_end_year=2022)
br_names = [p["name"] for p in br_stats]

for name in check_names:
    in_nba_api = name in nba_api_names
    in_br = name in br_names
    print(f"{name}: nba_api={in_nba_api}, basketball_reference={in_br}")