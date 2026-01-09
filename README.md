# Swedish Hockey Statistics Scraper

A Python script for collecting and analyzing hockey game statistics from the Swedish Ice Hockey Federation's statistics website (stats.swehockey.se).

## Features

- Scrapes game schedules, lineups, and statistics from swehockey.se
- Tracks player statistics including:
  - Games played
  - Goals and assists
  - Penalty minutes (PIM)
  - Detailed event history
- Exports data to CSV files for further analysis
- Supports any league/tournament with a schedule ID

## Requirements

- Python 3.x
- pandas
- requests
- beautifulsoup4

## Installation

1. Clone or download this repository

2. Install required packages:
```bash
pip install pandas requests beautifulsoup4
```

## Usage

### Basic Usage

Edit the `__main__` section in `get_all_stats.py` to specify the schedule ID(s) you want to scrape:

```python
if __name__ == "__main__":
    # Process schedule and collect statistics
    getAllScheduledGames('19563')  # Replace with your schedule ID

    # Print stats to console
    print_all_stats(player_stats)

    # Write CSV files
    write_player_stats_csv(player_stats, "player_stats.csv")
    write_events_csv(player_stats, "player_events.csv")
```

### Running the Script

```bash
python3 get_all_stats.py
```

### Finding Schedule IDs

Schedule IDs can be found in the URL when viewing a schedule on stats.swehockey.se:
```
https://stats.swehockey.se/ScheduleAndResults/Schedule/19563
                                                          ^^^^^
                                                     Schedule ID
```

## Output Files

The script generates two CSV files:

### 1. player_stats.csv
Player summary statistics with columns:
- `TEAM` - Team name
- `NUMBER` - Player jersey number
- `NAME` - Player name
- `GAMES PLAYED` - Total games played
- `GOALS` - Total goals scored
- `ASSISTS` - Total assists
- `PIM` - Total penalty minutes

### 2. player_events.csv
Detailed event log with columns:
- `DATE` - Game date
- `GROUP` - Tournament/league group
- `TYPE` - Event type (GOAL, ASSIST, PIM)
- `PLAYER NAME` - Player name
- `PLAYER TEAM` - Player's team
- `HOME TEAM` - Home team name
- `AWAY TEAM` - Away team name

## Data Format

Both CSV files use semicolon (`;`) as the delimiter for compatibility with Swedish locale spreadsheet applications.

## Example Workflow

1. **Find your tournament** on stats.swehockey.se
2. **Copy the schedule ID** from the URL
3. **Edit** `get_all_stats.py` and replace the schedule ID
4. **Run** the script: `python3 get_all_stats.py`
5. **Analyze** the generated CSV files in Excel, Google Sheets, or your preferred tool

## Example Schedule IDs

Some example tournament schedule IDs:

```python
# U15 tournaments
getAllScheduledGames('19563')  # U15P DM Röd Grupp 2
getAllScheduledGames('19565')  # U15P DM Blå Grupp 2

# SHL (Swedish Hockey League)
getAllScheduledGames('18263')  # SHL 2024-2025
```

## Debug Mode

Debug output can be controlled via the `DEBUG` variable at the top of the script:
```python
DEBUG = 1  # Enable debug output
DEBUG = 0  # Disable debug output
```

## Notes

- The script processes all completed games (games with results)
- Games without results are automatically skipped
- Team names and player names are normalized to remove extra whitespace
- The script handles Swedish characters (Å, Ä, Ö) correctly

## Troubleshooting

### "Failed to fetch the webpage"
- Check your internet connection
- Verify the schedule ID is correct
- The swehockey.se website may be temporarily unavailable

### "Could not extract match ID"
- The game may not have been played yet
- The game result may not be published yet

### Empty CSV files
- Verify the schedule ID has completed games with results
- Check that the tournament exists and is public

## License

This project is for educational and personal use. Please respect the terms of service of stats.swehockey.se when scraping data.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.
