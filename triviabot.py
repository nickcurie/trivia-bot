import os

import discord

import schedule
import time

from random import shuffle

from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')

team_data = {}
team_points = {}
buzz_queue = []
emoji_team_list = ['👍', '🔥', '🍆', '💦', '😤', '👁️','👄','🔫', '🇰🇵']
host_id = 0
current_round = 0

round_active = -1

#change hosts
#randomize emojis

@bot.event
async def on_ready():
	print("Trivia Boi online!")

@bot.event
async def on_reaction_add(reaction, user):
	if user.id == host_id:
		#print("fuck")
		emoji = reaction.emoji
		emoji_index = -1
		for emoji_num in range(len(emoji_team_list)):
			if emoji == emoji_team_list[emoji_num]:
				emoji_index = emoji_num
		team_name = list(team_data.keys())[emoji_index]
		team_points[team_name] += 1
		await reaction.message.channel.send("Team {0} got a point!".format(team_name))

@bot.command(name='start', help='Starts trivia. Usage: !start')
async def start_trivia(ctx):
	await ctx.send("Starting Trivia...")
	team_data.clear()
	global round_active
	global host_id
	global current_round
	shuffle(emoji_team_list)
	round_active = 0
	host_id = 0
	current_round = 0
	team_points.clear()
	await ctx.send("Declare team leads and names with !lead")

@bot.command(name='lead', help='Declares team leader and name. Usage: !lead {Team Name}')
async def team_info(ctx, team_name):
	team_name=team_name[:25]
	for name in team_data:
		members = team_data[name]
		if ctx.message.author.id in members:
			await ctx.send("You are already in the team '{0}'".format(name))
			return
	# if team_name == '':
	# 	team_data.setdefault(ctx.message.author.display_name, []).append(ctx.message.author.id)
	# 	team_points[ctx.message.author.display_name] = 0
	# else:
	team_data.setdefault(team_name, []).append(ctx.message.author.id)
	team_points[team_name] = 0
	await ctx.send("Team declared! {0}, your team is '{1}'".format(ctx.message.author.display_name, team_name))

@bot.command(name='join', help="Joins a team")
async def join_team(ctx, team_name):
	if team_name in team_data:
		for name in team_data:
			members = team_data[name]
			if ctx.message.author.id in members:
				await ctx.send("You are already in the team '{0}'".format(name))
				return
		team_data[team_name].append(ctx.message.author.id)
		await ctx.send('{0} joined team {1}'.format(ctx.message.author.display_name, team_name))
	else:
		await ctx.send('{0} is not a valid team'.format(team_name))

@bot.command(name='teams', help="Lists all team names. Usage !teams")
async def list_teams(ctx):
	message = ""
	for name in team_data:
		message += '{0}: {1}\n'.format(name, team_points[name])
	await ctx.send(message)

@bot.command(name='addpoint', help='Adds a point to the given team. Usage ![addpoint, addp, ap] {Team Name}', aliases=['addp','ap'])
async def add_point(ctx):
	if host_id == ctx.message.author.id:
		message_block = "`"
		for team in team_data:
			message_block += "{0}: {1} ".format(emoji_team_list[list(team_data.keys()).index(team)], team)
		message_block += "`"
		msg = await ctx.send(message_block)
		for team in team_data:
			emoji = emoji_team_list[list(team_data.keys()).index(team)]
			#print(emoji)
			await msg.add_reaction(emoji)
	else:
		await ctx.send("You're not the host!")

@bot.command(name='buzz', help="Lock in spot to answer question. Usage ![buzz, b, blank]", aliases=['b','blank'])
async def buzz_in(ctx):
	if round_active == 1:
		if get_team(ctx.message.author.id) == "":
			await ctx.send("You must be on a team to buzz in!")
		else:
			user_id = ctx.message.author.id
			team = get_team(user_id)
			if team in buzz_queue:
				await ctx.send("Your team has already buzzed in!")
			else:
				buzz_queue.append(team)
				await ctx.send("BUZZ! Team {0} has buzzed in!".format(team))
	else:
		await ctx.send("The round has not begun yet. Don't spam or you'll be mod abused.")

@bot.command(name='endround', help="Ends the current round. Usage ![endround, er, endr]", aliases=['er', 'endr'])
async def end_round(ctx):
	if host_id == ctx.message.author.id:
		global round_active
		round_active = 0
		buzz_queue.clear()
		await ctx.send("Round {0} ended!".format(current_round))
	else:
		await ctx.send("You're not the host!")

@bot.command(name='startround', help="Starts a new round. Usage ![startround, sr, startr]", aliases=['sr', 'startr'])
async def start_round(ctx):
	if host_id == ctx.message.author.id:
		global round_active
		global current_round
		round_active = 1
		current_round += 1
		await ctx.send("Round {0} started!".format(current_round))
		if current_round > 4 and current_round % 5 == 0:
			await ctx.send("Showing progress...")
			message = ""
			for name in team_data:
				message += '{0}: {1}\n'.format(name, team_points[name])
			await ctx.send(message)
	else:
		await ctx.send("You're not the host!")

@bot.command(name='nextround', help="Ends the current round. Usage ![nextround, nr, nextr]", aliases=['nr', 'nextr'])
async def next_round(ctx):
	if host_id == ctx.message.author.id:
		global current_round
		buzz_queue.clear()
		await ctx.send("Round {0} ended!".format(current_round))
		current_round += 1
		await ctx.send("Round {0} started!".format(current_round))
		if current_round > 4 and current_round % 5 == 0:
			await ctx.send("Showing progress...")
			message = ""
			for name in team_data:
				message += '{0}: {1}\n'.format(name, team_points[name])
			await ctx.send(message)
	else:
		await ctx.send("You're not the host!")

@bot.command(name='host', help="Declares the host")
async def declare_host(ctx):
	global host_id
	if host_id == 0:
		host_id = ctx.message.author.id
		await ctx.send("{0} is basically god".format(ctx.message.author.display_name))
	else:
		await ctx.send("Someone is already the host")

@bot.command(name='order', help="Lists the order of the buzz queue. Usage ![order, o]", aliases=['o'])
async def show_order(ctx):
	message = ""
	for team in buzz_queue:
		message += "{0}. {1} \n".format(buzz_queue.index(team)+1, team)
	await ctx.send(message)

@bot.command(name='leave', help="Leave current team")
async def leave_team(ctx):
	team = get_team(ctx.message.author.id)
	if team == "":
		await ctx.send("You're not in a team!")
	else:
		team_data[team].remove(ctx.message.author.id)
		await ctx.send("{0} has left team {1}".format(ctx.message.author.display_name, team))
		if len(team_data[team]) == 0:
			del team_data[team]

@bot.command(name='fakepoint', help="Yeah you would need help lol")
async def award_participation_trophy(ctx, team_name):
	if team_name in team_data:
		await ctx.send("Congratulations team {0}, you've been awarded a participation trophy courtesy of {1}".format(team_name, ctx.message.author.display_name))
	else:
		await ctx.send("That's not a team you monkey")

@bot.command(name='endgame', help='Ends the game and shows final results. Usage ![endgame, eg, end]', aliases=['eg','end'])
async def end_game(ctx):
	if ctx.message.author.id == host_id:
		team_name = max(team_points, key=lambda key: team_points[key])
		await ctx.send("Congratulations team {0}, you win!".format(team_name))
		message = ""
		for name in team_data:
			message += '{0}: {1}\n'.format(name, team_points[name])
		await ctx.send(message)
	else:
		await ctx.send("Nice try buddy")

# @bot.command(name='countdown', help="Starts question countdown. Usage ![countdown, cd]", aliases=['cd'])
# async def start_countdown(ctx):
# 	cycles = 0
# 	#await ctx.send("LOL")
# 	schedule.every(1).seconds.do(edit_message, ctx)
# 	while True:
# 		if cycles < 10:
# 			cycles += 1
# 			schedule.run_pending()
# 			time.sleep(1)
# 		else:
# 			break


#helper functions
def get_team(user_id):
	for team in team_data:
		members = team_data[team]
		if user_id in members:
			return team
	return ""

async def edit_message(ctx):
	await ctx.send("hi")

bot.run(TOKEN)