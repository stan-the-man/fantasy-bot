import os

from models.transaction import get_waiver_transactions, get_all_transactions
from models.roster import get_roster, get_rosters, get_drafted_players
from models.weekly_player_performance import get_weekly_player_performance, get_performances_for_players
from models.player import get_player
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
        return 10 * self.win_percentage(week)


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
