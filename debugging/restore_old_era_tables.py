import duckdb
import pandas as pd
import time

# Reuses the exact same pull logic already in goatpipeline.py - importing
# instead of copy-pasting so there's only ever one real definition of these
from goatpipeline import OLD_SEASONS, pull_old_basic_stats, pull_old_team_standings

DUCKDB_PATH = "goat.duckdb"


def main():
    all_old_basic = []
    all_old_standings = []

    for i, season in enumerate(OLD_SEASONS, start=1):
        print(f"[{i}/{len(OLD_SEASONS)}] Re-pulling {season} (BR basic stats)...")
        all_old_basic.append(pull_old_basic_stats(season))
        time.sleep(8)

        print(f"[{i}/{len(OLD_SEASONS)}] Re-pulling {season} (BR team standings)...")
        all_old_standings.append(pull_old_team_standings(season))
        time.sleep(8)

    old_basic = pd.concat([df for df in all_old_basic if not df.empty], ignore_index=True)
    old_standings = pd.concat([df for df in all_old_standings if not df.empty], ignore_index=True)

    con = duckdb.connect(DUCKDB_PATH)

    con.execute("CREATE OR REPLACE TABLE raw_player_basic_totals_old AS SELECT * FROM old_basic")
    print(f"Restored {len(old_basic)} rows into raw_player_basic_totals_old")

    con.execute("CREATE OR REPLACE TABLE raw_team_standings_old AS SELECT * FROM old_standings")
    print(f"Restored {len(old_standings)} rows into raw_team_standings_old")


if __name__ == "__main__":
    main()
