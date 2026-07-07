-- Staging: rename, cast, nothing clever yet.
-- Mirrors stg_player_season_totals — same pattern, different source.

select
    team_id,
    season,
    cast(wins as integer)          as wins,
    cast(losses as integer)        as losses,
    cast(win_pct as decimal(5,3))  as win_pct
from {{ ref('raw_team_season_records') }}
