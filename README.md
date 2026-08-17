# Fantasy Bot

CLI tool that pulls league data from the Sleeper API, stores it in a local SQLite
database, and prints stats/rankings computed from that data.

## Requirements
- python3 (with the `venv` module; on Debian/Ubuntu: `sudo apt install python3-venv`)
- pip

The database is SQLite via Python's built-in `sqlite3` module, so no separate
sqlite3 install is needed. The `sqlite3` CLI is only useful if you want to
inspect the db by hand.

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

Notes:
1. Run `python3 main.py init` to create your `.env`. Enter your Sleeper username
   and pick your league from the list, or paste a league id directly (found in
   the general settings for your league in the Sleeper app, or in the league URL
   on sleeper.com).
2. The current week is inferred automatically from Sleeper's NFL state, so
   there's nothing to update week to week. To pin a specific week (e.g. to
   recompute an old week's metrics), set `WEEK=<n>` in `.env` or on the command
   line: `WEEK=5 python3 main.py rankings`.
3. Only need to run `python3 main.py setup` once. After that use `python3 main.py update`.
4. Sleeper api docs: https://docs.sleeper.com/#introduction
5. For information on how the metrics are calculated, see METRICS.md

All commands are run through `main.py`:

```bash
python3 main.py <command>
```

### Commands

| Command | Description |
| --- | --- |
| `init` | Interactively creates the `.env` file: looks up your leagues by Sleeper username (or takes a league id directly) and saves your choice. |
| `setup` | Pulls users, rosters, matchups (current week), and players from the Sleeper API and imports them into the local SQLite db. Run this only once when first setting things up. |
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

Tests use an old league where I hand-did the math using spreadsheets and manual data entry (thus we can verify the functions work). It has 5 weeks of matchup data stored in it, weeks 1-5.

```bash
python3 main.py tests
```

or directly with `unittest`:

```bash
python3 -m unittest discover tests -p "*_test.py"
```

## Contributing
Email me at `stan@waterfluence.com` if you have feature requests or wish to contribute
