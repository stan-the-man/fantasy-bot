# Metrics

Reference for the stats computed in [logic/stats_module.py](logic/stats_module.py).

## Power Ranking

A single composite score blending win percentage, point differential, and points
scored, weighted so record matters most but doesn't tell the whole story:

```
power_ranking = win_percentage + (point_diff * 0.25) + (points_for_normalized * 0.5)
```

Rounded to 2 decimal places. Computed per team, for a given week, via
`TeamMetricsModule.power_ranking(week)`.

## Win Percentage

Not your actual head-to-head record — this is an "effective" record, comparing
your score each week against every other roster's score that week, not just
your scheduled opponent. It answers "how often would this team have won against
a random team that week?" rather than "how often did this team beat the
opponent it happened to be matched against."

```
win_percentage = effective_wins / (effective_wins + effective_losses)
```

Effective wins/losses accumulate across every week from 1 through the given
week. See `TeamMetricsModule.effective_wins_and_losses(week)` and
`win_percentage(week)`.

## Points For (Normalized)

A team's total points scored (`fpts`), scaled to a 0–1 range against the
highest `fpts` total in the league:

```
points_for_normalized = fpts / max(fpts across all rosters)
```

A value of `1.0` means the league's top scorer; lower values mean fewer points
scored relative to the top. See `TeamMetricsModule.points_for_normalized()`.

## Point Diff

Points scored minus points allowed (`fpts - fpts_against`), normalized against
the spread between the league's highest-scoring team and lowest-points-allowed
team:

```
point_diff = (fpts - fpts_against) / (max(fpts across all rosters) - min(fpts_against across all rosters))
```

Positive values indicate a team outscores its opponents on average; negative
values indicate the opposite. See `TeamMetricsModule.point_diff()` and
`point_diff_normalizer(db)`.
