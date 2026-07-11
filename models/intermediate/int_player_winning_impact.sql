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
--
-- Sources from the unified basic-stats and team-standings models, so this
-- covers both modern (nba_api) and old-era (Basketball-Reference) rows -
-- team_key differs by source but each row only ever joins against its own
-- source's team table, so the mismatched ID schemes never collide.

with player_composite as (

    select
        c.player_id,
        c.player_name,
        c.season,
        u.team_key,
        c.composite_raw
    from {{ ref('int_player_composite_demo') }} c
    inner join {{ ref('int_player_basic_unified') }} u
        on c.player_id = u.player_id
        and c.season = u.season

),

team_totals as (

    select
        team_key,
        season,
        sum(composite_raw) as team_composite_total
    from player_composite
    group by team_key, season

),

team_records as (

    select
        team_key,
        season,
        win_pct
    from {{ ref('int_team_standings_unified') }}

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
        on p.team_key = t.team_key
        and p.season = t.season
    inner join team_records r
        on p.team_key = r.team_key
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
