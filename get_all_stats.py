import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import csv

DEBUG = 1

# Initialize an empty stats dictionary
player_stats = {}

# Team name mapping: short name -> full name
team_name_mapping = {}

def normalize_team_name(short_name, full_names):
    """
    Map a short team name (e.g., 'BOO', 'VHF', 'SKE') to its full name.
    Handles abbreviations like SKE -> Skellefteå AIK
    """
    short_name = short_name.strip().upper()

    # Already mapped?
    if short_name in team_name_mapping:
        return team_name_mapping[short_name]

    best_match = None
    best_score = 0

    for full_name in full_names:
        full_upper = full_name.upper()

        # Exact match
        if short_name == full_upper:
            best_match = full_name
            best_score = 1.0
            break

        # Starts with (BOO matches Boo HC)
        if full_upper.startswith(short_name):
            score = 0.95
            if score > best_score:
                best_score = score
                best_match = full_name

        # Check if any word starts with the short name (SKE in Skellefteå AIK)
        words = full_upper.split()
        for word in words:
            if word.startswith(short_name):
                score = 0.9
                if score > best_score:
                    best_score = score
                    best_match = full_name
                break

    if best_match:
        team_name_mapping[short_name] = best_match
        DEBUG == 1 and print(f"Mapped team: '{short_name}' -> '{best_match}'")
        return best_match

    print(f"WARNING: Could not map team '{short_name}'")
    return short_name

def getLineUps(matchid, matchdate, gametext, series):
    home_team, away_team = map(str.strip, gametext.split(" - "))
    parsed_home_team = re.sub(r"\s*\(.*?\)|\s+", " ", home_team).strip()
    parsed_away_team = re.sub(r"\s*\(.*?\)|\s+", " ", away_team).strip()

    # URL of the webpage
    lineUpsUrl = f"https://stats.swehockey.se/Game/LineUps/{matchid}"
    gameEventsUrl = f"https://stats.swehockey.se/Game/Events/{matchid}"
    print('Collects lineup from ' + lineUpsUrl)

    # Send a GET request to fetch the webpage content
    response = requests.get(lineUpsUrl)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        print('Parsings lineup from ' + lineUpsUrl)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all div elements with the class 'lineUpPlayer'
        line_up_players = soup.find_all('div', class_='lineUpPlayer')

        # Loop through the divs and extract the preceding <h3> and format player names
        for player in line_up_players:
            # Find the preceding <h3> for each lineUpPlayer
            team_name = player.find_previous('h3').text.strip()

            # Extract and clean up player text
            raw_player_text = player.text.strip().replace('\n', ' ')

            # Parse the player number, first name, and last name
            try:
                # Split the player text into number and name parts
                number, name = raw_player_text.split('.', 1)
                lastname, firstname = [n.strip() for n in name.split(',', 1)]
                formatted_name = f"{number.strip()},{firstname} {lastname}"
            except ValueError:
                formatted_name = f"Invalid format for player: {raw_player_text}"
            # Parse to remove the part in parentheses and extra spaces
            team_name = re.sub(r"\s*\(.*?\)|\s+", " ", team_name).strip()

            player_name = f"{firstname} {lastname}"
            ensure_player(player_stats, team_name, f"{player_name}", number)
            DEBUG == 1 and print(f"Game played Team: {team_name} Player: {player_name}")
            player_stats[team_name][player_name]["games_played"] += 1
        return parsed_home_team, parsed_away_team
    else:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return (None, None)
   
def ensure_player(stats, team, player_name, number):
    if team not in stats:
        stats[team] = {}
    if player_name not in stats[team]:
        print(f"Adding player to Team: {team} Name: {player_name}")
        stats[team][player_name] = {
            "number": number,
            "goals": 0,
            "assists": 0,
            "pim": 0,
            "games_played": 0,
            "events": []
        }
        
def add_player_goal(stats, team, player_name, number, matchdate, series, home, away, game_id):
    ensure_player(stats, team, player_name, number)

    stats[team][player_name]["goals"] += 1
    DEBUG == 1 and print(f"add_player_goal for {matchdate},{series},{home},{away},{team},{player_name}")

    stats[team][player_name]["events"].append({
        "type": "goal",
        "date": matchdate,
        "series": series,
        "home": home,
        "away": away,
        "game_id": game_id
    })

    return stats
    
def add_player_assist(stats, team, player_name, number, matchdate, series, home, away, game_id):
    ensure_player(stats, team, player_name, number)

    stats[team][player_name]["assists"] += 1
    DEBUG == 1 and print(f"add_player_assist for {matchdate},{series},{home},{away},{team},{player_name}")

    stats[team][player_name]["events"].append({
        "type": "assist",
        "date": matchdate,
        "series": series,
        "home": home,
        "away": away,
        "game_id": game_id
    })

    return stats

def add_player_pim(stats, team, player_name, number, pim, matchdate, series, home, away, game_id):
    ensure_player(stats, team, player_name, number)

    stats[team][player_name]["pim"] += pim
    stats[team][player_name]["events"].append({
        "type": "pim",
        "minutes": pim,
        "date": matchdate,
        "series": series,
        "home": home,
        "away": away,
        "game_id": game_id
    })

    return stats

def getGameStats(game_id, serie, matchdate, gametext):
    home_goals = 0
    away_goals = 0
    home_team, away_team = map(str.strip, gametext.split(" - "))
    parsed_home_team = re.sub(r"\s*\(.*?\)|\s+", " ", home_team).strip()
    parsed_away_team = re.sub(r"\s*\(.*?\)|\s+", " ", away_team).strip()
    DEBUG == 1 and print(f"Processing gamestats for Matchdate: {matchdate} Serie: {serie} Home Team: {parsed_home_team}, Away Team: {parsed_away_team}")

    url = 'http://stats.swehockey.se/Game/Events/' + game_id
    df_gamedata = pd.read_html(url, match='Actions', attrs={'class': 'tblContent'}, displayed_only=False)

    # Get relevant columns, rename and only keep rows with time (length: 5)
    df_gameevents = df_gamedata[1].iloc[:, [0, 1, 2, 3, 4]]

    df_gameevents.columns = ['time', 'event', 'team', 'players', 'on_ice']

    df_gameevents = df_gameevents[df_gameevents['time'].str.len() == 5]
    df_gameevents['game_id'] = game_id

    for _, row in df_gameevents.iloc[::-1].iterrows():
        time = row['time']
        event = row['event']
        team = row['team']
        players_str = row['players']

        # Only process rows that represent goals or assists (e.g., 6-3, 4-2, etc.)
        DEBUG == 1 and print(f"Processing '{event}' {team} {time}: {players_str}")
        if isinstance(event, str) and re.match(r"\d+-\d+.*", event):  # Check if event is a score (e.g., 6-3)
            DEBUG == 1 and print(f"Goal found for {matchdate}  {event} {team} {time}: {players_str}")
            goal_event = event.split(' ')[0]  # Get the score part (e.g., '6-3')
            new_home, new_away = map(int, goal_event.split('-'))
            scoring_team = ""
            # Avgör vilket lag som gjorde målet
            if new_home != home_goals:
                DEBUG == 1 and print(f"Scoring team {parsed_home_team}")
                home_goals = new_home
                scoring_team = parsed_home_team
            elif new_away != away_goals:
                DEBUG == 1 and print(f"Scoring team {parsed_away_team}")
                away_goals = new_away
                scoring_team = parsed_away_team

            players = parse_goal(players_str, matchdate, serie, scoring_team, parsed_home_team, parsed_away_team, game_id)
        elif not pd.isna(event) and re.match(r"(\d+ min)", event):
            match = re.match(r"(\d+) min", event)
            pim = int(match.group(1))
            if pim == 1:
                pim = 2
            DEBUG == 1 and print(f"Penalty found for {matchdate} {event} {team} {time}: {players_str} {match.group(1)}")
            playes = parse_penalty(players_str, matchdate, serie, team, pim, parsed_home_team, parsed_away_team, game_id)


def parse_penalty(player_string, matchdate, serie, team, time, home_team, away_team, game_id):
    # Updated regex to handle special characters including Scandinavian ones like 'ø', 'å', etc.
    # Updated regex to handle accented characters like 'é', 'è', 'ø', etc., and hyphenated last names
    pattern = r"(\d+)\.\s+([A-Za-zÅÄÖåäöÉéèÁáÀàÁáøØüæ'`-]+(?:\s+[A-Za-zÅÄÖåäöÉéèÁáÀàÁáøØüæ'`-]+)*),\s+([A-Za-zÅÄÖåäöÉéèÁáÀàÁáøØü'`-]+)"
    #pattern = r"(\d+)\.\s+([A-Za-zÅÄÖåäöÉéÁáÀàÁáøØ-]+(?:\s+[A-Za-zÅÄÖåäöÉéÁáÀàÁáøØ-]+)*),\s+([A-Za-zÅÄÖåäöÉéÁáÀàÁáøØ]+)"
    match = re.match(pattern, player_string)

    DEBUG == 1 and print(f"Parsing '{player_string}'")

    team_penalty = re.match("Team.*", player_string)
    if team_penalty:
        return

    number = match.group(1)  # Player number, e.g., "18"
    surname = match.group(2)  # Surname, e.g., "Andersson"
    firstname = match.group(3)  # Firstname, e.g., "Henry"

    # Normalize team name to match lineup teams
    normalized_team = normalize_team_name(team, list(player_stats.keys()))

    add_player_pim(player_stats, normalized_team, f"{firstname} {surname}", number, time, matchdate, serie, home_team, away_team, game_id)
    DEBUG == 1 and print(f"Penalty added for Player: Number='{number}', Name='{firstname} {surname}' Team: {normalized_team}")


# Function to process the players_event string
def parse_goal(input_string, matchdate, serie, team, home_team, away_team, game_id):
    # parse_goal expression to match both goal scorer and assist (ensuring no digits in names)
    pattern = r"(\d{1,2})\.\s+([A-Za-zåäöÅÄÖ-]+),\s+([A-Za-zåäöÅÄÖ-]+)"

    # Find all matches
    matches = re.findall(pattern, input_string)
    # Process the matches to assign goal scorer and assist
    if len(matches) >= 1:
        # Normalize team name to match lineup teams
        normalized_team = normalize_team_name(team, list(player_stats.keys()))

        # Goal scorer (first match)
        goal_number, goal_surname, goal_firstname = matches[0]
        add_player_goal(player_stats, normalized_team, f"{goal_firstname} {goal_surname}", goal_number, matchdate, serie, home_team, away_team, game_id)
        DEBUG == 1 and print(f"Date: {matchdate}  Team: {normalized_team} Serie: {serie} Goal Scorer: #{goal_number} '{goal_firstname} {goal_surname}'")

        # Assists (remaining matches)
        for assist in matches[1:]:
            assist_number, assist_surname, assist_firstname = assist
            add_player_assist(player_stats, normalized_team, f"{assist_firstname} {assist_surname}", assist_number, matchdate, serie, home_team, away_team, game_id)
            DEBUG == 1 and print(f"Date: {matchdate} Team: {normalized_team} Serie: {serie} Assist: #{assist_number} '{assist_firstname} {assist_surname}'")
    else:
        print(f"ERROR: Could not parse {input_string}")
      
def getAllScheduledGames(schedule_id):
    """
    Get all games from a schedule ID and process lineups and game statistics
    """
    url = f'http://stats.swehockey.se/ScheduleAndResults/Schedule/{schedule_id}'
    print(f'Collects scheduled games from {url}')
    response = requests.get(url)

    # Find group name from header
    soup = BeautifulSoup(response.text, "html.parser")
    div = soup.select_one("div.d-lg-flex:nth-child(1)")

    if div:
        header_group = div.get_text(strip=True).split(",")[0]
        print(f"Group from header: {header_group}")
    else:
        header_group = None
        print("No matching div found for group header")

    df_games = pd.read_html(response.text, extract_links="all", displayed_only=False)[2]

    # Flatten MultiIndex - handle nested tuples
    flattened_cols = []
    for col in df_games.columns:
        # col is like (('Schedule and Results', None), ('Round', None))
        # We want the last non-None string value
        if isinstance(col, tuple) and len(col) >= 2:
            # Get the second element of the tuple (e.g., ('Round', None))
            inner = col[1]
            if isinstance(inner, tuple) and len(inner) >= 1:
                # Use the first element of the inner tuple ('Round')
                flattened_cols.append(inner[0])
            else:
                flattened_cols.append(str(inner))
        else:
            flattened_cols.append(str(col))
    df_games.columns = flattened_cols

    # Identify columns dynamically
    col_date = [c for c in df_games.columns if "Date" in c][0]

    # Check which column has the match link by looking at first row
    # The column with javascript:openonlinewindow('/Game/Events/...') is the score column
    game_col = [c for c in df_games.columns if "Game" in c][0]
    result_col = [c for c in df_games.columns if "Result" in c][0]
    empty_cols = [c for c in df_games.columns if c == '' or (isinstance(c, str) and c.strip() == '')]

    # Check first row to determine which column has the game link
    first_row = df_games.iloc[0]

    # Helper function to check if value contains game link
    def has_game_link(val):
        if isinstance(val, tuple) and len(val) >= 2 and val[1]:
            return '/Game/Events/' in str(val[1])
        return False

    if has_game_link(first_row[result_col]):
        # U15/Standard structure: Game has matchup, Result has score+link
        col_game = game_col
        col_result = result_col
    elif empty_cols and has_game_link(first_row[empty_cols[0]]):
        # SHL structure: Result has matchup, empty column has score+link
        col_game = result_col
        col_result = empty_cols[0]
    else:
        # Fallback: assume standard structure
        col_game = game_col
        col_result = result_col

    col_venue = [c for c in df_games.columns if "Venue" in c][0]
    col_group = next((c for c in df_games.columns if "Group" in c), None)

    # Build clean dataframe
    clean = pd.DataFrame({
        "date": df_games[col_date],
        "game": df_games[col_game],
        "result": df_games[col_result],
        "venue": df_games[col_venue],
        "group": df_games[col_group] if col_group else header_group
    })

    # Track current date for SHL-style tables where date appears once for multiple games
    current_date = None

    for ind in clean.index:
        # Extract game text and href
        game_val = clean['game'][ind]
        if isinstance(game_val, tuple):
            game_text, game_href = game_val
        else:
            game_text = game_val
            game_href = None
        # Handle date - may be string or tuple
        date_val = clean['date'][ind]
        if isinstance(date_val, tuple):
            date_text = date_val[0]
        else:
            date_text = date_val

        # Check if date_text is a full date or just a time
        # Full date format: "2025-09-13" or "2025-09-13 19:00"
        # Time only format: "19:00" or "15:15"
        if date_text and re.match(r'\d{4}-\d{2}-\d{2}', date_text):
            # This is a full date, extract and save it
            current_date = date_text.split()[0]
        elif date_text and re.match(r'\d{2}:\d{2}', date_text) and current_date:
            # This is just a time, use the last valid date
            date_text = current_date

        result_text, result_href = clean['result'][ind] if isinstance(clean['result'][ind], tuple) else (clean['result'][ind], None)
        # Handle venue - may be string or tuple
        venue_val = clean['venue'][ind]
        if isinstance(venue_val, tuple):
            venue_text, venue_href = venue_val
        else:
            venue_text = venue_val
            venue_href = None

        # Handle group - may be string or tuple
        group_val = clean['group'][ind]
        if isinstance(group_val, tuple):
            group_text, group_href = group_val
        else:
            group_text = group_val
            group_href = None
        DEBUG == 1 and print(f"Date: {date_text} Game: {game_text} Result: {result_text} Venue: {venue_text} Group: {group_text}")

        # Skip if result_href is None
        if result_href is None:
            continue  # Skip this iteration if result_href is None

        # Use a regular expression to extract the number
        match = re.search(r"/Game/Events/(\d+)", result_href)
        if match:
            matchid = match.group(1)
            #game_text, game_href = df_games['game'][ind]
            ## Extract result text and href
            #result_text, result_href = df_games['game'][ind]
            #print(f"Lineup for {df_games['date'][ind][0]} {game_text}")
            matchdate = date_text.split()[0]
            print(f"Retrieving lineups for {matchid} {matchdate} {game_text}")
            (home_team, away_team) = getLineUps(matchid, matchdate, game_text, group_text)
            print(f"Retrieving game stats for {matchid} {matchdate}  {game_text}")
            getGameStats(matchid, group_text, matchdate, game_text)
        else:
            print(f"Could not extract match ID from: {result_href}")



def write_player_stats_csv(stats, filename="player_stats.csv"):
    """
    Write player statistics to CSV file
    Format: TEAM;NUMBER;NAME;GAMES PLAYED;GOALS;ASSISTS;PIM
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        # Write header
        csvwriter.writerow(["TEAM", "NUMBER", "NAME", "GAMES PLAYED", "GOALS", "ASSISTS", "PIM"])

        # Write data rows
        for team, players in stats.items():
            for name, data in players.items():
                csvwriter.writerow([
                    team,
                    data['number'],
                    name,
                    data['games_played'],
                    data['goals'],
                    data['assists'],
                    data['pim']
                ])

    print(f"Player statistics written to {filename}")

def write_events_csv(stats, filename="player_events.csv"):
    """
    Write all player events to CSV file
    Format: DATE;GROUP;TYPE;PLAYER NAME;PLAYER TEAM;HOME TEAM;AWAY TEAM;GAME ID;GAME LINK
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        # Write header
        csvwriter.writerow(["DATE", "GROUP", "TYPE", "PLAYER NAME", "PLAYER TEAM", "HOME TEAM", "AWAY TEAM", "GAME ID", "GAME LINK"])

        # Collect all events with player info
        all_events = []
        for team, players in stats.items():
            for name, data in players.items():
                for event in data['events']:
                    game_id = event.get('game_id', '')
                    game_link = f"https://stats.swehockey.se/Game/Events/{game_id}" if game_id else ""
                    all_events.append({
                        'date': event['date'],
                        'series': event['series'],
                        'type': event['type'].upper(),
                        'home': event['home'],
                        'away': event['away'],
                        'player_name': name,
                        'player_team': team,
                        'minutes': event.get('minutes', ''),
                        'game_id': game_id,
                        'game_link': game_link
                    })

        # Sort by date
        all_events.sort(key=lambda e: e['date'])

        # Write data rows
        for event in all_events:
            event_type = event['type']
            if event_type == 'PIM':
                event_type = f"PIM {event['minutes']}"

            csvwriter.writerow([
                event['date'],
                event['series'],
                event_type,
                event['player_name'],
                event['player_team'],
                event['home'],
                event['away'],
                event['game_id'],
                event['game_link']
            ])

    print(f"Player events written to {filename}")

def print_stats(stats):
    print("\n=== PLAYER STATISTICS ===\n")

    for team, players in stats.items():
        print(f"TEAM: {team}")
        print("-" * (6 + len(team)))

        for name, data in players.items():
            print(f"{data['number']:>2}  {name}")
            print(f"   Games:   {data['games_played']}")
            print(f"   Goals:   {data['goals']}")
            print(f"   Assists: {data['assists']}")
            print(f"   PIM:     {data['pim']}")
            print()

        print()

def print_all_stats(stats):
    print("\n==============================")
    print("      FULL PLAYER STATS")
    print("==============================\n")

    for team, players in stats.items():
        print(f"TEAM: {team}")
        print("=" * (6 + len(team)))

        for name, data in players.items():
            print(f"\n{data['number']:>2}  {name}")
            print(f"   Games Played: {data['games_played']}")
            print(f"   Goals:        {data['goals']}")
            print(f"   Assists:      {data['assists']}")
            print(f"   PIM:          {data['pim']}")
            print("   Events:")

            if not data["events"]:
                print("      (no events recorded)")
                continue

            # Sort events by date if you want chronological order
            events_sorted = sorted(data["events"], key=lambda e: e["date"])

            for e in events_sorted:
                etype = e["type"].upper()
                game_id = e.get('game_id', '')
                game_link = f"https://stats.swehockey.se/Game/Events/{game_id}" if game_id else ""

                if etype == "GOAL":
                    print(f"      {e['date']}  GOAL     vs {e['home']} / {e['away']}  ({e['series']})  [{game_link}]")

                elif etype == "ASSIST":
                    print(f"      {e['date']}  ASSIST   vs {e['home']} / {e['away']}  ({e['series']})  [{game_link}]")

                elif etype == "PIM":
                    print(f"      {e['date']}  PIM {e['minutes']:>2}  vs {e['home']} / {e['away']}  ({e['series']})  [{game_link}]")

                elif etype == "PLAYED":
                    print(f"      {e['date']}  PLAYED   vs {e['home']} / {e['away']}  ({e['series']})  [{game_link}]")

        print("\n")

if __name__ == "__main__":
    # Process schedule and collect statistics
    #getAllScheduledGames('19563')
    # SHL
    getAllScheduledGames('18263')

    # Print stats to console
    print_all_stats(player_stats)

    # Write CSV files
    write_player_stats_csv(player_stats, "player_stats.csv")
    write_events_csv(player_stats, "player_events.csv")

