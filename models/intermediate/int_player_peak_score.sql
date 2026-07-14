-- Intermediate: the REAL peak_z, replacing the naive equal-weighted counting-
-- stat composite that used to live in int_player_composite_demo. That
-- original formula couldn't tell "padding stats" from "winning basketball" -
-- the exact bug that had Karl Malone/Shaq ranked above Jordan's actual real
-- MVP-caliber 1996-97 season, purely because bigs accumulate rebounds more
-- easily than wings accumulate points, and the naive formula weighted every
-- category equally.
--
-- win_shares_per_48 isn't a hand-picked formula - it's Basketball-Reference's
-- own empirically-derived estimate of wins contributed, per 48 minutes
-- played. Using the PER-48 rate (not raw season-total win_shares) keeps this
-- about per-minute dominance, matching the "peak" spirit of the other
-- components - raw win_shares would reward accumulated season-long
-- durability more than per-game brilliance, which is really a longevity
-- question, not a peak one.
--
-- Same games_played * min_per_game >= 500 filter as era_score, for the same
-- reason: this is a RATE stat, so a tiny real sample can swing it to a
-- meaningless extreme - the same Sun Yue/Bruce Bowen/Patrick Baldwin Jr.
-- problem, just in a new column. Reapplying the known fix here instead of
-- waiting to rediscover the same bug from scratch.
--
-- Real gap worth knowing, same as era_score: this only scores players who
-- matched to Basketball-Reference and cleared the minutes bar. Anyone who
-- didn't gets NULL here - an honest gap, not silently papered over.

with peak_inputs as (

    select
        player_id,
        player_name,
        season,
        ws_per_48
    from {{ ref('int_player_advanced_join') }}
    where ws_per_48 is not null
      and (games_played * min_per_game) >= 500

)

select
    player_id,
    player_name,
    season,
    ws_per_48,
    (ws_per_48 - avg(ws_per_48) over (partition by season))
    / stddev(ws_per_48) over (partition by season)   as peak_z
from peak_inputs
