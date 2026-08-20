from models.roster import get_roster, get_rosters
from models.matchup import (
    get_matchup,
    get_all_matchups_except_roster_for_week,
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


class TeamMetricsModule:
    def __init__(self, db, team_id):
        self.db = db
        self.team_id = team_id
        self.roster = get_roster(db, team_id)
        self.settings = self.roster.settings

    def team_name(self):
        user = get_user(self.db, self.roster.owner_id)
        return user.team_name()

    def power_ranking(self, week):
        return round(self.win_percentage(week) + (self.point_diff() * .25) + (self.points_for_normalized() * .5), 2)

    def effective_wins_and_losses(self, week):
        # weeks are 1 indexed
        total_wins = 0
        total_losses = 0
        for i in range(1, week + 1):
            wins, losses = self.effective_wins_and_losses_for_week(i)
            total_wins += wins
            total_losses += losses
        return total_wins, total_losses

    def effective_wins_and_losses_for_week(self, week):
        my_matchup = get_matchup(self.db, self.team_id, week)
        if my_matchup is None:
            # no data imported for this week; contributes nothing to the record
            return 0, 0
        all_weekly_matches = get_all_matchups_except_roster_for_week(self.db, self.team_id, week)
        wins = 0
        losses = 0
        for opponent in all_weekly_matches:
            if my_matchup.points > opponent.points:
                wins += 1
            else:
                losses += 1
        return wins, losses

    def win_percentage(self, week):
        wins, losses = self.effective_wins_and_losses(week)
        return float(wins / (wins + losses))

    def point_diff(self):
        return float((self.settings['fpts'] - self.settings['fpts_against']) / point_diff_normalizer(self.db))

    def points_for_normalized(self):
        return float(self.settings['fpts'] / max_points_for(self.db))


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
