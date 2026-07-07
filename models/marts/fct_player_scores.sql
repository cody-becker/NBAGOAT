-- Marts: your df.to_csv('final.csv') moment.
-- Real version has four real component columns. winning_z is now live;
-- era_score and longevity_z are still placeholders.

select
    c.player_id,
    c.player_name,
    c.season,
    c.composite_z           as peak_z,
    w.winning_z,
    cast(null as decimal)   as era_score,
    cast(null as decimal)   as longevity_z
from {{ ref('int_player_composite_demo') }} c
left join {{ ref('int_player_winning_impact') }} w
    on c.player_id = w.player_id
    and c.season = w.season
order by peak_z desc
