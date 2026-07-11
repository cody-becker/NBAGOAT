-- Staging: old-era basic stats. Same shape as stg_player_season_totals,
-- but sourced entirely from Basketball-Reference instead of nba_api, since
-- nba_api has nothing at all before 1996-97.
--
-- player_id here is BR's own "slug" (e.g. "jordami01"), cast to text - the
-- only stable ID BR provides. This does NOT match nba_api's numeric player_id
-- scheme at all, even for a player who spans both eras (Jordan's 1990-91 row
-- and his 1996-97 row will have completely different, unrelated IDs). Fine
-- for ranking individual seasons - each row stands alone - but worth knowing
-- before ever building career-level aggregation, which would need to match
-- by name instead of ID across this boundary.

select
    slug                            as player_id,
    name                            as player_name,
    regexp_replace(
        regexp_replace(
            lower(strip_accents(replace(replace(replace(name, '.', ''), '''', ''), '-', ''))),
            '\s+(jr|sr|ii|iii|iv|v)$', ''
        ),
        '\s[a-z]\s', ' ', 'g'
    )                               as player_name_key,
    season,
    team                            as team_name,
    cast(games_played as integer)   as games_played,
    cast(min_per_game as decimal(5,1)) as min_per_game,
    cast(pts_per_game as decimal(5,1)) as pts_per_game,
    cast(reb_per_game as decimal(5,1)) as reb_per_game,
    cast(ast_per_game as decimal(5,1)) as ast_per_game,
    cast(stl_per_game as decimal(5,1)) as stl_per_game,
    cast(blk_per_game as decimal(5,1)) as blk_per_game,
    cast(tov_per_game as decimal(5,1)) as tov_per_game
from {{ ref('raw_player_basic_totals_old') }}
