import duckdb
from basketball_reference_web_scraper import client

# Pull real 1961-62 advanced stats directly from Basketball-Reference
print("Pulling 1961-62 advanced stats from Basketball-Reference...")
stats_1962 = client.players_advanced_season_totals(season_end_year=1962)
print(f"Got {len(stats_1962)} player-seasons for 1961-62")
print()

# A few stars from that season, for context beyond just Wilt
names_of_interest = ["Wilt Chamberlain", "Bill Russell", "Oscar Robertson", "Elgin Baylor"]
for p in stats_1962:
    if p["name"] in names_of_interest:
        print(f"{p['name']:20} games={p['games_played']:3}  "
              f"bpm={p['box_plus_minus']:6}  ts_pct={p['true_shooting_percentage']}")
print()

# Now compare against the CURRENT era_score population already in your pipeline
# (this is the same games_played >= 20 filtered population int_player_era_score uses)
con = duckdb.connect("goat.duckdb")
current_pop = con.execute("""
    select bpm, ts_pct
    from int_player_advanced_join
    where bpm is not null and ts_pct is not null and games_played >= 20
""").df()

bpm_mean, bpm_std = current_pop["bpm"].mean(), current_pop["bpm"].std()
ts_mean, ts_std = current_pop["ts_pct"].mean(), current_pop["ts_pct"].std()

print(f"Current population (1996-97/2008-09/2021-22, n={len(current_pop)}):")
print(f"  bpm    mean={bpm_mean:.2f}  std={bpm_std:.2f}")
print(f"  ts_pct mean={ts_mean:.3f}  std={ts_std:.3f}")
print()

# Where would Wilt's actual 1961-62 numbers land using TODAY's z-score baseline?
wilt = next(p for p in stats_1962 if p["name"] == "Wilt Chamberlain")
wilt_bpm_z = (wilt["box_plus_minus"] - bpm_mean) / bpm_std
wilt_ts_z = (wilt["true_shooting_percentage"] - ts_mean) / ts_std
wilt_era_score = (wilt_bpm_z + wilt_ts_z) / 2

print(f"Wilt Chamberlain 1961-62, scored against the MODERN population baseline:")
print(f"  bpm={wilt['box_plus_minus']} -> z={wilt_bpm_z:.2f}")
print(f"  ts_pct={wilt['true_shooting_percentage']} -> z={wilt_ts_z:.2f}")
print(f"  era_score={wilt_era_score:.2f}")