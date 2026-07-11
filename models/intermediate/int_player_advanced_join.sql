-- Intermediate: bring basic box scores and Basketball-Reference's advanced
-- metrics into one row per player-season, across BOTH eras.
--
-- Two different join strategies, because the two eras have fundamentally
-- different ID situations:
--   - Modern (nba_api backbone): no shared ID with Basketball-Reference at
--     all, so this joins on the normalized name + season (see
--     stg_player_season_totals for what the normalization does).
--   - Old-era (Basketball-Reference IS the backbone): both the basic stats
--     and advanced stats come from BR and share BR's own "slug" field - a
--     clean, unambiguous ID join, no fuzzy name matching needed or wanted.
--
-- Left join in both cases so nba_api/BR-basic stays the backbone in each
-- era - a name or slug that doesn't find an advanced-stats match still
-- keeps its row, just with null advanced columns.

with modern as (

    select
        s.player_id,
        s.player_name,
        s.season,
        s.team_id,
        s.games_played,
        s.min_per_game,
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

),

old_era as (

    select
        o.player_id,
        o.player_name,
        o.season,
        cast(null as varchar)      as team_id,
        o.games_played,
        o.min_per_game,
        o.pts_per_game,
        o.reb_per_game,
        o.ast_per_game,
        o.stl_per_game,
        o.blk_per_game,
        o.tov_per_game,
        b.per,
        b.ts_pct,
        b.usg_pct,
        b.win_shares,
        b.ws_per_48,
        b.bpm,
        b.vorp
    from {{ ref('stg_player_basic_totals_old') }} o
    left join {{ ref('stg_player_advanced_stats') }} b
        on o.player_id = b.slug
        and o.season = b.season

)

select * from modern
union all
select * from old_era
