# Fantasy Bot

CLI tool that pulls league data from the Sleeper API, stores it in a local SQLite
database, and prints stats/rankings computed from that data.

## Setup

Clone the repo and set up a virtual environment:

```bash
git clone <repo-url>
cd fantasy-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To leave the virtual environment later, run `deactivate`.

## Usage

All commands are run through `main.py`:

```bash
python3 main.py <command>
```

### Commands

| Command | Description |
| --- | --- |
| `setup` | Pulls users, rosters, matchups (current week), and players from the Sleeper API and imports them into the local SQLite db. Run this first. |
| `update` | Refreshes rosters and matchups from the API. |
| `matchups` | Imports matchups for the current week only. |
| `moves` | Shows the current week's waiver/free agent transactions (adds/drops), with player names resolved from the db. |
| `rankings` | Prints each team's name and power ranking, computed from data already in the db. |
| `weekly_metrics` | Prints the highest scorer, lowest scorer, and closest game for the current week. |
| `status` | Prints the current week and league id. |
| `tests` | Runs the full unit test suite under `tests/`. |

Example:

```bash
python3 main.py setup
python3 main.py rankings
```

Commands that hit the live API (`setup`, `update`, `matchups`, `moves`) require
network access.

## Running tests

```bash
python3 main.py tests
```

or directly with `unittest`:

```bash
python3 -m unittest discover tests -p "*_test.py"
```
