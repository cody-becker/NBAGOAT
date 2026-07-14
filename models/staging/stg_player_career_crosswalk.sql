-- Staging: the career crosswalk - which old-era player_id and modern-era
-- player_id belong to the same real human. Built via Splink (see
-- career_entity_resolution.py) - every row here has either cleared the
-- calibrated confidence scoring or been manually verified against nba_api's
-- own FROM_YEAR/TO_YEAR record directly. The two confirmed-wrong "Charles
-- Smith" pairings were already excluded before this file was ever written.

select
    old_player_id,
    cast(modern_player_id as varchar)   as modern_player_id,
    cast(match_probability as decimal(6,5)) as match_probability,
    manually_reviewed
from {{ ref('player_career_crosswalk') }}
