import os

from models.transaction import get_waiver_transactions, get_all_transactions
from models.roster import get_roster, get_drafted_players
from models.weekly_player_performance import get_weekly_player_performance, get_performances_for_players
from models.matchup import get_matchup
from models.player import get_player
from logic.team_metrics import TeamMetricsModule


class PlayerMetricsModule:
    def __init__(self, db, team_id):
        self.db = db
        self.team_id = team_id
        self.roster = get_roster(db, team_id)
        self.team_metrics = TeamMetricsModule(db, team_id)

    def get_drafted_player_points(self, week):
        drafted_players = get_drafted_players(self.db, self.team_id)
        matchup = get_matchup(self.db, self.team_id, week)
        if matchup is None:
            return 0
        drafted_player_points = 0
        for player in drafted_players:
            performance = get_weekly_player_performance(self.db, player, week, os.environ['SEASON'])
            if performance is not None and player in matchup.starters:
                drafted_player_points += performance.stats.get('pts_half_ppr', 0)

        return drafted_player_points

    def get_total_player_points_for_week(self, week):
        matchup = get_matchup(self.db, self.team_id, week)
        if matchup is None:
            return 0
        return matchup.points

    def draft_ability_score(self):
        weeks_in_regular_season = 14
        # points by drafted player / total points -- per week for regular season
        weekly_scores = []
        for week in range(1, weeks_in_regular_season):
            total_points = self.get_total_player_points_for_week(week)
            if not total_points:
                continue
            weekly_scores.append((self.get_drafted_player_points(week) / total_points) * self.player_win_multiplier(week))
        if not weekly_scores:
            return 0
        # we normalize to number of weeks gathered
        return round(sum(weekly_scores) / len(weekly_scores), 1)

    def waiver_and_trades_score(self):
        # points by non-drafted player / total points -- per week
        weeks_in_regular_season = 14
        # points by drafted player / total points -- per week for regular season
        weekly_scores = []
        for week in range(1, weeks_in_regular_season):
            total_points = self.get_total_player_points_for_week(week)
            if not total_points:
                continue
            weekly_scores.append(((total_points - self.get_drafted_player_points(week)) / total_points) * self.player_win_multiplier(week))
        if not weekly_scores:
            return 0
        # we normalize to number of weeks gathered
        points_scored = sum(weekly_scores) / len(weekly_scores)
        transactions = (len(get_waiver_transactions(self.db, self.team_id)) / get_all_transactions(self.db)) * self.player_win_multiplier(week)
        return round((points_scored + transactions), 1)

    def roster_management_score(self):
        manager_scores = 0
        for week in range(1, 14):
            matchup = get_matchup(self.db, self.team_id, week)
            if matchup is None:
                return 0

            performances = get_performances_for_players(self.db, matchup.players, week, os.environ['SEASON'])
            keys = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'FLEX', 'DST', 'K', 'TE']

            starters = {
                'QB': None,
                'RB1': None,
                'RB2': None,
                'WR1': None,
                'WR2': None,
                'TE': None,
                'FLEX': None,
                'DST': None,
                'K': None,
            }
            bench = {
                'QB': None,
                'RB1': None,
                'RB2': None,
                'WR1': None,
                'WR2': None,
                'FLEX': None,
                'TE': None,
                'DST': None,
                'K': None,
            }
            position_to_key = {'DEF': 'DST'}

            for player_id in matchup.players:
                player = get_player(self.db, player_id)
                if player is None or not player.fantasy_positions:
                    continue
                position = player.fantasy_positions[0]
                performance = performances.get(player_id)
                points = performance.stats.get('pts_half_ppr', 0) if performance else 0
                key = position_to_key.get(position, position)
                target = starters if player_id in matchup.starters else bench

                if key == 'RB':
                    slot = 'RB1' if target['RB1'] is None else 'RB2'
                elif key == 'WR':
                    slot = 'WR1' if target['WR1'] is None else 'WR2'
                else:
                    slot = key

                if slot in target and target[slot] is None:
                    target[slot] = points
                else:
                    # collision: no empty spot for this position, so keep whichever
                    # value is larger in the slot and bump the loser to FLEX
                    if slot in target and points > target[slot]:
                        points, target[slot] = target[slot], points
                    target['FLEX'] = max(points, target['FLEX']) if target['FLEX'] is not None else points

            max_value = 0
            starter_value = 0
            for key in keys:
                starter_score = starters[key] if not starters[key] is None else 0
                bench_score = bench[key] if not bench[key] is None else 0
                max_value += max(starter_score, bench_score)
                starter_value += starter_score

            if max_value == 0:
                return 0
            if ((starter_value / max_value)) > .9:
                manager_scores += 1

        return round((manager_scores / 14) * 5, 1)

    def player_win_multiplier(self, week):
        return 10 * self.team_metrics.win_percentage(week)
