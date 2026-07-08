-- Intermediate: era-influence component.
--
-- This is the one model in the whole pipeline that deliberately does NOT use
-- `partition by season`. peak_z and winning_z both compare a player only to
-- their own season's population, which is exactly what makes those two
-- era-neutral - but it also means neither one can ever capture "how good
-- were you compared to the whole history of the league," which is the
-- actual point of era_score.
--
-- Instead of raw counting stats (which inflate/deflate with a whole era's
-- pace, independent of individual skill), this uses two stats that were
-- built to already be pace/possession-adjusted at the source:
--   - bpm: points per 100 possessions vs. league average - a rate stat,
--     not a per-game count, so a fast era and a slow era aren't comparing
--     apples to oranges the way raw pts/reb/ast would.
--   - ts_pct: true shooting % - folds 2s/3s/FTs into one shot-value-adjusted
--     efficiency number, also pace-independent.
--
-- Real gap worth knowing: this can only score players who matched to
-- Basketball-Reference (see int_player_advanced_join) and only for seasons
-- BR data has been pulled for. Anyone unmatched, or from a season not yet
-- ingested, gets NULL here - that's an honest gap, not silently papered over.
--
-- games_played >= 20 filter: BPM/PER are RATE stats - with a tiny sample
-- (a few games, a handful of minutes), one bad possession swings the rate
-- wildly and produces numbers that look extreme but mean nothing (checked
-- the real data: a 2-game sample producing a -42.6 BPM, a 1-game sample
-- producing +97.4). Left unfiltered, these outliers don't just make their
-- own row meaningless - they drag the population mean/stddev used to
-- z-score EVERYONE, since there's no partition here. 20 games is a
-- judgment call, not a rigorously derived cutoff - adjust if you want.

with era_inputs as (

    select
        player_id,
        player_name,
        season,
        bpm,
        ts_pct
    from {{ ref('int_player_advanced_join') }}
    where bpm is not null
      and ts_pct is not null
      and games_played >= 20

),

era_z as (

    select
        player_id,
        player_name,
        season,
        (bpm - avg(bpm) over ()) / stddev(bpm) over ()             as bpm_z,
        (ts_pct - avg(ts_pct) over ()) / stddev(ts_pct) over ()     as ts_pct_z
    from era_inputs

)

select
    player_id,
    player_name,
    season,
    (bpm_z + ts_pct_z) / 2   as era_score
from era_z
