NBA GOAT Pipeline

⚠️ Huge work in progress. Most of this doesn't work yet, half the models are placeholders, and the structure will probably change a lot before this is "done." Building in public, mistakes and all.

What this actually is:

An attempt to rank NBA players without pretending there's one "correct" GOAT list. Instead of a single made-up composite score, players get scored on four separate categories, and the weighting between them is meant to be adjustable, not fixed by me. The plan is a live site where you can drag sliders and watch the ranking re-sort in real time.

The four categories (weights are my current default, not gospel):


Peak dominance — 0.35
Winning impact — 0.30
Era influence — 0.20
Longevity/consistency — 0.15


Current status


✅ Player box score stats pulled via nba_api (1996-97 onward)
✅ Team win-loss records pulled via nba_api
✅ dbt pipeline: staging → intermediate → marts, running locally on DuckDB
✅ peak_z — raw production, z-scored per season
✅ winning_z — player's share of team production × team win%, z-scored per season
🚧 era_score — not started
🚧 longevity_z — not started
🚧 Basketball-Reference integration — for advanced metrics (PER/BPM/VORP/Win Shares) and anything pre-1996-97, since nba_api doesn't go back further
❌ Supabase — not connected yet, everything's local DuckDB
❌ Frontend — doesn't exist yet, just SQL and a duckdb file right now


Stack (planned end state)

nba_api + Basketball-Reference → Supabase (Postgres) → dbt → Next.js / Vercel

Right now it's just: nba_api → local DuckDB → dbt.

Known unsolved problems


- The raw stat composite weights every stat equally (pts = reb = ast = stl = blk = 1.0) — naive, will probably get replaced by real advanced metrics later
- No shared player ID between nba_api and Basketball-Reference — cross-source joins happen on name + season, which has real edge cases (traded players, suffixes, name collisions)
- Pre-1996-97 seasons need Basketball-Reference entirely (nba_api returns nothing that far back)


Why bother

Most "GOAT ranking" content pretends objectivity that doesn't exist. This is an attempt to make the subjectivity explicit and adjustable instead of hiding it behind a single fake number.


Expect this README, the models, and honestly the whole repo structure to look pretty different a month from now.
