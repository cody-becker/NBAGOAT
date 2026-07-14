-- Marts: your df.to_csv('final.csv') moment.
-- All four... well, three of four real component columns now use real
-- advanced-stat inputs, not naive counting stats. longevity_z is still a
-- placeholder. peak_z now comes from int_player_peak_score (win_shares_per_48),
-- not int_player_composite_demo, which is now purely internal plumbing for
-- winning_impact's team-share math.

select
    c.player_id,
    c.player_name,
    c.season,
    p.peak_z,
    w.winning_z,
    e.era_score,
    cast(null as decimal)   as longevity_z
from {{ ref('int_player_composite_demo') }} c
left join {{ ref('int_player_peak_score') }} p
    on c.player_id = p.player_id
    and c.season = p.season
left join {{ ref('int_player_winning_impact') }} w
    on c.player_id = w.player_id
    and c.season = w.season
left join {{ ref('int_player_era_score') }} e
    on c.player_id = e.player_id
    and c.season = e.season
order by peak_z desc
