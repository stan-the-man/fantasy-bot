import argparse
import os
import sys
import unittest

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
from models.user import import_users
from models.roster import import_rosters, get_rosters
from models.player import get_player, import_players
from models.matchup import import_matchups, count_matchups_for_week, last_week_with_matchups
from logic.stats_module import TeamMetricsModule, MatchMetricsModule, max_points_for

def setup(client, db, args):
    import_users(db, client.get('/users'))
    import_rosters(db, client.get('/rosters'))
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)
    import_players(db, client.getPlayers())


def update(client, db, args):
    import_rosters(db, client.get('/rosters'))
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)


def update_matchups(client, db, args):
    import_matchups(db, client.get('/matchups/' + str(client.week)), client.week)


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

    return parser


COMMANDS = {
    "moves": show_moves,
    "rankings": show_rankings,
    'weekly_metrics': show_paper_metrics,
    "status": status,
    "setup": setup,
    "update": update,
    "matchups": update_matchups,
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

    db = get_connection()
    week_env = os.environ.get('WEEK')
    if week_env:
        week = int(week_env)
        week_source = 'set via WEEK'
    else:
        week = infer_week(get_nfl_state())
        if week is not None:
            week_source = 'inferred from current NFL week'
        else:
            week = last_week_with_matchups(db)
            if week is not None:
                week_source = 'out of season; last week with local data'
            else:
                week = 1
                week_source = 'out of season, no local data; defaulting to 1'

    client = ApiClient(league_id, week)
    client.week_source = week_source
    try:
        COMMANDS[args.command](client, db, args)
    finally:
        db.close()


if __name__ == "__main__":
    main()
