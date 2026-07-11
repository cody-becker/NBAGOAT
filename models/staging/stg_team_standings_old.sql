-- Staging: old-era team standings, sourced from Basketball-Reference.
-- Mirrors stg_team_season_records, just keyed on BR's team name string
-- instead of nba_api's numeric team_id, since these seasons never touch
-- nba_api at all.

select
    team                            as team_name,
    season,
    cast(wins as integer)           as wins,
    cast(losses as integer)         as losses,
    cast(win_pct as decimal(5,3))   as win_pct
from {{ ref('raw_team_standings_old') }}
