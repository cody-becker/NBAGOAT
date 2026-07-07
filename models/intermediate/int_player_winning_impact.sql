-- Intermediate: winning-impact component.
-- Idea: don't just credit players for being on a winning team (that would
-- score every player on a good roster identically). Credit them in
-- proportion to how much of that team's total production was theirs.
--
-- winning_impact_raw = (player's share of team's total composite output)
--                       * team win_pct
--
-- This is exactly what's supposed to close the Murray/Young/Davis gap:
-- a ball-dominant guard racking up empty-ish stats on a mediocre team gets
-- a small win_pct multiplier; an efficient star carrying a big share of a
-- winning team's output gets a large one — even at identical raw stats.

with player_composite as (

    select
        c.player_id,
        c.player_name,
        c.season,
        s.team_id,
        c.composite_raw
    from {{ ref('int_player_composite_demo') }} c
    inner join {{ ref('stg_player_season_totals') }} s
        on c.player_id = s.player_id
        and c.season = s.season

),

team_totals as (

    select
        team_id,
        season,
        sum(composite_raw) as team_composite_total
    from player_composite
    group by team_id, season

),

team_records as (

    select
        team_id,
        season,
        win_pct
    from {{ ref('stg_team_season_records') }}

),

winning_raw as (

    select
        p.player_id,
        p.player_name,
        p.season,
        (p.composite_raw / nullif(t.team_composite_total, 0))
            * r.win_pct                                        as winning_impact_raw
    from player_composite p
    inner join team_totals t
        on p.team_id = t.team_id
        and p.season = t.season
    inner join team_records r
        on p.team_id = r.team_id
        and p.season = r.season

)

select
    player_id,
    player_name,
    season,
    winning_impact_raw,
    (winning_impact_raw - avg(winning_impact_raw) over (partition by season))
    / stddev(winning_impact_raw) over (partition by season)   as winning_z
from winning_raw
