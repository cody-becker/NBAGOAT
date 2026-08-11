NBAGOAT

An all-time NBA "greatest ever" ranking, built as a real ELT data pipeline. It's designed around a simple idea: there's no single objectively correct GOAT list, only a blend of what you personally value. Instead of baking in one fixed answer, the site exposes the actual weights and lets you set them yourself.

Live site: https://nbagoat-gamma.vercel.app/

The idea

Every player's career gets scored across four independent dimensions, each z-scored so they're directly comparable:

Peak dominance (peak_z): how statistically dominant a player was, per minute, during their identified prime seasons
Winning impact (winning_z): what share of their team's total production was theirs, weighted by how much their team actually won
Era influence (era_score): efficiency and impact compared against the entire history of the league, not just their own season
Longevity (longevity_z): how many genuinely elite seasons a player sustained, not just how good their best one was

Drag any of the four sliders on the live site and the whole leaderboard re-ranks instantly. There's no "correct" default: the starting weights are just one opinion among many. Every mix can be shared, too: the URL updates live as you adjust the sliders, and there's a one-click "copy this mix as a link" button, so a specific weighting is always a real, shareable link, not just a private setting on your own screen.

What it actually ranks

This ranks full careers, not individual seasons. A player's peak_z, winning_z, and era_score are each averaged across their identified prime seasons specifically (any season where peak_z >= 1.0), not their whole career and not just their single best year. A player with no season that ever cleared that bar won't appear on the leaderboard at all, even if they had a long, solid career.

Clicking into any player opens a detail view with their full stat breakdown and a short, data-grounded description of what makes their statistical profile distinctive. Those descriptions are generated once, ahead of time, entirely from each player's own computed numbers (never from outside biographical facts an AI model might get wrong), and served as a static file, the same batch-not-live approach as the rest of the site.

Data sources
1996-97 onward: nba_api for box scores and team standings, Basketball-Reference for advanced stats (BPM, True Shooting %, Win Shares)
1973-74 through 1995-96: Basketball-Reference as the entire backbone (basic stats, team standings, and advanced stats), since nba_api has no coverage at all before 1996-97. The floor is 1973-74 specifically because steals and blocks weren't tracked before that, which breaks BPM's formula for earlier eras.
Career-level identity resolution: players whose careers span the 1996-97 boundary exist under two completely different, unrelated ID systems (nba_api's numeric IDs vs. Basketball-Reference's own slugs). These get matched using Splink, a probabilistic record-linkage library, combining name-rarity weighting with career-timeline plausibility, then verified by hand against nba_api's own official career-span data for every case flagged as genuinely ambiguous.
Architecture
nba_api + Basketball-Reference
        │
        ▼
  goatpipeline.py  (ingestion)
        │
        ▼
   DuckDB (raw tables)
        │
        ▼
  dbt (staging → intermediate → marts)
        │
        ├─ career_entity_resolution.py     (one-time: cross-era player matching)
        ├─ generate_all_descriptions.py    (one-time: AI career descriptions)
        │
        ▼
  export_career_scores.py  (serving)
        │
        ▼
  career_scores.json + player_descriptions.json → site/  → Vercel

Deliberately no backend, no database in production: the frontend is a single static HTML file reading two static JSON exports. That's a real, conscious tradeoff: it keeps the whole thing simple and free to host, at the cost of needing a manual re-export/redeploy any time the underlying data changes. There was never a use case here (no accounts, no writes, no scheduled automation) that actually required a backend.

Player descriptions are generated with a local, open-source model (Qwen, via Ollama), not a paid API, so the whole pipeline stays genuinely free to run end to end.

Repo structure
goatpipeline.py                # ingestion: nba_api + Basketball-Reference
export_career_scores.py        # serving: career-level JSON export
career_entity_resolution.py    # one-time: cross-era player ID matching
generate_all_descriptions.py   # one-time: AI-generated career descriptions
models/
  staging/                     # source-conformed, minimal transformation
  intermediate/                # the real business logic lives here
  marts/                       # final, analysis-ready output
seeds/                         # placeholder/fallback data + the career crosswalk
site/                          # the actual deployed static site
debugging/                     # reusable diagnostic scripts
Known, honest limitations
peak_z, winning_z, and era_score all require a Basketball-Reference match. A small number of players (mostly deep-bench/short-career players with unusual or corrupted name data in one source or the other) don't have one, and show up as null rather than a guessed number.
Cross-era player matching relies on name and timeline plausibility. It's been calibrated and spot-checked carefully, but isn't independently verified for every single one of the matched careers, only the ones flagged as genuinely ambiguous.
longevity_z for currently active players will keep changing as their careers continue. It can only count prime seasons that have already happened.
Descriptions are generated by a smaller, local model rather than a larger hosted one, and are deliberately restricted to describing what the numbers say rather than any outside biographical fact, to avoid a model inventing something inaccurate about a real person's career.
Highlight video is not yet built out beyond a handful of manually verified examples. Sourcing it reliably (confirming a video is both the correct player and an actual official upload) turned out to be a real, slow, per-player task, not something easily automated.
There's no unique, directly shareable URL for an individual player's detail view yet, only for a given slider mix on the leaderboard.
Running it locally
powershell
python goatpipeline.py                     # pulls all raw data (~30-45 min)
python -m dbt.cli.main run --profiles-dir .
python career_entity_resolution.py         # only needed if re-matching careers
python generate_all_descriptions.py        # only needed if regenerating descriptions
python export_career_scores.py
copy career_scores.json site\career_scores.json
copy player_descriptions.json site\player_descriptions.json
cd site
python -m http.server 8000
