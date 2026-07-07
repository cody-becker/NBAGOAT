-- Intermediate: this is your df.groupby().transform() moment, just as SQL.
-- Simplified for this demo into ONE composite metric so you can see the
-- z-score mechanic end to end. In the real project this exact pattern
-- (a window function comparing each player against the full population)
-- gets applied separately to peak, winning impact, era influence, longevity.

with scored as (

    select
        player_id,
        player_name,
        season,
        coalesce(pts_per_game, 0)
            + coalesce(reb_per_game, 0)
            + coalesce(ast_per_game, 0)
            + coalesce(stl_per_game, 0)
            + coalesce(blk_per_game, 0)
            - coalesce(tov_per_game, 0)                as composite_raw
    from {{ ref('stg_player_season_totals') }}

)

select
    player_id,
    player_name,
    season,
    composite_raw,
    (composite_raw - avg(composite_raw) over (partition by season))
    / stddev(composite_raw) over (partition by season)   as composite_z
from scored
