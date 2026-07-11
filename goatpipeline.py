import time
import duckdb
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguestandings
from basketball_reference_web_scraper import client

# All seasons nba_api actually covers - 1996-97 is the real floor, see
# earlier findings: pre-1996-97 returns empty from this endpoint every time
SEASONS = [
    "1996-97", "1997-98", "1998-99", "1999-00", "2000-01",
    "2001-02", "2002-03", "2003-04", "2004-05", "2005-06",
    "2006-07", "2007-08", "2008-09", "2009-10", "2010-11",
    "2011-12", "2012-13", "2013-14", "2014-15", "2015-16",
    "2016-17", "2017-18", "2018-19", "2019-20", "2020-21",
    "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
]

# Seasons nba_api has NOTHING for, so Basketball-Reference has to be the
# entire backbone instead of just the advanced-stats supplement. Floor is
# 1973-74 on purpose, not further back - steals/blocks weren't tracked
# before that, which is exactly why BPM defaulted to a meaningless 0.0 for
# Wilt's 1961-62 season during the earlier stress test. Going further back
# would just reintroduce that same broken signal.
OLD_SEASONS = [
    "1973-74", "1974-75", "1975-76", "1976-77", "1977-78",
    "1978-79", "1979-80", "1980-81", "1981-82", "1982-83",
    "1983-84", "1984-85", "1985-86", "1986-87", "1987-88",
    "1988-89", "1989-90", "1990-91", "1991-92", "1992-93",
    "1993-94", "1994-95", "1995-96",
]

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


def pull_old_basic_stats(season: str, max_retries: int = 3) -> pd.DataFrame:
    season_end_year = season_to_end_year(season)

    for attempt in range(1, max_retries + 1):
        stats = client.players_season_totals(season_end_year=season_end_year)
        df = pd.DataFrame(stats)

        if not df.empty:
            break

        if attempt < max_retries:
            wait = 15 * attempt
            print(f"  Got 0 rows for {season} basic stats (attempt {attempt}/{max_retries}), "
                  f"waiting {wait}s and retrying...")
            time.sleep(wait)
        else:
            print(f"  WARNING: no Basketball-Reference basic stats for {season} "
                  f"after {max_retries} attempts")
            return df

    df["team"] = df["team"].apply(lambda t: t.value if t is not None else None)
    df["total_rebounds"] = df["offensive_rebounds"] + df["defensive_rebounds"]

    # Traded players show up as multiple rows here (one per team stint), but
    # unlike the advanced-stats endpoint, this one gives real season TOTALS,
    # not pre-computed rates - so instead of picking a single "combined" row,
    # we can just sum the stints ourselves and derive accurate per-game
    # numbers directly. More correct than the pick-a-row approach used for
    # advanced stats, and only possible because these are counting stats.
    totals = df.groupby(["slug", "name"], as_index=False).agg(
        games_played=("games_played", "sum"),
        minutes_played=("minutes_played", "sum"),
        points=("points", "sum"),
        total_rebounds=("total_rebounds", "sum"),
        assists=("assists", "sum"),
        steals=("steals", "sum"),
        blocks=("blocks", "sum"),
        turnovers=("turnovers", "sum"),
    )

    # Attribute a traded player to whichever team they played the most games
    # for that season - a judgment call, not a rigorously correct answer
    primary_team = (
        df.sort_values("games_played", ascending=False)
        .drop_duplicates(subset=["slug", "name"], keep="first")[["slug", "name", "team"]]
    )
    totals = totals.merge(primary_team, on=["slug", "name"], how="left")

    totals["season"] = season
    totals["pts_per_game"] = totals["points"] / totals["games_played"]
    totals["reb_per_game"] = totals["total_rebounds"] / totals["games_played"]
    totals["ast_per_game"] = totals["assists"] / totals["games_played"]
    totals["stl_per_game"] = totals["steals"] / totals["games_played"]
    totals["blk_per_game"] = totals["blocks"] / totals["games_played"]
    totals["tov_per_game"] = totals["turnovers"] / totals["games_played"]
    totals["min_per_game"] = totals["minutes_played"] / totals["games_played"]

    return totals[[
        "slug", "name", "season", "team", "games_played", "min_per_game",
        "pts_per_game", "reb_per_game", "ast_per_game", "stl_per_game",
        "blk_per_game", "tov_per_game",
    ]]


def pull_old_team_standings(season: str, max_retries: int = 3) -> pd.DataFrame:
    season_end_year = season_to_end_year(season)

    for attempt in range(1, max_retries + 1):
        standings = client.standings(season_end_year=season_end_year)
        df = pd.DataFrame(standings)

        if not df.empty:
            break

        if attempt < max_retries:
            wait = 15 * attempt
            print(f"  Got 0 rows for {season} standings (attempt {attempt}/{max_retries}), "
                  f"waiting {wait}s and retrying...")
            time.sleep(wait)
        else:
            print(f"  WARNING: no Basketball-Reference standings for {season} "
                  f"after {max_retries} attempts")
            return df

    df["team"] = df["team"].apply(lambda t: t.value if t is not None else None)
    df["season"] = season
    df["win_pct"] = df["wins"] / (df["wins"] + df["losses"])

    return df[["team", "season", "wins", "losses", "win_pct"]]


def pull_advanced_stats(season: str, max_retries: int = 3) -> pd.DataFrame:
    season_end_year = season_to_end_year(season)

    for attempt in range(1, max_retries + 1):
        stats = client.players_advanced_season_totals(season_end_year=season_end_year)
        df = pd.DataFrame(stats)

        if not df.empty:
            break

        if attempt < max_retries:
            wait = 15 * attempt
            print(f"  Got 0 rows for {season} (attempt {attempt}/{max_retries}), "
                  f"waiting {wait}s and retrying...")
            time.sleep(wait)
        else:
            print(f"  WARNING: no Basketball-Reference advanced stats for {season} "
                  f"after {max_retries} attempts")
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
        "slug", "name", "season", "team", "positions", "age", "games_played",
        "minutes_played", "player_efficiency_rating", "true_shooting_percentage",
        "usage_percentage", "offensive_win_shares", "defensive_win_shares",
        "win_shares", "win_shares_per_48_minutes", "offensive_box_plus_minus",
        "defensive_box_plus_minus", "box_plus_minus", "value_over_replacement_player",
    ]]


def main():
    all_seasons = []
    all_team_records = []
    all_advanced = []

    for i, season in enumerate(SEASONS, start=1):
        print(f"[{i}/{len(SEASONS)}] Pulling {season} (nba_api player stats)...")
        all_seasons.append(pull_season(season))
        time.sleep(1)

        print(f"[{i}/{len(SEASONS)}] Pulling {season} (nba_api team standings)...")
        all_team_records.append(pull_team_records(season))
        time.sleep(1)

        print(f"[{i}/{len(SEASONS)}] Pulling {season} (Basketball-Reference advanced stats)...")
        all_advanced.append(pull_advanced_stats(season))
        # Bumped from 3s to 8s - the 2008-09 run earlier came back empty even
        # at 3s, so this trades a longer total runtime for fewer silent
        # zero-row seasons on a 30-season run where that risk compounds a lot
        time.sleep(8)

    all_old_basic = []
    all_old_standings = []

    for i, season in enumerate(OLD_SEASONS, start=1):
        print(f"[OLD {i}/{len(OLD_SEASONS)}] Pulling {season} (BR basic stats - full backbone)...")
        all_old_basic.append(pull_old_basic_stats(season))
        time.sleep(8)

        print(f"[OLD {i}/{len(OLD_SEASONS)}] Pulling {season} (BR team standings)...")
        all_old_standings.append(pull_old_team_standings(season))
        time.sleep(8)

        print(f"[OLD {i}/{len(OLD_SEASONS)}] Pulling {season} (BR advanced stats)...")
        all_advanced.append(pull_advanced_stats(season))
        time.sleep(8)

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

    old_basic = pd.concat([df for df in all_old_basic if not df.empty], ignore_index=True)
    old_standings = pd.concat([df for df in all_old_standings if not df.empty], ignore_index=True)

    con = duckdb.connect(DUCKDB_PATH)

    con.execute("CREATE OR REPLACE TABLE raw_player_season_totals AS SELECT * FROM raw")
    print(f"Loaded {len(raw)} rows into raw_player_season_totals")

    con.execute("CREATE OR REPLACE TABLE raw_team_season_records AS SELECT * FROM team_records")
    print(f"Loaded {len(team_records)} rows into raw_team_season_records")

    con.execute("CREATE OR REPLACE TABLE raw_player_advanced_stats AS SELECT * FROM advanced")
    print(f"Loaded {len(advanced)} rows into raw_player_advanced_stats")

    con.execute("CREATE OR REPLACE TABLE raw_player_basic_totals_old AS SELECT * FROM old_basic")
    print(f"Loaded {len(old_basic)} rows into raw_player_basic_totals_old")

    con.execute("CREATE OR REPLACE TABLE raw_team_standings_old AS SELECT * FROM old_standings")
    print(f"Loaded {len(old_standings)} rows into raw_team_standings_old")


if __name__ == "__main__":
    main()
