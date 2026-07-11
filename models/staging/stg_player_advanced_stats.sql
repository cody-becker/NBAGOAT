-- Staging: rename, cast, nothing clever yet.
-- Source: Basketball-Reference (via basketball_reference_web_scraper), not nba_api.
-- Join key note: for MODERN seasons (nba_api backbone), this table has no
-- shared ID with nba_api - int_player_advanced_join joins on name + season.
-- For OLD-era seasons (BR is the entire backbone), slug IS a shared, clean
-- ID against stg_player_basic_totals_old - no fuzzy name matching needed
-- there at all, since both sides come from BR and share the same slug.

select
    slug,
    name                                        as player_name,
    regexp_replace(
        regexp_replace(
            lower(strip_accents(replace(replace(replace(name, '.', ''), '''', ''), '-', ''))),
            '\s+(jr|sr|ii|iii|iv|v)$', ''
        ),
        '\s[a-z]\s', ' ', 'g'
    )                                           as player_name_key,
    season,
    team,
    positions,
    cast(age as integer)                        as age,
    cast(games_played as integer)                as games_played,
    cast(minutes_played as integer)              as minutes_played,
    cast(player_efficiency_rating as decimal(6,2)) as per,
    cast(true_shooting_percentage as decimal(5,3)) as ts_pct,
    cast(usage_percentage as decimal(5,3))       as usg_pct,
    cast(offensive_win_shares as decimal(6,2))   as ows,
    cast(defensive_win_shares as decimal(6,2))   as dws,
    cast(win_shares as decimal(6,2))             as win_shares,
    cast(win_shares_per_48_minutes as decimal(6,3)) as ws_per_48,
    cast(offensive_box_plus_minus as decimal(6,2)) as obpm,
    cast(defensive_box_plus_minus as decimal(6,2)) as dbpm,
    cast(box_plus_minus as decimal(6,2))         as bpm,
    cast(value_over_replacement_player as decimal(6,2)) as vorp
from {{ ref('raw_player_advanced_stats') }}
