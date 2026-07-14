-- Intermediate: maps every player_id that exists anywhere in the pipeline to
-- a single "canonical_player_id" - the ID everything about that real human
-- should be grouped under.
--
-- The vast majority of players only ever exist under one ID (either purely
-- modern, or purely old-era with no crosswalk match) - for them,
-- canonical_player_id is just their own player_id, unchanged.
--
-- For the ~400 players in the crosswalk, their OLD-era player_id gets
-- remapped to their MODERN player_id as the canonical one (an arbitrary but
-- consistent choice - modern IDs tend to be the more stable, recognizable
-- ones). This is what actually lets a full career get grouped into one row
-- later, instead of staying split across two disconnected IDs forever.

with all_ids as (

    select distinct player_id
    from {{ ref('int_player_basic_unified') }}

),

crosswalk as (

    select old_player_id, modern_player_id
    from {{ ref('stg_player_career_crosswalk') }}

)

select
    all_ids.player_id,
    coalesce(crosswalk.modern_player_id, all_ids.player_id) as canonical_player_id
from all_ids
left join crosswalk
    on all_ids.player_id = crosswalk.old_player_id
