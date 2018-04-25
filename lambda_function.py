# Code taken from https://gist.github.com/criccomini/3805436
import datetime
import time
from urllib.request import urlopen
import json
import os
import xml.etree.ElementTree as ET
import pytz

# e.g. http://scores.nbcsports.msnbc.com/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=MLB&period=20120929
url = 'http://scores.nbcsports.msnbc.com/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=%s&period=%s'

def today(league, yyyymmdd, team):
  games = []
  
  try:
    f = urlopen(url % (league, yyyymmdd))
    print("DEBUG: URL requested: " + f.geturl())
    jsonp = f.read().decode('utf-8')
    f.close()
    json_str = jsonp.replace('shsMSNBCTicker.loadGamesData(', '').replace(');', '')
    json_parsed = json.loads(json_str)
    for game_str in json_parsed.get('games', []):
      game_tree = ET.XML(game_str)
      visiting_tree = game_tree.find('visiting-team')
      home_tree = game_tree.find('home-team')
      gamestate_tree = game_tree.find('gamestate')
      home = home_tree.get('nickname')
      away = visiting_tree.get('nickname')
      # Set TZ because results from url are returned in EST
      tz_est = pytz.timezone('US/Eastern')
      start = tz_est.localize(datetime.datetime.strptime(yyyymmdd + gamestate_tree.get('gametime'), '%Y%m%d%I:%M %p'))
      if (team == 'ALL'):
        games.append({
          'league': league,
          'start': start,
          'home': home,
          'away': away,
          'home-score': home_tree.get('score'),
          'away-score': visiting_tree.get('score'),
          'status': gamestate_tree.get('status'),
          'clock': gamestate_tree.get('display_status1'),
          'clock-section': gamestate_tree.get('display_status2')
        })
      else:
        if team in home or team in away:
          games.append({
          'league': league,
          'start': start,
          'home': home,
          'away': away,
          'home-score': home_tree.get('score'),
          'away-score': visiting_tree.get('score'),
          'status': gamestate_tree.get('status'),
          'clock': gamestate_tree.get('display_status1'),
          'clock-section': gamestate_tree.get('display_status2')
          })
        else:
          continue
  except Exception as e:
    print("ERROR: " + str(e))
  #print ("DEBUG: " + json.dumps(games))
  return games

def rssfmt (results, showtz):
  xml = '''<?xml version="1.0" encoding="UTF-8"?>
  <rss version="2.0">
  <channel>
  <title>Today's Scores</title>
  <description>Todays Sports Scoreboard</description>
  <link>http://www.nbcsports.com/content/scoreboard-central</link>
  <ttl>10</ttl>
  '''
  for game in results:
    xml += f'''
    <item>
    <title>{game['away']} vs. {game['home']} [ {game['start'].astimezone(tz=showtz).strftime("%I:%M %p %Z")} ]</title>
    <description>{game['status']} | {game['clock']} {game['clock-section']}
    {game['away']} [ {game['away-score']} ] - {game['home']} [ {game['home-score']} ]
    </description>
    </item>
    '''
  xml += '''
  </channel>
  </rss>
  '''
  return xml

def validateinput(event):
  sport = ""
  team = ""
  gamedate = ""
  showtz = ""
  try:
    # Using get method to check if exist or set default value
    query_string = event.get('queryStringParameters', {})
    if query_string is None:
      query_string = {}
    tzoffset = query_string.get('tz', 'US/Eastern')
    if tzoffset in pytz.all_timezones:
      showtz = pytz.timezone(tzoffset)
    else:
      showtz = pytz.timezone('US/Eastern')
    gamedate = str(query_string.get('date', datetime.datetime.now(tz=showtz).strftime("%Y%m%d")))
    if gamedate == "":
      gamedate = str(datetime.date.today().strftime("%Y%m%d"))
    team = str(query_string.get('team', 'ALL'))
    sport = str(query_string.get('sport', 'MLB'))
    if sport not in ['NFL', 'MLB', 'NBA', 'NHL']:
      sport = "MLB" 
  except Exception as e:
    print("ERROR: " + str(e))
    return 0
  return (sport, gamedate, team, showtz)  

def lambda_handler(event, context):
  print("DEBUG: Received event: " + json.dumps(event, indent=2))
  try:
    (sport, gamedate, team, showtz) = validateinput(event)
  except Exception as e:
    print("ERROR: " + str(e))
    api_proxy_response = { "statusCode": 400 }
    return api_proxy_response 
  try:
    output = rssfmt(today(sport, gamedate, team), showtz)
    api_proxy_response = { "statusCode": 200,
                           "isBase64Encoded": "false",
                           "headers": {"Access-Control-Allow-Origin": "*",
                           "Content-Type": "application/xml"},
                           "body": output
                         }
  except Exception as e:
    print("ERROR: " + str(e))
    api_proxy_response = { "statusCode": 400 }
  return api_proxy_response


if __name__ == "__main__":
  testevent = {
    "queryStringParameters" : {"date"  : "",
                               "team"  : "Giants",
                               "sport" : "MLB",
                               "tz"    : "US/Pacific"
     }
  }
  testcontext = "test"
  import pprint
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(lambda_handler(testevent, testcontext))