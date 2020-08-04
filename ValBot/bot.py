import os
import discord
from discord.ext import commands
import extract
from storage import writeRoster, getRoster, addRoster, leaveRoster, linkRoster, unlinkRoster, getHistory, writeHistory, saveMatch, getPlayerStats, getMatch, getMatches 
import datetime
import requests
import cv2

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/pre/')
POST_IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/post/')

bot = commands.Bot(command_prefix='!')
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for guild in bot.guilds:
	    print(
	        f'{bot.user.name} connected to:\n'
	        f'{guild.name}(id: {guild.id})'
	    )

active_channels = ['valorant', 'moderation-logeartion'] # channels that ValBot responds to
def checkChannelActive(ctx):
	if ctx.channel.name not in active_channels:
		print(f'{ctx.channel.name} is not an active channel!')
		return False
	return True

@bot.command(name='leave', help='Remove your Discord account')
@commands.check(checkChannelActive)
async def leave(ctx):
	player = ctx.author.name
	left = leaveRoster(player)
	if left:
		await ctx.send(f"```\n'{player}' has left ValBot's roster! 😭\n```")
	else:
		await ctx.send(f"```\n'{player}' is already not on ValBot's roster! 😭\n```")

@bot.command(name='roster', help='List roster')
@commands.check(checkChannelActive)
async def roster(ctx):
	player_string = ''
	roster = getRoster()
	spacing = 36
	i = 0
	for player, riotIDs in roster.items():
		i+=1
		player_string += f"{i}.   {f'{player}:'.ljust(spacing)}{riotIDs}\n"
	await ctx.send(f"```\nRoster ({len(roster)} players):\n{'Name:'.ljust(spacing)}     RiotIDs\n{player_string}\n```")

@bot.command(name='link', help='Link Riot ID to your Discord account')
@commands.check(checkChannelActive)
async def link(ctx, riotID=None):
	player = ctx.author.name
	addRoster(player)

	if not riotID:
		await ctx.send("```Please retry, missing a riotID [  !link '<riotID>'  ]```")
		return

	linked = linkRoster(player, riotID)
	if linked:
		await ctx.send(f"```'{riotID}' has been linked to '{player}'!```")
	else:
		await ctx.send(f"```'{riotID}' is already linked with '{player}' or another player!```")

@bot.command(name='unlink', help='Unlink Riot ID from your Discord account')
@commands.check(checkChannelActive)
async def unlink(ctx, riotID=None):
	player = ctx.author.name
	addRoster(player)
	if not riotID:
		await ctx.send("```Please retry, missing a riotID [  !unlink <riotID>  ]```")
		return
		
	unlinked = unlinkRoster(player, riotID)
	if unlinked:
		await ctx.send(f"```'{riotID}' has been unlinked from {player}!```")
	else:
		await ctx.send(f"```'{riotID}' is already unlinked from {player}!```")

current_img = ''  # path to current img to handle
@bot.command(name='upload', help='Upload post game image for OCR')
@commands.check(checkChannelActive)
async def upload(ctx):
    global current_img
    time = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    if len(ctx.message.attachments) == 0:
    	await ctx.channel.send('```Please attach an image!```')
    	return
    attach = ctx.message.attachments[0]
    print(f'received upload: {attach.url}')
    path_name = os.path.join(IMG_PATH, f'{time}.png')
    with open(path_name, 'wb') as f:
        f.write(requests.get(attach.url).content)
    current_img = path_name
    await ctx.channel.send('```Image downloaded as "' + time + '.png"```')
    await ctx.channel.send('```Either !process or !cancel...```')

@bot.command(name='process', help='Process img after !upload')
@commands.check(checkChannelActive)
async def process(ctx):
	global current_img
	data = {}  # holds the extracted info
	detected_rosterIDs = [] # parallel arrays
	detected_riotIDs = []

	if current_img == '':
		await ctx.channel.send('```No img currently active, please !upload```')
		return
	await ctx.channel.send('```processing...```')
	data, img, error = extract.extract(current_img)
	if error:
		await ctx.channel.send(f'```{error}```')
	post_path = os.path.join(POST_IMG_PATH, (current_img.split("/")[-1]).split(".")[0] + '_post.png')
	cv2.imwrite(post_path, img)
	await ctx.channel.send('```done! sending results...```')
	await ctx.channel.send(file=discord.File(post_path))
	if error:
		await ctx.channel.send('```quitting because of error```')

	# get list of players from data who are on roster
	roster = getRoster()
	for player, value in data.items():
		for rosterID, riotIDs in roster.items():
			if player in riotIDs:
				detected_rosterIDs.append(rosterID)
				detected_riotIDs.append(player)
	detected_string = ''
	for i in range(len(detected_rosterIDs)):
		detected_string += f'{detected_rosterIDs[i]} as "{detected_riotIDs[i]}"\n'
	await ctx.channel.send(f'```roster members ({len(detected_rosterIDs)}) found:\n{detected_string}\n```')

	# get user input to confirm, cancel, or edit
	def check(message):
		return message.author == ctx.author and message.channel == ctx.channel
	user_input = ''
	attributes = ['color', 'score', 'K', 'D', 'A', 'econ', 'bloods', 'plants', 'defuses', 'name']
	change_log = {} # formatted as nested dictionary, player key then attribute key
	while user_input != 'confirm' and user_input != 'cancel':
		await ctx.channel.send(f'```RESPOND OPTIONS: [  confirm  ],\t [  cancel  ],\t [  edit <name>:<attribute>:<value>  ]\n\npossible names\n{list(data.keys())}\n\neditable attributes\n{attributes}```')
		user_input = str((await bot.wait_for('message', check=check)).content)

		if user_input == 'confirm' or user_input == 'cancel':
			continue

		elif user_input[0:4] == 'edit':
			# store the change, print all existing changes
			name, attribute, value = (user_input.split(' ')[1]).split(':')
			if name not in data:
				await ctx.channel.send(f'```{name} not a valid name, please try again```')
				continue
			if attribute not in attributes:
				await ctx.channel.send(f'```{attribute} not a valid attribute, please try again```')
				continue
			if name not in change_log:
				change_log[name] = {}
			change_log[name][attribute] = value
			change_string = ''
			for name, value in change_log.items():
				change_string += f'{name}:\n'
				for attr in value:
					if attr == 'name':  # data does not store name, since it is its keys
						change_string += f'\t{attr}: from "{name}" to "{value[attr]}"\n'
					else:
						change_string += f'\t{attr}: from "{data[name][attributes.index(attr)]}" to "{value[attr]}"\n'

			await ctx.channel.send(f'```Changes to be made:\n{change_string}\n```')
			continue

		else:
			await ctx.channel.send('```invalid option, please try again```')
	if user_input == 'cancel':
		current_img = ''
		await ctx.channel.send('```cancelled```')

	elif user_input == 'confirm':
		user_input = ''
		while user_input != 'blue' and user_input != 'red':
			await ctx.channel.send("```Who won? <blue/red>```")
			user_input = str((await bot.wait_for('message', check=check)).content)
		winner = user_input

		# change the data using change_log, then store the data
		for name, value in change_log.items():
			for attr, newVal in value.items():
				if attr == 'name':
					data[newVal] = data[name]
					del data[name]
				else:
					data[name][attributes.index(attr)] = newVal

		relevant_data = {} # filter only data whose key is on roster
		for key, value in data.items():
			for rosterID, riotIDs in roster.items():
				if key in riotIDs:
					relevant_data[rosterID] = value
					value[0] = 1 if value[0] == winner else 0 # turn color to 0 or 1

		save_string = ''
		for rosterID, stats in relevant_data.items():
			save_string += f'{f"{rosterID}:".ljust(25)}{f"WON" if stats[0] == 1 else f"LOST"} {stats[1:]}\n'


		await ctx.channel.send(f'```SAVING:\n{save_string}```')
		timeKey = (current_img.split("/")[-1]).split(".")[0]
		reformatted = datetime.datetime.strptime(timeKey,'%Y%m%d_%H%M').strftime("%B %#d, %Y at %#I:%M")
		print(f'saving {reformatted} data with timeKey {timeKey}')
		saved = saveMatch(relevant_data, timeKey)
		current_img = ''
		if saved:
			await ctx.channel.send('```FINISHED SAVING```')
		else:
			await ctx.channel.send('```could not save!! error with duplicate key?```')


@bot.command(name='cancel', help='Cancel img after !upload')
@commands.check(checkChannelActive)
async def cancel(ctx):
	global current_img
	if current_img == '':
		await ctx.channel.send('```No img currently active to cancel!```')
		return
	current_img = ''
	await ctx.channel.send('```Img has been cancelled!```')

@bot.command(name='history', help='View entire stored history')
@commands.check(checkChannelActive)
async def history(ctx):
	history = getHistory()
	await ctx.channel.send(f'```{history}```')

@bot.command(name='matches', help='List stored matches')
@commands.check(checkChannelActive)
async def matches(ctx):
	matches = getMatches()
	string = ''
	i = 0
	for match in matches:
		i+=1
		reformatted = datetime.datetime.strptime(match,'%Y%m%d_%H%M').strftime("%B %#d, %Y at %#I:%M")
		string += f"{i}. [{reformatted}]\n"
	await ctx.channel.send(f'```Stored Matches:\n{string}```')

@bot.command(name='match', help='View match <#>')
@commands.check(checkChannelActive)
async def match(ctx, matchNum = None):
	if not matchNum:
		await ctx.channel.send('```Please specify a match number (from !matches) [  !match <num>  ]```')
		return
	matches = getMatches()
	if not matchNum.isdigit() or int(matchNum) > len(matches) or int(matchNum) < 1:
		await ctx.channel.send('```Please specify a valid match number (from !matches) [  !match <num>  ]```')
		return
	timeKey = matches[int(matchNum)-1]
	reformatted = datetime.datetime.strptime(timeKey,'%Y%m%d_%H%M').strftime("%B %#d, %Y at %#I:%M")
	matchStats = getMatch(timeKey)
	matchString = ''
	for rosterID, stats in matchStats.items():
		matchString += f"{f'{rosterID}:'.ljust(25)}{stats}"
	fields = ['WON', 'score', 'K', 'D', 'A', 'econ', 'bloods', 'plants', 'defuses']
	await ctx.channel.send(f'```{f"{reformatted}".ljust(25)}{fields}\n{matchString}```')

whitelist = ['A_L__'] # people who can use admin commands
@bot.command(name='admin', help='run commands as admin')
@commands.check(checkChannelActive)
async def admin(ctx, command=None, target=None, riotID=None):
	if ctx.author.name not in whitelist:
		await ctx.channel.send("```Do 100 pushups a day and perhaps one day, you'll have this power as your own!```")
		return
	if not command:
		await ctx.channel.send("```Need to specify a command! [  !admin <command> <parameters...>  ]```")
		return
	commands = ['link', 'unlink', 'leave']
	if command not in commands:
		await ctx.channel.send(f"```{command} is not a valid command! Try: {commands}```")
		return

	if command == 'link':
		if not target or not riotID:
			await ctx.channel.send("```Need to specify a target and/or riotID! [  !admin link <discordID> <riotID>  ]```")
			return
		addRoster(target)
		linked = linkRoster(target, riotID)
		if linked:
			await ctx.send(f"```'{riotID}' has been linked to '{target}'!```")
		else:
			await ctx.send(f"```'{riotID}' is already linked with '{target}' or another player!```")

	if command == 'unlink':
		if not target or not riotID:
			await ctx.channel.send("```Need to specify a target and/or riotID! [  !admin unlink <discordID> <riotID>  ]```")
			return
		addRoster(target)
		unlinked = unlinkRoster(target, riotID)
		if unlinked:
			await ctx.send(f"```'{riotID}' has been unlinked from {target}!```")
		else:
			await ctx.send(f"```'{riotID}' is already unlinked from {target}!```")

	if command == 'leave':
		if not target:
			await ctx.channel.send("```Need to specify a target! [  !admin leave <discordID>  ]```")
			return
		left = leaveRoster(target)
		if left:
			await ctx.send(f"```'{target}' has left ValBot's roster! 😭```")
		else:
			await ctx.send(f"```'{target}' is already not on ValBot's roster! 😭```")

bot.run(TOKEN)