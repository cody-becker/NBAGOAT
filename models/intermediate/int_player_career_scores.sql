-- Intermediate: career-level scores, averaged across a player's identified
-- "prime" seasons - not their whole career (dilutes true peaks with decline
-- years) and not just their single best season (ignores sustained
-- excellence entirely).
--
-- "Prime" = peak_z >= 1.0 - a season at least one full standard deviation
-- above that year's average, not just "better than average." A judgment
-- call, same category as the 500-minute and 20-game thresholds elsewhere
-- in this project - not a derived constant, just a defensible line.
--
-- Uses peak_z specifically (not a blend of all three components) to define
-- ONE coherent "these were their peak years" window per player. winning_z
-- and era_score then get averaged WITHIN that same window, not against
-- their own separate thresholds - otherwise each component could select a
-- different set of seasons, and "prime" would stop meaning one consistent
-- period in a player's career.
--
-- Real, accepted scope limit: a player with zero peak_z >= 1.0 seasons
-- simply has no row here at all - an honest absence, not a fake number.
-- True journeymen/role players still exist in fct_player_scores per-season,
-- just not in this career-level view.

with player_seasons as (

    -- Sources the three components directly from their own intermediate
    -- models, NOT from fct_player_scores - this table now feeds
    -- longevity_z, which fct_player_scores itself needs, so going through
    -- the fully-assembled marts table here would create a real circular
    -- dependency (dbt correctly refuses to build a cycle). Same underlying
    -- data either way - fct_player_scores never does anything beyond
    -- joining these same three models together.

    select
        u.player_id,
        u.player_name,
        u.season,
        p.peak_z,
        w.winning_z,
        e.era_score
    from {{ ref('int_player_basic_unified') }} u
    left join {{ ref('int_player_peak_score') }} p
        on u.player_id = p.player_id and u.season = p.season
    left join {{ ref('int_player_winning_impact') }} w
        on u.player_id = w.player_id and u.season = w.season
    left join {{ ref('int_player_era_score') }} e
        on u.player_id = e.player_id and u.season = e.season

),

player_seasons_mapped as (

    select
        m.canonical_player_id,
        s.player_id,
        s.player_name,
        s.season,
        s.peak_z,
        s.winning_z,
        s.era_score
    from player_seasons s
    inner join {{ ref('int_player_identity_map') }} m
        on s.player_id = m.player_id

),

prime_seasons as (

    select *
    from player_seasons_mapped
    where peak_z >= 1.0

),

career_names as (

    -- Whichever row's OWN player_id matches the canonical ID - for a
    -- cross-era-linked player, that's specifically their modern-era row
    select distinct canonical_player_id, player_name
    from player_seasons_mapped
    where player_id = canonical_player_id

)

select
    p.canonical_player_id,
    n.player_name,
    count(*)          as prime_season_count,
    min(p.season)     as prime_span_start,
    max(p.season)     as prime_span_end,
    avg(p.peak_z)     as career_peak_z,
    avg(p.winning_z)  as career_winning_z,
    avg(p.era_score)  as career_era_score
from prime_seasons p
left join career_names n
    on p.canonical_player_id = n.canonical_player_id
group by p.canonical_player_id, n.player_name
