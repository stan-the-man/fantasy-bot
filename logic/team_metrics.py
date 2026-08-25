from models.roster import get_roster
from models.matchup import get_matchup, get_all_matchups_except_roster_for_week
from models.user import get_user
from logic.season_metrics import max_points_for, point_diff_normalizer


class TeamMetricsModule:
    def __init__(self, db, team_id):
        self.db = db
        self.team_id = team_id
        self.roster = get_roster(db, team_id)
        self.settings = self.roster.settings

    def team_name(self):
        user = get_user(self.db, self.roster.owner_id)
        return user.team_name() + ' ' + user.display_name

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
