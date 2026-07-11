-- Intermediate: unify modern (nba_api) and old-era (Basketball-Reference)
-- team standings into one consistent schema - same reasoning as
-- int_player_basic_unified, just for the team-win_pct side.

select
    cast(team_id as varchar) as team_key,
    season,
    win_pct
from {{ ref('stg_team_season_records') }}

union all

select
    team_name as team_key,
    season,
    win_pct
from {{ ref('stg_team_standings_old') }}
