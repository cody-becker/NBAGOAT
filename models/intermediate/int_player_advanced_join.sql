-- Intermediate: bring nba_api's basic box scores and Basketball-Reference's
-- advanced metrics into one row per player-season.
--
-- No shared player ID between the two sources, so this joins on name + season -
-- specifically the normalized player_name_key, not the raw player_name, since
-- the two sources format accented names and initials differently (see
-- stg_player_season_totals for what the normalization does).
--
-- Left join on purpose: nba_api stays the backbone (per the "fill gaps, don't
-- replace" decision) - every player from nba_api should survive this join even
-- if a name still doesn't match after normalization, and the advanced columns
-- come back null. Those remaining nulls are a signal to go investigate a
-- specific player by hand, not something to silently coalesce away here.

select
    s.player_id,
    s.player_name,
    s.season,
    s.team_id,
    s.games_played,
    s.pts_per_game,
    s.reb_per_game,
    s.ast_per_game,
    s.stl_per_game,
    s.blk_per_game,
    s.tov_per_game,
    b.per,
    b.ts_pct,
    b.usg_pct,
    b.win_shares,
    b.ws_per_48,
    b.bpm,
    b.vorp
from {{ ref('stg_player_season_totals') }} s
left join {{ ref('stg_player_advanced_stats') }} b
    on s.player_name_key = b.player_name_key
    and s.season = b.season
