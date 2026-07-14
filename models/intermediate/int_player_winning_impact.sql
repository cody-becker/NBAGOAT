-- Intermediate: winning-impact component.
-- Idea: don't just credit players for being on a winning team (that would
-- score every player on a good roster identically). Credit them in
-- proportion to how much of that team's total production was theirs.
--
-- winning_impact_raw = (player's share of team's total win_shares)
--                       * team win_pct
--
-- Uses real win_shares (Basketball-Reference), not the naive equal-weighted
-- counting-stat sum this model used to rely on via int_player_composite_demo.
-- That naive formula had the EXACT same rebounding-bias problem that made
-- Karl Malone/Shaq look inflated relative to Jordan's real MVP-caliber
-- 1996-97 season - it was fixed for peak_z, but kept quietly powering this
-- model's "team share" concept until now.
--
-- Raw win_shares specifically (not the per-48 rate used for peak_z) is
-- deliberate: this calculation needs a countable quantity that can be
-- meaningfully SUMMED across an entire roster to represent "team total
-- output" - exactly the property a rate stat can't provide, and exactly
-- why peak_z and this model can't just share one column.
--
-- Real, honest tradeoff: this now requires a Basketball-Reference match,
-- same as peak_z and era_score. A player without one loses winning_z too -
-- an accepted gap, not silently papered over.

with player_win_shares as (

    select
        j.player_id,
        j.player_name,
        j.season,
        u.team_key,
        j.win_shares
    from {{ ref('int_player_advanced_join') }} j
    inner join {{ ref('int_player_basic_unified') }} u
        on j.player_id = u.player_id
        and j.season = u.season
    where j.win_shares is not null

),

team_totals as (

    select
        team_key,
        season,
        sum(win_shares) as team_win_shares_total
    from player_win_shares
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
        (p.win_shares / nullif(t.team_win_shares_total, 0))
            * r.win_pct                                        as winning_impact_raw
    from player_win_shares p
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
