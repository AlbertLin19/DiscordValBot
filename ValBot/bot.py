import os
import discord
from discord.ext import commands
import pickle
import extract
import datetime
import requests
import cv2

bot = commands.Bot(command_prefix='!')
TOKEN = os.getenv('DISCORD_TOKEN')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER_PATH = os.path.join(BASE_DIR, 'ValBot/data/roster.txt')
MATCH_HISTORY_PATH = os.path.join(BASE_DIR, 'ValBot/data/match_history.txt')
IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/pre/')
POST_IMG_PATH = os.path.join(BASE_DIR, 'ValBot/imgs/post/')

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
		return []

# add player to roster list
def addRoster(player):
	roster = getRoster()
	if player not in roster:
		roster.append(player)
		writeRoster(roster)
		return True
	return False
	
# remove player from roster list
def leaveRoster(player):
	roster = getRoster()
	if player in roster:
		roster.remove(player)
		writeRoster(roster)
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

active_channels = ['valorant', 'moderation-logeartion'] # channels that ValBot responds to
def checkChannelActive(ctx):
	if ctx.channel.name not in active_channels:
		print(f'{ctx.channel.name} is not an active channel!')
		return False
	return True

@bot.command(name='register', help='Register into the roster')
@commands.check(checkChannelActive)
async def register(ctx):
	player = ctx.author.name
	added = addRoster(player)
	if added:
		await ctx.send(f"'{player}' has joined ValBot's roster!")
	else:
		await ctx.send(f"'{player}' is already on ValBot's roster!")

@bot.command(name='leave', help='Leave roster')
@commands.check(checkChannelActive)
async def leave(ctx):
	player = ctx.author.name
	left = leaveRoster(player)
	if left:
		await ctx.send(f"'{player}' has left ValBot's roster! :sob:")
	else:
		await ctx.send(f"'{player}' is already not on ValBot's roster! :sob:")

@bot.command(name='roster', help='List roster')
@commands.check(checkChannelActive)
async def roster(ctx):
	player_string = ''
	roster = getRoster()
	for i in range(len(roster)):
		player_string += f"{i + 1}.   {roster[i]}\n"
	await ctx.send(f"Roster ({len(roster)} players):\n{player_string}")

current_img = ''  # path to current img to handle
@bot.command(name='upload', help='Upload post game image for OCR')
@commands.check(checkChannelActive)
async def upload(ctx):
    global current_img
    time = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    if len(ctx.message.attachments) == 0:
    	await ctx.channel.send('Please attach an image!')
    	return
    attach = ctx.message.attachments[0]
    print(f'received upload: {attach.url}')
    path_name = os.path.join(IMG_PATH, f'{time}.png')
    with open(path_name, 'wb') as f:
        f.write(requests.get(attach.url).content)
    current_img = path_name
    await ctx.channel.send('Image downloaded as "' + time + '.png"')
    await ctx.channel.send('Either !process or !cancel...')

@bot.command(name='process', help='Process img after !upload')
@commands.check(checkChannelActive)
async def process(ctx):
	global current_img
	if current_img == '':
		await ctx.channel.send('No img currently active, please !upload')
		return
	await ctx.channel.send('processing...')
	data, img = extract.extract(current_img)
	post_path = os.path.join(POST_IMG_PATH, (current_img.split("/")[-1]).split(".")[0] + '_post.png')
	cv2.imwrite(post_path, img)
	current_img = ''
	await ctx.channel.send('done! sending results...')
	await ctx.channel.send(file=discord.File(post_path))

@bot.command(name='cancel', help='Cancel img after !upload')
@commands.check(checkChannelActive)
async def cancel(ctx):
	global current_img
	if current_img == '':
		await ctx.channel.send('No img currently active to cancel!')
		return
	current_img = ''
	await ctx.channel.send('Img has been cancelled!')

	
bot.run(TOKEN)