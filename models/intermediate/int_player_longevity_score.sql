-- Intermediate: longevity_z - specifically about career DURATION/SUSTAIN,
-- not quality. peak_z/winning_z/era_score already measure "how good" in
-- three different ways (per-minute dominance, team-context contribution,
-- cross-era efficiency) - longevity_z's whole job is to measure something
-- none of them touch: how MANY genuinely elite seasons a player sustained,
-- not how good any single one of them was.
--
-- Reuses prime_season_count directly from int_player_career_scores (the
-- same peak_z >= 1.0 "prime" definition already tested there) - z-scored
-- across every player who has at least one prime season. A player with
-- zero prime seasons has no longevity_z at all - the same honest-NULL
-- pattern as every other component in this pipeline.
--
-- Real, honest caveat: this can only count prime seasons that have already
-- happened. An active player's true eventual longevity is understated until
-- their career actually ends - the same limitation any real "career totals"
-- stat has for someone still playing, not something fixable here.

select
    canonical_player_id,
    player_name,
    prime_season_count,
    (prime_season_count - avg(prime_season_count) over ())
    / stddev(prime_season_count) over ()   as longevity_z
from {{ ref('int_player_career_scores') }}
