-- Intermediate: this model's job has narrowed. composite_raw used to BE
-- peak_z (the naive equal-weighted counting-stat sum, z-scored). It's now
-- purely an internal ingredient for int_player_winning_impact's team-share
-- math, which genuinely needs a countable, summable-across-a-roster
-- quantity - exactly what a rate stat like win_shares_per_48 can't provide.
-- The real peak_z now lives in int_player_peak_score.sql instead.

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
from {{ ref('int_player_basic_unified') }}
