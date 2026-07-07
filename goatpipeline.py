import time
import duckdb
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguestandings

# Start small on purpose - add more seasons once you've confirmed this works
SEASONS = ["1961-62", "1986-87", "1996-97", "2008-09", "2021-22"]

# Adjust this if you move the script inside the goat_pipeline project folder
DUCKDB_PATH = "goat.duckdb"



def pull_season(season: str) -> pd.DataFrame:
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed="PerGame",
    )
    df = stats.get_data_frames()[0]
    df["season"] = season
    return df


def pull_team_records(season: str) -> pd.DataFrame:
    # Note: LeagueStandings returns a SeasonID field (e.g. "22008"), not the
    # "2008-09" string format used elsewhere in this pipeline - so, same as
    # pull_season() above, we stamp the season string on manually rather than
    # trusting the API's own season field. Keeps the join key consistent with
    # stg_player_season_totals.season downstream.
    standings = leaguestandings.LeagueStandings(season=season)
    df = standings.get_data_frames()[0]
    df["season"] = season
    return df


def main():
    all_seasons = []
    all_team_records = []
    for season in SEASONS:
        print(f"Pulling {season}...")
        all_seasons.append(pull_season(season))
        time.sleep(2)  # don't hammer the API
        all_team_records.append(pull_team_records(season))
        time.sleep(2)  # don't hammer the API

    raw = pd.concat(all_seasons, ignore_index=True)
    raw = raw.rename(columns={
        "PLAYER_ID": "player_id",
        "PLAYER_NAME": "player_name",
        "TEAM_ID": "team_id",
        "GP": "gp",
        "MIN": "mp_pg",
        "PTS": "pts_pg",
        "REB": "reb_pg",
        "AST": "ast_pg",
        "STL": "stl_pg",
        "BLK": "blk_pg",
        "TOV": "tov_pg",
    })[[
        "player_id", "player_name", "season", "team_id", "gp",
        "mp_pg", "pts_pg", "reb_pg", "ast_pg", "stl_pg", "blk_pg", "tov_pg",
    ]]

    team_records = pd.concat(all_team_records, ignore_index=True)
    team_records = team_records.rename(columns={
        "TeamID": "team_id",
        "WINS": "wins",
        "LOSSES": "losses",
        "WinPCT": "win_pct",
    })[[
        "team_id", "season", "wins", "losses", "win_pct",
    ]]

    con = duckdb.connect(DUCKDB_PATH)
    con.execute("CREATE OR REPLACE TABLE raw_player_season_totals AS SELECT * FROM raw")
    print(f"Loaded {len(raw)} rows into raw_player_season_totals")

    con.execute("CREATE OR REPLACE TABLE raw_team_season_records AS SELECT * FROM team_records")
    print(f"Loaded {len(team_records)} rows into raw_team_season_records")


if __name__ == "__main__":
    main()
