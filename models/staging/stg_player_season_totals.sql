-- Staging: rename, cast, nothing clever yet.
-- This is the SQL equivalent of your first pandas cleaning cell.
--
-- player_name_key: a normalized version of the name used ONLY for joining
-- across sources (see int_player_advanced_join). nba_api and Basketball-
-- Reference format names differently in several real, recurring ways:
--   - accents ("Jose Calderon" vs "José Calderón")
--   - initials ("CJ Miles" vs "C.J. Miles")
--   - apostrophes ("Ndiaye" vs "N'diaye")
--   - suffixes ("Jimmy Butler" vs "Jimmy Butler III")
-- This collapses all four so the join isn't fooled by formatting.
-- player_name itself stays untouched for anything user-facing.
--
-- One hardcoded correction: nba_api's raw data has player_id 201180 listed
-- as "Sun Sun" - a known, documented data quality bug in the NBA's own
-- source system (his real name is Sun Yue). Fixed here, in a CTE, BEFORE
-- player_name_key is computed downstream - fixing only the display column
-- wouldn't help the Basketball-Reference join, since player_name_key needs
-- the corrected name to have any chance of matching "Sun Yue" on the BR side.

with corrected as (

    select
        player_id,
        case when player_id = 201180 then 'Sun Yue' else player_name end as player_name,
        season,
        team_id,
        cast(gp as integer)            as games_played,
        cast(mp_pg as decimal(5,1))     as min_per_game,
        cast(pts_pg as decimal(5,1))   as pts_per_game,
        cast(reb_pg as decimal(5,1))   as reb_per_game,
        cast(ast_pg as decimal(5,1))   as ast_per_game,
        cast(stl_pg as decimal(5,1))   as stl_per_game,
        cast(blk_pg as decimal(5,1))   as blk_per_game,
        cast(tov_pg as decimal(5,1))   as tov_per_game
    from {{ ref('raw_player_season_totals') }}

)

select
    player_id,
    player_name,
    regexp_replace(
        regexp_replace(
            lower(strip_accents(replace(replace(replace(player_name, '.', ''), '''', ''), '-', ''))),
            '\s+(jr|sr|ii|iii|iv|v)$', ''
        ),
        '\s[a-z]\s', ' ', 'g'
    )                           as player_name_key,
    season,
    team_id,
    games_played,
    min_per_game,
    pts_per_game,
    reb_per_game,
    ast_per_game,
    stl_per_game,
    blk_per_game,
    tov_per_game
from corrected
