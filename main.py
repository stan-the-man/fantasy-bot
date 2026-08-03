import argparse

from api_client import ApiClient
from db import get_connection
from models.user import import_users
from models.roster import import_rosters, get_rosters
from models.player import get_player, import_players
from models.matchup import import_matchups
from stats_module import TeamMetricsModule, MatchMetricsModule

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
    for roster in rosters:
        metrics = TeamMetricsModule(db, roster.roster_id)
        print(metrics.team_name() + ': ' + str(metrics.power_ranking()))


def show_paper_metrics(client, db, args):
    metrics = MatchMetricsModule(db, client.week)
    [team, highScore] = metrics.highest_scorer()
    print('Highest scorer: ' + team + ': ' + str(highScore))
    [team, lowScore] = metrics.lowest_scorer()
    print('Lowest scorer: ' + team + ': ' + str(lowScore))
    ((teamA, scoreA), (teamB, scoreB)) = metrics.closest_score()
    print('Closest game: ' + teamA + ' vs ' + teamB + ' point diff: '+ str(round(scoreA - scoreB, 2)))


def status(client, db, args):
    print('week - ' + client.week)
    print('league id -' + client.league_id)


def build_parser():
    parser = argparse.ArgumentParser(description="Fantasy bot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats_parser = subparsers.add_parser("stats", help="Show stats")
    subparsers.add_parser("moves", help="Show moves")
    subparsers.add_parser("rankings", help="Show rankings")
    subparsers.add_parser("setup", help="Set up data")
    subparsers.add_parser("update", help="update roster, matchup, and player data")
    subparsers.add_parser("status", help="Data about current settings")
    subparsers.add_parser("matchups", help="Import matchups for current week")
    subparsers.add_parser("weekly_metrics", help="high, low scorers, closest game for current week")

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

    client = ApiClient(week=1)
    db = get_connection()
    try:
        COMMANDS[args.command](client, db, args)
    finally:
        db.close()


if __name__ == "__main__":
    main()
