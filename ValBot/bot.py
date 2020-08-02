import os
import discord
from discord.ext import commands
bot = commands.Bot(command_prefix='!')
TOKEN = os.getenv('DISCORD_TOKEN')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER_PATH = os.path.join(BASE_DIR, 'ValBot/data/roster.txt')
MATCH_HISTORY_PATH = os.path.join(BASE_DIR, 'ValBot/data/match_history.txt')
# returns roster list
def getRoster():
	roster = []
	with open(ROSTER_PATH) as file:
		for player in file:
			roster.append(player)
	return roster

# add player to roster list
def addRoster(player):
	roster = getRoster()
	if player not in roster:
		with open(ROSTER_PATH, 'w') as file:
			for rosterPlayer in roster:
				file.write(str(rosterPlayer))
				file.write("\n")
			file.write(str(player) + '\n')
			return True
	return False
	
# remove player from roster list
def leaveRoster(player):
	roster = getRoster()
	if player in roster:
		roster.remove(player)
		with open(ROSTER_PATH, 'w') as file:
			for rosterPlayer in roster:
				file.write(str(rosterPlayer) + '\n')
		return True
	return False

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for guild in bot.guilds:
	    print(
	        f'{bot.user.name} connected to:\n'
	        f'{guild.name}(id: {guild.id})'
	    )

active_channels = ['valorant'] # channels that ValBot responds to
def checkChannelActive(ctx):
	if ctx.channel.name not in active_channels:
		print(f'{ctx.channel.name} is not an active channel!')
		return False
	return True

@bot.command(name='join', help='Join roster')
@commands.check(checkChannelActive)
async def join(ctx):
	added = addRoster(ctx.author)
	if added:
		await ctx.send(f"{ctx.author} has joined ValBot's roster!")
	else:
		await ctx.send(f"{ctx.author} is already on ValBot's roster!")

@bot.command(name='leave', help='Leave roster')
@commands.check(checkChannelActive)
async def leave(ctx):
	left = leaveRoster(ctx.author)
	if left:
		await ctx.send(f"{ctx.auathor} has left ValBot's roster! :sob:")
	else:
		await ctx.send(f"{ctx.author} is already not on ValBot's roster! :sob:")

@bot.command(name='roster', help='List roster')
@commands.check(checkChannelActive)
async def roster(ctx):
	await ctx.send(f"Roster: {getRoster()}")
	
bot.run(TOKEN)