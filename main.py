import argparse
import os
import sys
import unittest

import requests
from dotenv import load_dotenv

from connections.api_client import (
    ApiClient,
    get_nfl_state,
    get_user_info,
    get_user_leagues,
    get_league_info,
    infer_week,
)
from connections.db import get_connection
from logic.team_metrics import TeamMetricsModule
from logic.player_metrics import PlayerMetricsModule
from logic.season_metrics import MatchMetricsModule, max_points_for
from models.user import import_users
from models.roster import import_rosters, get_rosters, get_roster
from models.player import get_player, import_players
from models.matchup import import_matchups, count_matchups_for_week, last_week_with_matchups
from models.matchup import import_matchups
from models.league import import_league
from models.draft_pick import import_draft_picks
from models.transaction import import_transactions, get_transactions
from models.weekly_player_performance import import_weekly_player_performance, get_weekly_player_performance

def import_rostered_player_performances(client, db, rosters):
    rostered_player_ids = {player_id for roster in rosters for player_id in roster.players}
    for player_id in rostered_player_ids:
        if get_weekly_player_performance(db, player_id, client.week, client.season) is not None:
            continue
        performance = client.getWeeklyPlayerPerformance(player_id)
        if performance is not None:
            import_weekly_player_performance(db, performance)


def clear_league_scoped_tables(db):
    # roster_id (and everything keyed off it) is only unique within a single league,
    # so switching leagues without clearing these first pollutes stats with stale ids
    tables = ['leagues', 'users', 'rosters', 'matchups', 'draft_picks', 'transactions']
    for table in tables:
        db.execute(f'DROP TABLE IF EXISTS {table}')
    db.commit()


def setup(client, db, args):
    # each league has a roster id 1 -> 12. So when we run the setup command we need to clear
    # all tables not related to player
    clear_league_scoped_tables(db)
    league = import_league(db, client.get(''))
    import_users(db, client.get('/users'))
    rosters = import_rosters(db, client.get('/rosters'))
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)
    import_draft_picks(db, client.getDraftPicks(league.draft_id))
    import_transactions(db, client.get('/transactions/' + str(client.week)))
    # import_players(db, client.getPlayers())
    # import_rostered_player_performances(client, db, rosters)


def update(client, db, args):
    league = import_league(db, client.get(''))
    rosters = import_rosters(db, client.get('/rosters'))
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)
    import_draft_picks(db, client.getDraftPicks(league.draft_id))
    import_transactions(db, client.get('/transactions/' + str(client.week)))
    import_rostered_player_performances(client, db, rosters)


def update_matchups(client, db, args):
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)


def setup_past_league(client, db, args):
    for week in range(1, 18):
        import_matchups(db, client.get('/matchups/' + str(week)), week)
        import_transactions(db, client.get('/transactions/' + str(week)))
        print('imported week ' + str(week))


def show_moves(client, db, args):
    transactions = client.get('/transactions/' + str(client.week))
    # roster ids
    for transaction in transactions:
        output = ''
        if transaction['drops']:
            output += ' dropped: '
            for drop in transaction['drops'] or []:
                player = get_player(db, drop)
                output += f"{player.first_name} {player.last_name}, " if player else drop
        if transaction['adds']:
            output += ' and added: '
            for add in transaction['adds'] or []:
                player = get_player(db, add)
                output += f"{player.first_name} {player.last_name}, " if player else add

        print(transaction['type'] + ': ' + transaction['status'] + output)
        for budget in transaction['waiver_budget'] or []:
            print(budget)
    pass


def trades(client, db, args):
    transactions = get_transactions(db)
    for transaction in transactions:
        if transaction.type != 'trade':
            continue

        roster_ids = transaction.roster_ids
        team_names = {
            roster_id: TeamMetricsModule(db, roster_id).team_name()
            for roster_id in roster_ids
            if get_roster(db, roster_id) is not None
        }

        def player_name(player_id):
            player = get_player(db, player_id)
            return f"{player.first_name} {player.last_name}" if player else player_id

        # group each traded player under the roster that gave it up
        players_given_by_roster = {roster_id: [] for roster_id in roster_ids}
        if transaction.drops:
            for player_id, giving_roster_id in transaction.drops.items():
                players_given_by_roster.setdefault(giving_roster_id, []).append(player_name(player_id))
        elif transaction.adds and len(roster_ids) == 2:
            for player_id, receiving_roster_id in transaction.adds.items():
                giving_roster_id = next((r for r in roster_ids if r != receiving_roster_id), None)
                if giving_roster_id is not None:
                    players_given_by_roster.setdefault(giving_roster_id, []).append(player_name(player_id))

        if len(roster_ids) == 2 and any(players_given_by_roster.values()):
            roster_a, roster_b = roster_ids
            name_a = team_names.get(roster_a, str(roster_a))
            name_b = team_names.get(roster_b, str(roster_b))
            players_a = ', '.join(players_given_by_roster.get(roster_a, [])) or 'nothing'
            players_b = ', '.join(players_given_by_roster.get(roster_b, [])) or 'nothing'
            print(f"{name_a} trades: {players_a} to {name_b} for: {players_b}")
        else:
            # more than two rosters involved, or no add/drop data to attribute a side to
            player_ids = set(transaction.adds.keys()) | set(transaction.drops.keys())
            if not player_ids:
                player_ids = set(transaction.metadata.keys())
            players = ', '.join(player_name(player_id) for player_id in player_ids)
            print(' <-> '.join(team_names.values()) + ': ' + players)


def show_rankings(client, db, args):
    rosters = get_rosters(db)
    if not rosters:
        print("No rosters imported yet. Run 'python3 main.py setup' first.")
        return
    if count_matchups_for_week(db, client.week) == 0 or max_points_for(db) == 0:
        print(f"No scored games for week {client.week} yet. Run 'python3 main.py update' once games have been played.")
        return
    for roster in rosters:
        metrics = TeamMetricsModule(db, roster.roster_id)
        print(metrics.team_name() + ': ' + str(metrics.power_ranking(client.week)))


def show_paper_metrics(client, db, args):
    metrics = MatchMetricsModule(db, client.week)
    if count_matchups_for_week(db, client.week) == 0:
        print(f"No matchup data for week {client.week} yet. Run 'python3 main.py update' once games have been played.")
        return
    [team, highScore] = metrics.highest_scorer()
    print('Highest scorer: ' + team + ': ' + str(highScore))
    [team, lowScore] = metrics.lowest_scorer()
    print('Lowest scorer: ' + team + ': ' + str(lowScore))
    ((teamA, scoreA), (teamB, scoreB)) = metrics.closest_score()
    print('Closest game: ' + teamA + ' vs ' + teamB + ' point diff: '+ str(round(scoreA - scoreB, 2)))

def player_profile_stats(client, db, args):
    rosters = get_rosters(db)
    for roster in rosters:
        metrics = TeamMetricsModule(db, roster.roster_id)
        player_metrics = PlayerMetricsModule(db, roster.roster_id)
        print("Name: " + metrics.team_name())
        print("Draft Ability: " + str(player_metrics.draft_ability_score()))
        print("Roster Management: " + str(player_metrics.roster_management_score()))
        print("Waiver And Trades: " + str(player_metrics.waiver_and_trades_score()))


def status(client, db, args):
    print(f"week - {client.week} ({getattr(client, 'week_source', 'unknown')})")
    print('league id - ' + client.league_id)


def run_tests():
    suite = unittest.TestLoader().discover(start_dir="tests", pattern="*_test.py")
    unittest.TextTestRunner(verbosity=2).run(suite)


def _existing_week_override():
    if not os.path.exists('.env'):
        return None
    with open('.env') as f:
        for line in f:
            if line.strip().startswith('WEEK='):
                return line.strip().split('=', 1)[1]
    return None


def _pick_league(username):
    user = get_user_info(username)
    state = get_nfl_state()
    season = state.get('league_season') or state.get('season')
    leagues = get_user_leagues(user['user_id'], season)
    if not leagues:
        season = str(int(season) - 1)
        leagues = get_user_leagues(user['user_id'], season)
    if not leagues:
        print(f"No NFL leagues found for user '{username}'.")
        sys.exit(1)
    if len(leagues) == 1:
        return leagues[0]['league_id']
    for i, league in enumerate(leagues, 1):
        print(f"{i}. {league['name']} ({league['season']}, id {league['league_id']})")
    choice = int(input('Pick a league (number): '))
    return leagues[choice - 1]['league_id']


def run_init():
    load_dotenv()
    existing_league = os.environ.get('LEAGUE_ID')
    week_override = _existing_week_override()

    hint = f" (enter to keep {existing_league})" if existing_league else ""
    entered = input(f"Sleeper username or league ID{hint}: ").strip()

    if not entered and existing_league:
        league_id = existing_league
    elif entered.isdigit():
        league_id = entered
    elif entered:
        league_id = _pick_league(entered)
    else:
        print('Nothing entered and no existing .env to keep.')
        sys.exit(1)

    league = get_league_info(league_id)
    lines = [f"LEAGUE_ID={league_id}"]
    if week_override:
        lines.append(f"WEEK={week_override}")
    else:
        lines.append('# WEEK is inferred from the current NFL week; uncomment to override.')
        lines.append('# WEEK=1')
    with open('.env', 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"Wrote .env for league '{league['name']}' ({league_id}, {league['season']} season)")


def build_parser():
    parser = argparse.ArgumentParser(description="Fantasy bot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Interactively create the .env file (league lookup by Sleeper username)")
    subparsers.add_parser("moves", help="Show moves")
    subparsers.add_parser("rankings", help="Show rankings")
    subparsers.add_parser("setup", help="Set up data")
    subparsers.add_parser("update", help="update roster, matchup, and player data")
    subparsers.add_parser("status", help="Data about current settings")
    subparsers.add_parser("matchups", help="Import matchups for current week")
    subparsers.add_parser("weekly_metrics", help="high, low scorers, closest game for current week")
    subparsers.add_parser("tests", help="Run all unit tests")
    subparsers.add_parser("players", help="Get roster season stats")
    subparsers.add_parser("trades", help="List all trade transactions")
    subparsers.add_parser("setup_past_league", help="Import matchups and transactions for weeks 1-17")

    return parser


COMMANDS = {
    "moves": show_moves,
    "rankings": show_rankings,
    'weekly_metrics': show_paper_metrics,
    "status": status,
    "setup": setup,
    "update": update,
    "matchups": update_matchups,
    "tests": run_tests,
    "players": player_profile_stats,
    "trades": trades,
    "setup_past_league": setup_past_league,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == 'init':
        run_init()
        return
    if args.command == 'tests':
        run_tests()
        return

    load_dotenv()
    league_id = os.environ.get('LEAGUE_ID')
    if not league_id:
        print("LEAGUE_ID is not set. Run 'python3 main.py init' to create a .env file.")
        sys.exit(1)

    league_id = os.environ['LEAGUE_ID']
    week = int(os.environ['WEEK'])
    season = os.environ['SEASON']
    week_env = os.environ.get('WEEK')

    client = ApiClient(league_id, week, season)
    db = get_connection()
    if week_env:
        week = int(week_env)
        week_source = 'set via WEEK'
    else:
        try:
            week = infer_week(get_nfl_state())
            reason = 'out of season'
        except requests.RequestException:
            week = None
            reason = 'Sleeper unreachable'
        if week is not None:
            week_source = 'inferred from current NFL week'
        else:
            week = last_week_with_matchups(db)
            if week is not None:
                week_source = f'{reason}; last week with local data'
            else:
                week = 1
                week_source = f'{reason}, no local data; defaulting to 1'

    client = ApiClient(league_id, week)
    client.week_source = week_source
    try:
        COMMANDS[args.command](client, db, args)
    finally:
        db.close()


if __name__ == "__main__":
    main()
