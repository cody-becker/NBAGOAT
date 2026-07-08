import time
import duckdb
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguestandings
from basketball_reference_web_scraper import client

# Start small on purpose - add more seasons once you've confirmed this works
SEASONS = ["1996-97", "2008-09", "2021-22"]

DUCKDB_PATH = "goat.duckdb"


def season_to_end_year(season: str) -> int:
    # "2008-09" -> 2009, "1996-97" -> 1997
    # Basketball-Reference's own convention: a season is named by the year it ENDS in
    start_year = int(season.split("-")[0])
    return start_year + 1


def pull_season(season: str) -> pd.DataFrame:
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed="PerGame",
    )
    df = stats.get_data_frames()[0]
    df["season"] = season
    return df


def pull_team_records(season: str) -> pd.DataFrame:
    standings = leaguestandings.LeagueStandings(season=season)
    df = standings.get_data_frames()[0]
    df["season"] = season
    return df


def pull_advanced_stats(season: str) -> pd.DataFrame:
    season_end_year = season_to_end_year(season)
    stats = client.players_advanced_season_totals(season_end_year=season_end_year)
    df = pd.DataFrame(stats)

    if df.empty:
        print(f"  WARNING: no Basketball-Reference advanced stats for {season}")
        return df

    # Enums -> plain strings, so DuckDB/dbt see normal text, not Python objects
    df["team"] = df["team"].apply(lambda t: t.value if t is not None else None)
    df["positions"] = df["positions"].apply(
        lambda ps: ",".join(p.value for p in ps) if ps else None
    )

    # Traded players get a per-team row PLUS a combined-season row
    # (is_combined_totals=True). Keep the combined row when it exists,
    # otherwise the single row a non-traded player already has is fine.
    df = df.sort_values("is_combined_totals", ascending=False).drop_duplicates(
        subset="name", keep="first"
    )

    df["season"] = season
    return df[[
        "name", "season", "team", "positions", "age", "games_played",
        "minutes_played", "player_efficiency_rating", "true_shooting_percentage",
        "usage_percentage", "offensive_win_shares", "defensive_win_shares",
        "win_shares", "win_shares_per_48_minutes", "offensive_box_plus_minus",
        "defensive_box_plus_minus", "box_plus_minus", "value_over_replacement_player",
    ]]


def main():
    all_seasons = []
    all_team_records = []
    all_advanced = []

    for season in SEASONS:
        print(f"Pulling {season} (nba_api player stats)...")
        all_seasons.append(pull_season(season))
        time.sleep(1)

        print(f"Pulling {season} (nba_api team standings)...")
        all_team_records.append(pull_team_records(season))
        time.sleep(1)

        print(f"Pulling {season} (Basketball-Reference advanced stats)...")
        all_advanced.append(pull_advanced_stats(season))
        time.sleep(3)  # BR rate-limits harder than nba_api - be more patient here

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
    })[["team_id", "season", "wins", "losses", "win_pct"]]

    advanced = pd.concat([df for df in all_advanced if not df.empty], ignore_index=True)

    con = duckdb.connect(DUCKDB_PATH)

    con.execute("CREATE OR REPLACE TABLE raw_player_season_totals AS SELECT * FROM raw")
    print(f"Loaded {len(raw)} rows into raw_player_season_totals")

    con.execute("CREATE OR REPLACE TABLE raw_team_season_records AS SELECT * FROM team_records")
    print(f"Loaded {len(team_records)} rows into raw_team_season_records")

    con.execute("CREATE OR REPLACE TABLE raw_player_advanced_stats AS SELECT * FROM advanced")
    print(f"Loaded {len(advanced)} rows into raw_player_advanced_stats")


if __name__ == "__main__":
    main()
