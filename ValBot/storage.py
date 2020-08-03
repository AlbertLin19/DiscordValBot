import pickle
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER_PATH = os.path.join(BASE_DIR, 'ValBot/data/roster.txt')
MATCH_HISTORY_PATH = os.path.join(BASE_DIR, 'ValBot/data/match_history.txt')

# write a roster out
def writeRoster(roster):
	with open(ROSTER_PATH, 'wb') as file:
		pickle.dump(roster, file)
			
# returns roster list
def getRoster():
	try:
		with open(ROSTER_PATH, 'rb') as file:
			return pickle.load(file)

	except Exception as e:
		print(e)
		print(f'error with unpickling "{ROSTER_PATH}", returning an empty roster')
		return {}

# add player to roster list
def addRoster(player):
	roster = getRoster()
	if player not in roster:
		roster[player] = []
		writeRoster(roster)
		return True
	return False
	
# remove player from roster list
def leaveRoster(player):
	roster = getRoster()
	if player in roster:
		del roster[player]
		writeRoster(roster)
		return True
	return False

# link riotID to roster key
def linkRoster(player, riotID):
	roster = getRoster()
	if player not in roster or riotID in roster[player]:
		return False
	for rosterID, riotIDs in roster.items():
		if riotID in riotIDs:
			return False
	roster[player].append(riotID)
	writeRoster(roster)
	return True

# unlink riotID to roster key
def unlinkRoster(player, riotID):
	roster = getRoster()
	if player not in roster or riotID not in roster[player]:
		return False
	roster[player].remove(riotID)
	writeRoster(roster)
	return True
