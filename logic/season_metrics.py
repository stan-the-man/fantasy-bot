from models.roster import get_roster, get_rosters
from models.matchup import (
    get_top_scoring_matchup,
    get_lowest_scoring_matchup,
    get_closest_scoring_matchup,
)
from models.user import get_user


def max_points_for(db):
    rosters = get_rosters(db)
    return max(roster.settings['fpts'] for roster in rosters)


def min_points_against(db):
    rosters = get_rosters(db)
    return min(roster.settings['fpts_against'] for roster in rosters)


# this is inefficient, i have to calc max every time i call this
# would result in the query happening 12 times if we ran this for
# all teams
def point_diff_normalizer(db):
    return max_points_for(db) - min_points_against(db)


class MatchMetricsModule:
    def __init__(self, db, week):
        self.db = db
        self.week = week

    def highest_scorer(self):
        high_score = get_top_scoring_matchup(self.db, self.week)
        if high_score is None:
            return None
        team = get_roster(self.db, high_score.roster_id)
        player = get_user(self.db, team.owner_id)
        return player.team_name(), high_score.points

    def lowest_scorer(self):
        low_score = get_lowest_scoring_matchup(self.db, self.week)
        if low_score is None:
            return None
        team = get_roster(self.db, low_score.roster_id)
        player = get_user(self.db, team.owner_id)
        return player.team_name(), low_score.points

    def closest_score(self):
        closest = get_closest_scoring_matchup(self.db, self.week)
        if closest is None:
            return None
        team_a = get_roster(self.db, closest['roster_a_id'])
        team_b = get_roster(self.db, closest['roster_b_id'])
        user_a = get_user(self.db, team_a.owner_id)
        user_b = get_user(self.db, team_b.owner_id)
        return (user_a.team_name(), closest['points_a']), (user_b.team_name(), closest['points_b'])
