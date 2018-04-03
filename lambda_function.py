# Code taken from https://gist.github.com/criccomini/3805436
import datetime
import time
from urllib.request import urlopen
import json
import os
#import elementtree.ElementTree as ET
import xml.etree.ElementTree as ET

# e.g. http://scores.nbcsports.msnbc.com/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=MLB&period=20120929
url = 'http://scores.nbcsports.msnbc.com/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=%s&period=%d'

def today(league, gamedate, team):
  yyyymmdd = gamedate
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
      os.environ['TZ'] = 'US/Eastern'
      start = int(time.mktime(time.strptime('%s %d' % (gamestate_tree.get('gametime'), yyyymmdd), '%I:%M %p %Y%m%d')))
      del os.environ['TZ']
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
    print("DEBUG: " + str(e))
  print ("DEBUG: " + json.dumps(games))
  return games

def rssfmt (results):
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
    <title>{game['away']} vs. {game['home']} [ {time.strftime("%I:%M %p %Z", time.localtime(game['start']))}]</title>
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


def lambda_handler(event, context):
  print("DEBUG: Received event: " + json.dumps(event, indent=2))
  try:
    gamedate = int(event['queryStringParameters']['date'])
    print("DEBUG: Looking for games on " + str(gamedate))
  except:
    tzmin8 = datetime.timezone(datetime.timedelta(hours=-8))
    gamedate = int(datetime.datetime.now(tzmin8).strftime("%Y%m%d"))
    print("DEBUG: date not received using default date " + str(gamedate))
  try:
    team = str(event['queryStringParameters']['team'])
    print("DEBUG: Looking for team name " + team)
  except:
    team = 'ALL'
    print("DEBUG: team not received looking for all teams")
  try:
    if event['queryStringParameters']['sport'] in ['NFL', 'MLB', 'NBA', 'NHL']:
      sport = str(event['queryStringParameters']['sport'])
    else:
      sport = "MLB"  
  except:
    sport = "MLB"    
  try:
    output = rssfmt(today(sport, gamedate, team))
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
    "queryStringParameters" : {"date"  : "20180403",
                               "team"  : "Giants",
                               "sport" : "MLB"
     }
  }
  testcontext = "test"
  import pprint
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(lambda_handler(testevent, testcontext))