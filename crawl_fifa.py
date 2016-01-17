import requests
import json
import re
import time
import os
from bs4 import BeautifulSoup

root_url = 'http://www.futhead.com/16/players/$ID'
root_price_url = 'http://www.futhead.com/16/players/$ID/prices/all/'
SUCCESS='SUCCESS'
NOT_PLAYER_ID='NOT_PLAYER_ID'
SKIPPED_FOR_ATTRIBUTE='SKIPPED_FOR_ATTRIBUTE'
date_string = time.strftime("%Y%m%d")
cache_path = date_string + '.cache'

def load_from_cache():
  if not os.path.isfile(cache_path):
    return 0, None
  with open (cache_path, 'r') as read_cache:
    existing_players = json.loads(read_cache.read())
    max_key = existing_players['current_id']
    existing_players.pop('current_id', None)
    return max_key, existing_players

def save_to_cache(current_id, all_players):
  all_players['current_id'] = current_id
  with open (cache_path, 'w') as write_to_cache:
    write_to_cache.write(json.dumps(all_players, sort_keys=True, indent=4))

def crawl_player(player_id, all_players):
  url = root_url.replace('$ID', str(player_id))
  res = requests.get(url)
  if res.status_code != 200:
    print 'Player ' + str(player_id) + ' failed with ' + str(res.status_code)
    return NOT_PLAYER_ID
    # print res.text.encode('utf-8')
  soup = BeautifulSoup(res.text.encode('utf-8'), 'html.parser')
  # print(soup.prettify().encode('utf-8'))
  player = {}
  attribute_count = 0
  for tag in soup.find_all(re.compile("^a")):
    if tag.get('class') is None:
      continue
    if not ('list-group-item' in tag['class'] and 'active' in tag['class']):
      continue
    if len(tag['class']) != 3:
      continue
    attribute_count = attribute_count + 1
    attribute_name = None
    attribute_value = None
    for index, child in enumerate(tag.children):
      if index == 0:
        attribute_name = child.string.strip()
      if index == 1:
        attribute_value = int(child.string.strip())
    # print attribute_name
    # print attribute_value
    player[attribute_name] = attribute_value
  if attribute_count != 6:
    print 'ERROR in attribute_count in player ' + str(player_id)
    # Skip this player
    return SKIPPED_FOR_ATTRIBUTE
  price_url = root_price_url.replace('$ID', str(player_id))
  res_price = requests.get(price_url)
  price_data = json.loads(res_price.text)
  player['price'] = price_data
  all_players[str(player_id)] = player
  return SUCCESS;

def main():
  all_players = {}
  write_valid_ids = open('valid_ids_' + date_string, 'w', 0)
  write_invalid_ids = open('invalid_ids_' + date_string, 'w', 0)
  start_id, existing_players = load_from_cache()
  player_id = start_id + 1
  if existing_players:
    all_players = existing_players
  print 'Start from ' + str(player_id)
  while player_id < 30000:
    ret = crawl_player(player_id, all_players)
    if ret == SUCCESS:
      print 'Player ' + str(player_id) + SUCCESS
      write_valid_ids.write(str(player_id) + ',')
    if ret == NOT_PLAYER_ID:
      print 'Player ' + str(player_id) + NOT_PLAYER_ID
      write_invalid_ids.write(str(player_id) + ',')
    if player_id % 50 == 0:
      save_to_cache(player_id, all_players)
    time.sleep(5)
    player_id = player_id + 1

  write_valid_ids.flush()
  write_valid_ids.close()
  write_invalid_ids.flush()
  write_invalid_ids.close()
  with open('players_' + date_string, 'w') as write_to_file:
    write_to_file.write(json.dumps(all_players, sort_keys=True, indent=4))
  os.remove(cache_path)

if __name__ == '__main__':
  main()
