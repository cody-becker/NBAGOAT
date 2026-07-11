-- Intermediate: unify modern (nba_api) and old-era (Basketball-Reference)
-- basic stats into one consistent schema, so peak_z/winning_z can be
-- computed the same way regardless of which source a season came from.
--
-- player_id stays whatever each source's native ID is (nba_api's numeric ID
-- cast to text for modern rows, BR's slug for old-era rows) - these are NOT
-- the same ID system. A player spanning both eras (peak-era Jordan vs. his
-- 1996-97 Bulls year) will have two unrelated IDs here. Fine for ranking
-- individual seasons, since each row stands alone - would need name-based
-- matching instead of ID matching for any future career-level rollup.
--
-- team_key similarly differs by source (nba_api's numeric team_id cast to
-- text, or BR's team name string) - only used to join each row to its own
-- source's team-standings table, never compared across sources.

select
    cast(player_id as varchar)   as player_id,
    player_name,
    player_name_key,
    season,
    cast(team_id as varchar)    as team_key,
    games_played,
    min_per_game,
    pts_per_game,
    reb_per_game,
    ast_per_game,
    stl_per_game,
    blk_per_game,
    tov_per_game
from {{ ref('stg_player_season_totals') }}

union all

select
    player_id,
    player_name,
    player_name_key,
    season,
    team_name                   as team_key,
    games_played,
    min_per_game,
    pts_per_game,
    reb_per_game,
    ast_per_game,
    stl_per_game,
    blk_per_game,
    tov_per_game
from {{ ref('stg_player_basic_totals_old') }}
