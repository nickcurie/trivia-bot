import os
import discord

# import schedule
# import time
from random import shuffle
from dotenv import load_dotenv
from discord.ext import commands
import sqlite3


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

conn = sqlite3.connect('trivia.db')
c = conn.cursor()

emoji_list = ['👍', '🔥', '🍆', '💦', '😤', '👁️','👄','🔫', '🇰🇵']


@bot.event
async def on_ready():
        print("Trivia Boi online!")
        c.execute('CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name VARCHAR(255), points TINYINT DEFAULT 0, buzz_order TINYINT DEFAULT -1)')
        c.execute('CREATE TABLE IF NOT EXISTS members (team_id INTEGER, user_id INTEGER, host TINYINT DEFAULT 0, FOREIGN KEY (team_id) REFERENCES teams (id))')
        c.execute('CREATE TABLE IF NOT EXISTS rounds (id INTEGER PRIMARY KEY, active TINYINT)')
        conn.commit()

@bot.event
async def on_reaction_add(reaction, user):
        host_id = get_host_id()
        if user.id == host_id:
                emoji = reaction.emoji
                emoji_index = -1
                for emoji_num in range(len(emoji_list)):
                        if str(emoji) == str(emoji_list[emoji_num]):
                                emoji_index = emoji_num
                                break
                c.execute('SELECT points, name FROM teams WHERE id = ?', (emoji_index+1,))
                row = c.fetchone()
                points = row[0]
                team_name = row[1]
                points += 1
                c.execute('UPDATE teams SET points = ?', (points,))
                await reaction.message.channel.send("Team {0} got a point!".format(team_name))
                conn.commit()

@bot.command(name='start', help='Starts trivia. Usage: !start')
async def start_trivia(ctx):
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                global emoji_list

                server = ctx.message.channel.guild
                server_emojis = server.emojis
                #print("server emojis are: {}".format(server_emojis))
                if len(server_emojis) > 6:
                    emoji_list = list(map(lambda x: str(x), server_emojis))
                else:
                    print("not using custom server emojis")

                shuffle(emoji_list)
                c.execute('INSERT INTO rounds (id, active) SELECT 1,1 WHERE NOT EXISTS(SELECT 1 FROM rounds WHERE id = 1)')
                conn.commit()
                embedVar = discord.Embed(title="Welcome To Trivia!", description="Tonight's episode is hosted by {0}!".format(ctx.message.author.display_name), color=0x00ff00)
                await ctx.send(embed=embedVar)
                embedVar = discord.Embed(title="Round 1 started!", description="", color=0x00ff00)
                await ctx.send(embed=embedVar)
        elif host_id == 0:
                await ctx.send("Please declare a host first")
        else:
                await ctx.send("You **CANNOT**")

@bot.command(name='lead', help='Declares team leader and name. Usage: !lead {Team Name}')
async def team_info(ctx, team_name):
        team_name = team_name[:40]
        c.execute('SELECT * FROM members WHERE user_id = ?', (ctx.message.author.id,))
        row = c.fetchone()
        if row:
                if row[2] == 1:
                        await ctx.send("Hosts can't join teams")
                else:
                        await ctx.send("You're already in a team")
        else:
                c.execute('INSERT INTO teams (name) VALUES (?)', (team_name,))
                c.execute('SELECT id FROM teams WHERE name = ?', (team_name,))
                row = c.fetchone()
                c.execute('INSERT INTO members (team_id, user_id) VALUES (?,?)',(row[0], ctx.message.author.id))
                embedVar = discord.Embed(title="Team Declared!", description="{0}, your team is {1}".format(ctx.message.author.display_name, team_name))
                await ctx.send(embed=embedVar)
                conn.commit()
        # for name in team_data:
        #         members = team_data[name]
        #         if ctx.message.author.id in members:
        #                 await ctx.send("You are already in the team '{0}'".format(name))
        #                 return
        # team_data.setdefault(team_name, []).append(ctx.message.author.id)
        # team_points[team_name] = 0

@bot.command(name='join', help="Joins a team")
async def join_team(ctx, team_name):
        # if team_name in team_data:
        #         for name in team_data:
        #                 members = team_data[name]
        #                 if ctx.message.author.id in members:
        #                         await ctx.send("You are already in the team '{0}'".format(name))
        #                         return
        #         team_data[team_name].append(ctx.message.author.id)
        #         await ctx.send('{0} joined team {1}'.format(ctx.message.author.display_name, team_name))
        # else:
        #         await ctx.send('{0} is not a valid team'.format(team_name))
        c.execute('SELECT * FROM teams WHERE name = ?', (team_name,))
        row = c.fetchone()
        #print(row)
        if row:
                c.execute('INSERT INTO members (team_id, user_id) VALUES (?,?)', (row[0], ctx.message.author.id))
                embedVar = discord.Embed(title="Team Joined!", description="{0} joined team {1}".format(ctx.message.author.display_name, team_name))
                await ctx.send(embed=embedVar)
                conn.commit()
        else:
                await ctx.send('{0} is not a valid team'.format(team_name))

@bot.command(name='teams', help="Lists all team names. Usage !teams")
async def list_teams(ctx):
        embedVar = discord.Embed(title="Team Data", description="", color=0x00ff00)
        c.execute('SELECT name, points FROM teams')
        for row in c.fetchall():
                plural = 'points'
                if row[1] == 1:
                        plural = 'point'
                embedVar.add_field(name='{0}'.format(row[0]), value='{0} {1}'.format(row[1], plural), inline=False)
        await ctx.send(embed=embedVar)

@bot.command(name='addpoint', help='Adds a point to the given team. Usage ![addpoint, addp, ap] {Team Name}', aliases=['addp','ap'])
async def add_point(ctx):
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                embedVar = discord.Embed(title="Add A Point")
                c.execute('SELECT name FROM teams')
                i = 0
                for row in c.fetchall():
                        embedVar.add_field(name="Team {0}".format(i+1), value="{0}: {1}\n".format(emoji_list[i], row[0]))
                        i += 1
                msg = await ctx.send(embed=embedVar)
                c.execute('SELECT * FROM teams')
                for j in range(i):
                        emoji = emoji_list[j]
                        #print(emoji)
                        await msg.add_reaction(emoji)
        else:
                await ctx.send("You're not the host!")

@bot.command(name='buzz', help="Lock in spot to answer question. Usage ![buzz, b, blank]", aliases=['b','blank'])
async def buzz_in(ctx):
        # if round_active == 1:
        #         team = get_team(ctx.message.author.id)
        #         if team == "":
        #                 await ctx.send("You must be on a team to buzz in!")
        #         else:
        #                 if team in buzz_queue:
        #                         await ctx.send("Your team has already buzzed in!")
        #                 else:
        #                         buzz_queue.append(team)
        #                         await ctx.send("BUZZ! Team {0} has buzzed in!".format(team))
        # else:
        #         await ctx.send("The round has not begun yet. Don't spam or you'll be deleted off the face of the planet.")
        round_num = get_current_round()
        if round_num >= 0:
                team = get_team(ctx.message.author.id)
                if team == "":
                        await ctx.send("You must be on a team to buzz in!")
                else:
                        c.execute('SELECT buzz_order FROM teams WHERE name = ?', (team,))
                        row = c.fetchone()
                        if row[0] == -1:
                                c.execute('SELECT MAX(buzz_order) FROM teams')
                                highest_order = c.fetchone()[0]
                                if highest_order == -1:
                                        c.execute('UPDATE teams SET buzz_order = 1 WHERE name = ?', (team,))
                                else:
                                        c.execute('UPDATE teams SET buzz_order = ? WHERE name = ?', (highest_order+1,team))
                                embedVar = discord.Embed(title="BUZZ!", description="Team {0} has buzzed in!".format(team), color=0xff0000)
                                await ctx.send(embed=embedVar)
                                conn.commit()
                        else:
                                await ctx.send("Your team has already buzzed in!")
        else:
                await ctx.send("The round has not begun yet. Don't spam or you'll be deleted off the face of the planet.")

@bot.command(name='endround', help="Ends the current round. Usage ![endround, er]", aliases=['er'])
async def end_round(ctx):
        # if host_id == ctx.message.author.id:
        #         global round_active
        #         round_active = 0
        #         buzz_queue.clear()
        #         await ctx.send("Round {0} ended!".format(current_round))
        # else:
        #         await ctx.send("You're not the host!")
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                round_num = get_current_round()
                if round_num == -1:
                        await ctx.send("No active round")
                else:
                        c.execute('UPDATE rounds SET active = 0 WHERE id = ?', (round_num,))
                        c.execute('UPDATE teams SET buzz_order = -1')
                        conn.commit()
                        embedVar = discord.Embed(title="Round {0} ended!".format(round_num), description="", color=0xff0000)
                        await ctx.send(embed=embedVar)
        else:
                await ctx.send("You're not the host!")

# welcome to trivia! hosted by: 
@bot.command(name='startround', help="Starts a new round. Usage ![startround, sr]", aliases=['sr'])
async def start_round(ctx):
        # if host_id == ctx.message.author.id:
        #         global round_active
        #         global current_round
        #         round_active = 1
        #         current_round += 1
        #         await ctx.send("Round {0} started!".format(current_round))
        #         if current_round > 4 and current_round % 5 == 0:
        #                 await ctx.send("Showing progress...")
        #                 message = ""
        #                 for name in team_data:
        #                         message += '{0}: {1}\n'.format(name, team_points[name])
        #                 await ctx.send(message)
        # else:
        #         await ctx.send("You're not the host!")
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                round_num = get_recent_round()
                print(round_num)
                if round_num == -1:
                        round_num = 1
                else:
                        round_num += 1
                c.execute('INSERT INTO rounds (id, active) VALUES (?, 1)', (round_num,))        
                conn.commit()
                embedVar = discord.Embed(title="Round {0} started!".format(round_num), description="", color=0x00ff00)
                await ctx.send(embed=embedVar)
                if round_num > 4 and round_num % 5 == 0:
                        embedVar = discord.Embed(title="Current Scores", description="", color=0x0000ff)
                        c.execute('SELECT name, points FROM teams ORDER BY points')
                        for row in c.fetchall():
                                plural = 'points'
                                if row[1] == 1:
                                        plural = 'point'
                                embedVar.add_field(name='{0}'.format(row[0]), value='{0} {1}'.format(row[1], plural), inline=False)
                        await ctx.send(embed=embedVar)
        else:
                await ctx.send("You're not the host!")

@bot.command(name='nextround', help="Ends the current round. Usage ![nextround, nr]", aliases=['nr'])
async def next_round(ctx):
        # if host_id == ctx.message.author.id:
        #         global current_round
        #         buzz_queue.clear()
        #         await ctx.send("Round {0} ended!".format(current_round))
        #         current_round += 1
        #         await ctx.send("Round {0} started!".format(current_round))
        #         if current_round > 4 and current_round % 5 == 0:
        #                 await ctx.send("Showing progress...")
        #                 message = ""
        #                 for name in team_data:
        #                         message += '{0}: {1}\n'.format(name, team_points[name])
        #                 await ctx.send(message)
        # else:
        #         await ctx.send("You're not the host!")
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                round_num = get_current_round()
                if round_num == -1:
                        await ctx.send("No")
                else:
                        #end current round
                        c.execute('UPDATE rounds SET active = 0 WHERE id = ?', (round_num,))
                        c.execute('UPDATE teams SET buzz_order = -1')
                        embedVar = discord.Embed(title="Round {0} ended!".format(round_num), description="", color=0xff0000)
                        await ctx.send(embed=embedVar)
                        #start new round
                        round_num += 1
                        c.execute('INSERT INTO rounds (id, active) VALUES (?, 1)', (round_num,))        
                        conn.commit()
                        embedVar = discord.Embed(title="Round {0} started!".format(round_num), description="", color=0x00ff00)
                        await ctx.send(embed=embedVar)
                        if round_num > 4 and round_num % 5 == 0:
                                embedVar = discord.Embed(title="Current Scores", description="", color=0x0000ff)
                                c.execute('SELECT name, points FROM teams ORDER BY points')
                                for row in c.fetchall():
                                        plural = 'points'
                                        if row[1] == 1:
                                                plural = 'point'
                                        embedVar.add_field(name='{0}'.format(row[0]), value='{0} {1}'.format(row[1], plural), inline=False)
                                await ctx.send(embed=embedVar)
        else:
                await ctx.send("You're not the host!")

@bot.command(name='host', help="Declares the host")
async def declare_host(ctx):
        host_id = get_host_id()
        if host_id == 0:
                c.execute('SELECT * FROM members WHERE user_id = ?', (ctx.message.author.id,))
                if c.fetchone():
                        await ctx.send("Hosts can't already be on a team. Leave with !leave")
                else:
                        c.execute('INSERT INTO members (user_id, host) VALUES (?, 1)', (ctx.message.author.id,))
                        await ctx.send("{0} is basically god".format(ctx.message.author.display_name))
                        conn.commit()
        elif host_id == ctx.message.author.id:
                await ctx.send("You are already the host")
        else:
                await ctx.send("Someone is already the host")
                

@bot.command(name='order', help="Lists the order of the buzz queue. Usage ![order, o]", aliases=['o'])
async def show_order(ctx):
        c.execute('SELECT buzz_order, name FROM teams ORDER BY buzz_order')
        embedVar = discord.Embed(title="Buzz Order", description="", color=0x00ff00)
        for row in c.fetchall():
                if row[0] == -1:
                        continue
                embedVar.add_field(name="Position {0}".format(row[0]),value="{0}".format(row[1]), inline=False)
        await ctx.send(embed=embedVar)

@bot.command(name='leave', help="Leave current team")
async def leave_team(ctx):
        # team = get_team(ctx.message.author.id)
        # if team == "":
        #         await ctx.send("You're not in a team!")
        # else:
        #         team_data[team].remove(ctx.message.author.id)
        #         await ctx.send("{0} has left team {1}".format(ctx.message.author.display_name, team))
        #         if len(team_data[team]) == 0:
        #                 del team_data[team]
        c.execute('SELECT team_id, name FROM members m INNER JOIN teams t ON m.team_id = t.id WHERE user_id = ?', (ctx.message.author.id,))
        row = c.fetchone()
        if row:
                c.execute('DELETE FROM members WHERE user_id = ?', (ctx.message.author.id,))
                await ctx.send("{0} has left team {1}".format(ctx.message.author.display_name, row[1]))
                c.execute('SELECT * FROM members m INNER JOIN teams t ON m.team_id = t.id WHERE t.id = ?', (row[0],))
                row2 = c.fetchone()
                if not row2:
                        c.execute('DELETE FROM teams WHERE id = ?', (row[0],))
                conn.commit()
        else:
                await ctx.send("You're not in a team!")

@bot.command(name='fakepoint', help="Yeah you would need help lol")
async def award_participation_trophy(ctx, team_name):
        # if team_name in team_data:
        #         embedVar = discord.Embed(title="Participation Award!", description="Congratulations team {0}, you've been awarded a participation trophy courtesy of {1}".format(team_name, ctx.message.author.display_name), color=0x00ff00)
        #         await ctx.send(embed=embedVar)
        # else:
        #         await ctx.send("That's not a team you monkey")
        c.execute('SELECT name FROM teams WHERE name = ?', (team_name,))
        row = c.fetchone()
        if row:
                embedVar = discord.Embed(title="Participation Award!", description="Congratulations team {0}, you've been awarded a participation trophy courtesy of {1}".format(team_name, ctx.message.author.display_name), color=0xffff00)
                embedVar.set_image(url="https://i.kym-cdn.com/entries/icons/original/000/010/566/060.png")
                await ctx.send(embed=embedVar)
        else:
                await ctx.send("That's not a team you monkey")

@bot.command(name='endgame', help='Ends the game and shows final results. Usage ![endgame, eg, end]', aliases=['eg','end'])
async def end_game(ctx):
        # if ctx.message.author.id == host_id:
        #         team_name = max(team_points, key=lambda key: team_points[key])
        #         await ctx.send("Congratulations team {0}, you win!".format(team_name))
        #         message = ""
        #         for name in team_data:
        #                 message += '{0}: {1}\n'.format(name, team_points[name])
        #         await ctx.send(message)
        # else:
        #         await ctx.send("Nice try buddy")
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                c.execute('SELECT name FROM teams ORDER BY points LIMIT 1')
                row = c.fetchone()
                await ctx.send("Congratulations team {0}, you win!".format(row[0]))
                embedVar = discord.Embed(title="Final Scores", description="")
                c.execute('SELECT name, points FROM teams ORDER BY points')
                for row in c.fetchall():
                        plural = 'points'
                        if row[1] == 1:
                                plural = 'point'
                        embedVar.add_field(name='{0}'.format(row[0]), value='{0} {1}'.format(row[1], plural), inline=False)
                await ctx.send(embed=embedVar)
                c.execute('UPDATE teams SET buzz_order = -1, points = 0')
                c.execute('DELETE FROM rounds')
                conn.commit()

        else:
                await ctx.send("Nice try buddy")


@bot.command(name='stepdown', help="Stop hosting trivia (and lose all credibility)")
async def stop_hosting(ctx):
        host_id = get_host_id()
        if host_id == ctx.message.author.id:
                c.execute('DELETE FROM members WHERE user_id = ?', (ctx.message.author.id,))
                await ctx.send("{0} has stepped down as the host".format(ctx.message.author.display_name))
                conn.commit()
        else:
                await ctx.send("You do not possess the power")

# @bot.command(name='countdown', help="Starts question countdown. Usage ![countdown, cd]", aliases=['cd'])
# async def start_countdown(ctx):
#       cycles = 0
#       #await ctx.send("LOL")
#       schedule.every(1).seconds.do(edit_message, ctx)
#       while True:
#               if cycles < 10:
#                       cycles += 1
#                       schedule.run_pending()
#                       time.sleep(1)
#               else:
#                       break


#helper functions
def get_team(user_id):
        c.execute('SELECT name FROM teams INNER JOIN members ON id=team_id WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if row:
                return row[0]
        else:
                return ""

def get_host_id():
        c.execute('SELECT user_id FROM members WHERE host = 1')
        row = c.fetchone()
        if row:
                return row[0]
        else:
                return 0

def get_current_round():
        c.execute('SELECT id FROM rounds WHERE active = 1')
        row = c.fetchone()
        if row:
                return row[0]
        else:
                return -1

def get_recent_round():
        c.execute('SELECT MAX(id) FROM rounds')
        row = c.fetchone()
        if not row or row[0] == None:
                return -1
        else:
                return row[0]

# async def edit_message(ctx):
#         await ctx.send("hi")

bot.run(TOKEN)
