-- Staging: rename, cast, nothing clever yet.
-- This is the SQL equivalent of your first pandas cleaning cell.

select
    player_id,
    player_name,
    season,
    team_id,
    cast(gp as integer)            as games_played,
    cast(pts_pg as decimal(5,1))   as pts_per_game,
    cast(reb_pg as decimal(5,1))   as reb_per_game,
    cast(ast_pg as decimal(5,1))   as ast_per_game,
    cast(stl_pg as decimal(5,1))   as stl_per_game,
    cast(blk_pg as decimal(5,1))   as blk_per_game,
    cast(tov_pg as decimal(5,1))   as tov_per_game
from {{ ref('raw_player_season_totals') }}
