-- Marts: your df.to_csv('final.csv') moment.
-- All four components are now real. longevity_z is career-level (same
-- value repeated across every one of a player's individual season rows,
-- via the identity map bridging original ID -> canonical ID -> longevity
-- score) - everything else here stays per-season.

select
    c.player_id,
    c.player_name,
    c.season,
    p.peak_z,
    w.winning_z,
    e.era_score,
    l.longevity_z
from {{ ref('int_player_basic_unified') }} c
left join {{ ref('int_player_peak_score') }} p
    on c.player_id = p.player_id
    and c.season = p.season
left join {{ ref('int_player_winning_impact') }} w
    on c.player_id = w.player_id
    and c.season = w.season
left join {{ ref('int_player_era_score') }} e
    on c.player_id = e.player_id
    and c.season = e.season
left join {{ ref('int_player_identity_map') }} m
    on c.player_id = m.player_id
left join {{ ref('int_player_longevity_score') }} l
    on m.canonical_player_id = l.canonical_player_id
order by peak_z desc
