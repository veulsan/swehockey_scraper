# Copilot / AI Agent Instructions for swehockey_scraper

This repository is a small, single-purpose scraper that collects game events from stats.swehockey.se and writes a CSV of player stats. Keep edits minimal and focused: the code is primarily a single-file procedural script (see `get_all_stats.py`).

- **Big picture:** `get_all_stats.py` fetches schedule pages and per-game event pages from `stats.swehockey.se`, parses tables with `pandas.read_html`, extracts lineups and events with BeautifulSoup and regexes, and accumulates per-player stats in the global `player_stats` dict. Final output is written to `all_stats2.csv`.

- **Key files:**
  - [get_all_stats.py](get_all_stats.py) — main script and canonical examples of project patterns.
  - `.claude/settings.local.json` — local agent settings (may contain secrets). Do not commit secrets.

- **How to run (examples):**
  - Activate the project's virtualenv (if present): `source .venv/bin/activate` then `python get_all_stats.py`
  - Or run directly with the venv Python: `./.venv/bin/python get_all_stats.py`
  - The script calls `getAllScheduledGamesNew('19565')` / `getAllScheduledGames('19565')` by default; change schedule IDs in `main()` to target other competitions.

- **Dependencies:** code uses `numpy`, `pandas`, `requests`, `beautifulsoup4`. If a `requirements.txt` is added, install with `pip install -r requirements.txt`.

- **Project-specific patterns & conventions:**
  - Single-file procedural style: functions operate on the global `player_stats` dict; prefer small, focused edits over large refactors unless you update callers.
  - Regex-heavy parsing: `parse_goal()` and `parse_penalty()` use regex tuned for Scandinavian characters. Preserve those character classes when modifying parsing.
  - Table reads assume the target HTML table is at index `2` in `pd.read_html(...)` — if the site layout changes, inspect the raw HTML and adapt selection logic (see `getAllScheduledGamesNew`).
  - Debug toggles: `DEBUG = 1` prints verbose parsing information. Set to `0` to silence.

- **Network & scraping notes:**
  - All HTTP targets are `stats.swehockey.se`. Tests and dry-runs should avoid hammering the site — add sleeps or rate limiting when iterating many schedule IDs.
  - `pandas.read_html` is used extensively; it can fail/change behavior if the site updates. Where possible prefer `requests` + `BeautifulSoup` for robust selection when updating.

- **Editing guidance for agents:**
  - When changing output columns or CSV name (`all_stats2.csv`), update `main()` and any callers that expect the existing columns.
  - Keep function signatures stable: many functions are called by name strings (e.g., `getAllScheduledGamesNew`) — avoid renaming without updating all references.
  - Preserve parsing regexes that include accented/Scandinavian characters (ÅÄÖåäö etc.).

- **Tests & debugging:**
  - No unit tests exist; run the script against a single schedule ID to validate behavior before broader runs.
  - Use `DEBUG = 1` to trace parsing. For faster iteration, mock network calls or save sample HTML locally and call parsing functions against it.

- **Security & secrets:**
  - There is a `.claude/settings.local.json` file in the workspace. Treat local config files as potentially sensitive and avoid printing them.

If anything here is unclear or you want the instructions tailored to a different agent persona (unit-test writer, refactorer, or bug fixer), tell me which focus you prefer and I will iterate.
