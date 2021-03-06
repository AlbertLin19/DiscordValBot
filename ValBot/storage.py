import pickle
import os
import numpy as np

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER_PATH = os.path.join(BASE_DIR, 'ValBot/data/roster.txt')
HISTORY_PATH = os.path.join(BASE_DIR, 'ValBot/data/history.txt')
IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/pre/')
POST_IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/post/')

# write a roster out
def writeRoster(roster):
	with open(ROSTER_PATH, 'wb') as file:
		pickle.dump(roster, file)
			
# returns roster dict
def getRoster():
	try:
		with open(ROSTER_PATH, 'rb') as file:
			return pickle.load(file)

	except Exception as e:
		print(e)
		print(f'error with unpickling "{ROSTER_PATH}", returning an empty roster')
		return {}

# add player to roster dict
def addRoster(player):
	roster = getRoster()
	if player not in roster:
		roster[player] = []
		writeRoster(roster)
		return True
	return False
	
# remove player from roster dict
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

# write match history out
def writeHistory(history):
	# make sure everything is an int
	for rosterID, matchDict in history.items():
		for timeKey, stats in matchDict.items():
			matchDict[timeKey] = [int(stat) for stat in stats]

	with open(HISTORY_PATH, 'wb') as file:
		pickle.dump(history, file)
			
# returns history dict
def getHistory():
	try:
		with open(HISTORY_PATH, 'rb') as file:
			return pickle.load(file)

	except Exception as e:
		print(e)
		print(f'error with unpickling "{HISTORY_PATH}", returning an empty history')
		return {}

# return dictionary with keys: rosterID, val: list of stats
def getMatch(timeKey):
	history = getHistory()
	matchDict = {}
	found = False
	for rosterID, dictOfMatches in history.items():
		for time, stats in dictOfMatches.items():
			if time == timeKey:
				found = True
				matchDict[rosterID] = stats
				continue
	if not found:
		return None
	return matchDict

# return dictionary with keys: time, val: list of stats
def getPlayerStats(rosterID):
	history = getHistory()
	if rosterID not in history:
		return None
	return history[rosterID]

# save new match using a timeKey
def saveMatch(data, timeKey):
	history = getHistory()
	for rosterID, dictOfMatches in history.items():
		if timeKey in dictOfMatches:
			return False
	for player, stats in data.items():
		if player not in history:
			history[player] = {}
		history[player][timeKey] = stats
	writeHistory(history)
	return True

# get list of stored matches
def getMatches():
	history = getHistory()
	matches = []
	for rosterID, matchDict in history.items():
		matches.extend(matchDict.keys())
	return sorted(set(matches))

# delete entries using timeKey
def deleteMatch(timeKey):
	history = getHistory()
	found = False
	for rosterID, dictOfMatches in history.items():
		if timeKey in dictOfMatches:
			found = True
			del dictOfMatches[timeKey]
	writeHistory(history)
	return found

# get avg player stats
def getAvgPlayerStats(rosterID):
	player_stats = getPlayerStats(rosterID)
	if not player_stats:
		return None
	arrays = []
	for timeKey, stats in player_stats.items():
		arrays.append(stats)
	if len(arrays) == 0:
		return None
	matrix = np.array(arrays)
	return np.sum(matrix, axis=0) / matrix.shape[0]

# get avg roster stats
def getAvgRosterStats():
	roster = getRoster()
	arrays = []
	for rosterID in roster:
		avgPlayerStats = getAvgPlayerStats(rosterID)
		if not np.any(avgPlayerStats):
			continue
		arrays.append(avgPlayerStats)
	if len(arrays) == 0:
		return None
	matrix = np.array(arrays)
	return np.sum(matrix, axis=0) / matrix.shape[0]

# get median of all the roster's average stats
def getMedRosterStats():
	roster = getRoster()
	arrays = []
	for rosterID in roster:
		avgPlayerStats = getAvgPlayerStats(rosterID)
		if not np.any(avgPlayerStats):
			continue
		arrays.append(avgPlayerStats)
	if len(arrays) == 0:
		return None
	matrix = np.array(arrays)
	return np.median(matrix, axis=0)

# clean the image files
def cleanImgDir():
	timeKeys = getMatches()
	num_removed = 0
	for img in os.listdir(IMG_PATH):
		if img.split('.')[0] not in timeKeys:
			os.remove(os.path.join(IMG_PATH, img))
			num_removed+=1
	for img in os.listdir(POST_IMG_PATH):
		if img.split('_post.')[0] not in timeKeys:
			os.remove(os.path.join(POST_IMG_PATH, img))
			num_removed+=1
	return num_removed

# get MMR of rosterID
def getMMR(rosterID):
	avg_stats = getAvgPlayerStats(rosterID)
	weights = np.asarray([0, 0.5, 0, 0, 0, 0.3, 0.2, 0, 0])
	avg_roster_stats = getAvgRosterStats()

	if not np.any(avg_stats) or not np.any(avg_roster_stats):
		return None

	# MMR is 1000*sum(weight* stat/avg roster stat) 
	return 1000*np.sum(np.multiply(weights, np.divide(avg_stats, avg_roster_stats)))