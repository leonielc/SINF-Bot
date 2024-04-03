import discord 
from discord import app_commands
from discord.ext import commands

import random
import datetime as dt
from typing import Literal

from utils import get_data, upd_data, GetLogLink, get_amount, is_cutie, UnexpectedValue, get_value, random_avatar
from cmds.games.games import Games, traveler




class GamblingHelper():
	def __init__(self, bot:commands.Bot):
		self.bot : commands.Bot = bot

	async def create_next_traveler(self, inter:discord.Interaction):
		E = discord.Embed(title="Create next traveler", color=discord.Color.purple())
		E.set_author(name=inter.user.name, icon_url=await GetLogLink(self.bot,str(inter.user.display_avatar)))
		E.set_thumbnail(url="https://media.discordapp.net/attachments/709313685226782751/1128082089397465218/thonking.gif")

		# id : amount
		True_or_False= {}
		MCQ = {}

		# create modal that write the question
		class GetBet(discord.ui.Modal):
			def __init__(self, message:discord.Message, question_type:Literal["True or False", "MCQ"]):
				self.message = message
				self.question_type = question_type
				super().__init__(title="Create the next traveler!")
				if self.question_type=="MCQ":
					question = discord.ui.TextInput(label="Question", default='', min_length=1, max_length=500)
					answer = discord.ui.TextInput(label="Answer", default='', min_length=1, max_length=50)
					answer_2 = discord.ui.TextInput(label="Possibility 2", default='', min_length=1, max_length=50)
					answer_3 = discord.ui.TextInput(label="Possibility 3", default='', min_length=1, max_length=50)
					answer_4 = discord.ui.TextInput(label="Possibility 4", default='', min_length=1, max_length=50)
				else:
					question = discord.ui.TextInput(label="Question", default='', min_length=0, max_length=500)
					answer = discord.ui.TextInput(label="True or False (The answer)", default='', min_length=0, max_length=50)
					
			async def on_submit(self, inter2: discord.Interaction):
				# get the amount 
				question_type = self.question_type
				if self.question_type == "Vrai_Faux":
					True_or_False[inter2.user.id] = True

				else:
					MCQ[inter2.user.id] = True

				#await self.message.edit(embed=E)

				#await inter2.response.send_message(f'bet set!', ephemeral=True)

		# create the view that asks users to bet
		class FirstView(discord.ui.View):
			def __init__(self, timeout:float):
				super().__init__(timeout=timeout)
				self.message_id : int

			@discord.ui.button(label="True or False",style=discord.ButtonStyle.success)
			async def True_False(self, inter2: discord.Interaction, _: discord.ui.Button):
				if inter2.user.id in MCQ or inter2.user.id in True_or_False:
					return await inter2.followup.send(f'You already bet', ephemeral=True)
				
				# fetch the message back (>15 mins)
				if not isinstance(inter2.channel, discord.TextChannel):
					raise UnexpectedValue("inter2.channel is not a discord.TextChannel")
				
				message = await inter2.channel.fetch_message(self.message_id)

				await inter2.response.send_modal(GetBet(message,"True or False"))
				

				# update timeout so it stays on time
				self.timeout = time_ends - int(dt.datetime.now().timestamp())

			@discord.ui.button(label="MCQ (4 possibilities)",style=discord.ButtonStyle.danger)
			async def MCQ(self, inter2: discord.Interaction, _: discord.ui.Button):
				if inter2.user.id in MCQ or inter2.user.id in True_or_False:
					return await inter2.followup.send("Cannot interact with this message", ephemeral=True)

				# fetch the message back (>15 mins)
				if not isinstance(inter2.channel, discord.TextChannel):
					raise UnexpectedValue("inter2.channel is not a discord.TextChannel")
				
				message = await inter2.channel.fetch_message(self.message_id)

				await inter2.response.send_modal(GetBet(message, "MCQ"))

				# update timeout so it stays on time
				self.timeout = time_ends - int(dt.datetime.now().timestamp())

		# +2 for the time it takes to send the message
		time_ends = int(dt.datetime.now().timestamp()) + 300 + 2
		left = time_ends - int(dt.datetime.now().timestamp())

		firstView = FirstView(left)

		message = await inter.followup.send(f"<t:{time_ends}:R>", embed=E,view=firstView)

		if not isinstance(message, discord.Message):
			raise UnexpectedValue("message is not a discord.Message")
		
		firstView.message_id = message.id

		await firstView.wait()

		# fetch the message back (>15 mins)
		if not isinstance(inter.channel, discord.TextChannel):
			raise UnexpectedValue("channel is not a discord.TextChannel")

		E = discord.Embed(title="Roulette", color=discord.Color.gold())
		E.description = f"Traveler set. It's coming..."

	async def change_next_method(self, inter : discord.Interaction, bet : str, gambling_func):
		gambling_funcs = ["roll", "flip", "ladder"]
		gambling_funcs.remove(gambling_func.__name__)
		choice = random.choice(gambling_funcs)
		if choice=="ladder":
			await self.ladder(inter, bet)
		elif choice == "flip":
			guess : Literal["heads", "tails"] = random.choice(["heads", "tails"])
			await self.flip(inter, bet, guess)
		elif choice == "roll":
			await self.roll(inter, bet)

	async def change_next_gain(self, E : discord.Embed, inter:discord.Interaction, multiplicator : float, user_data : dict):
		if "next_gain_x3" in user_data["effects"]:
			multiplicator = 3
			user_data["effects"].remove("next_gain_x3")
			user_data["effects"].remove("next_gain")
			E.color = discord.Color.purple()
			E.description = "Wow! You tripled your gain!"
			await inter.followup.send(embed=E)

		elif "next_gain_/3" in user_data["effects"]:
			multiplicator = 1/3
			user_data["effects"].remove("next_gain_/3")
			user_data["effects"].remove("next_gain")
			E.color = discord.Color.purple()
			E.description = "Haha, your gain was divided by three!"
			await inter.followup.send(embed=E)

		elif "next_gain_x10" in user_data["effects"]:
			multiplicator = 10
			user_data["effects"].remove("next_gain_x10")
			user_data["effects"].remove("next_gain")
			E.color = discord.Color.purple()
			E.description = "Wow! Your gain has grown by a factor 10!"
			await inter.followup.send(embed=E)
			
		elif "next_gain_/10" in user_data["effects"]:
			multiplicator = 1/10
			user_data["effects"].remove("next_gain_/10")
			user_data["effects"].remove("next_gain")
			E.color = discord.Color.purple()
			E.description = "Haha, your gain was divided by ten!"
			await inter.followup.send(embed=E)

		return multiplicator
	
	async def embed(self, inter : discord.Interaction, E : discord.Embed):
		url = random_avatar()
		if inter.user.avatar:
			url = inter.user.avatar.url
		E.set_author(name=inter.user.display_name, url = await GetLogLink(self.bot, url))
		E.set_footer(text="Roulette by Scylla and Ceisal")
		E = discord.Embed(title="Roulette")
		return E
	
	async def is_allowed_to_bet(self, inter:discord.Interaction, bet:str) -> tuple[int, discord.Embed, dict]:
		E = discord.Embed()
		E.color = discord.Color.green()
		E.set_author(name=inter.user.name, icon_url=await GetLogLink(self.bot, inter.user.display_avatar.url))

		try :
			user_data : dict = get_data(f"games/users/{inter.user.id}")
		except :
			E.description = f"{inter.user.mention}, You don't have an account yet"
			E.color = discord.Color.red()
			return 0, E, {}

		
		if "next_bet_all" in user_data["effects"] and bet!="all":
			bet="all"


		# translate the user request into a number
		amount = get_amount(user_data["roses"], bet)


		if amount is None or amount < 0:
			E.description = f"{inter.user.mention}, You need to bet a valid amount of 🌹"
			E.color = discord.Color.red()
			return 0, E, user_data

		if amount < 2:
			E.description = f"{inter.user.mention}, You need to bet at least 2🌹"
			E.color = discord.Color.red()

		elif user_data["roses"] < amount:
			E.description = f"{inter.user.mention}, You don't have enough 🌹"
			E.color = discord.Color.red()

		return amount, E, user_data

	async def check(self, inter:discord.Interaction) -> tuple[discord.Embed, dict]:
		E = discord.Embed()
		E.color = discord.Color.green()
		E.set_author(name=inter.user.name, icon_url=await GetLogLink(self.bot, inter.user.display_avatar.url))

		try :
			user_data : dict = get_data(f"games/users/{inter.user.id}")
		except :
			E.description = f"{inter.user.mention}, You don't have an account yet"
			E.color = discord.Color.red()
			return E, {}

		return E, user_data


	async def roll(self, inter:discord.Interaction, bet:str):
		try:
			await inter.response.defer()
		except:
			pass

		amount, E, user_data = await self.is_allowed_to_bet(inter, bet)
		# if the already has a description, an issue was found
		if E.description is not None:
			return await inter.followup.send(embed=E)
		
		r = random.randint(1,100)
		for element in user_data["effects"]:
			if "gain" or "bet" in element:
				roulette = True

		if roulette:
			E = await self.embed(inter, E)

		multiplicator = 1
		double = False
		divide = False
		if "change_bet_method" in user_data["effects"]:
			user_data["effects"].remove("change_bet_method")
			upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
			return await self.change_next_method(inter, bet, self.roll)

		if r >= 70:
			multiplicator  = await self.change_next_gain(E, inter, multiplicator, user_data)
		elif "chances_next_bet_x2" in user_data["effects"]:
			user_data["effects"].remove("chances_next_bet_x2")
			double=True
			E.color = discord.Color.purple()
			E.description = "Wow! You had twice the chance to win!"
			await inter.followup.send(embed=E)
		elif "chances_next_bet_/2" in user_data["effects"]:
			user_data["effects"].remove("chances_next_bet_/2")
			divide=True
			E.color = discord.Color.purple()
			E.description = "Well, you had half the chance to win this one"
			await inter.followup.send(embed=E)
		
		if double:
			r = max(random.randint(1,100),random.randint(1,100))
		elif divide:
			r = min(random.randint(1,100),random.randint(1,100))
		cash=amount
		if r == 100:
			#Il y a 2 int, un pour arrondir le résultat, un autre pour la division
			cash = int(int(amount*10)*multiplicator)
			E.description = f"{inter.user.mention}, You rolled a 100 and won **{cash}🌹!** 👑"
			E.color = discord.Color.gold()
		elif r >= 90:
			cash = int(int(amount*4)*multiplicator)
			E.description = f"{inter.user.mention}, You rolled a {r} and won **{cash}🌹!** 🎯"
			E.color = discord.Color.green()
		elif r >= 70:
			cash = int(int(amount*2)*multiplicator)
			E.description = f"{inter.user.mention}, You rolled a {r} and won **{cash}🌹!** 🎉"
			E.color = discord.Color.green()
		elif r==1:
			E.description = f"{inter.user.mention}, You rolled a 1 and kept your **{cash}🌹!** ✨"
			E.color = discord.Color.dark_purple()
		else: 
			cash = 0
			E.color = discord.Color.red()
			E.description = f"{inter.user.mention}, You rolled a {r} and won nothing..."

		user_data["roses"] += - amount + cash
		upd_data(user_data, f"games/users/{inter.user.id}")

		await inter.followup.send(embed=E) 

	async def flip(self, inter:discord.Interaction, bet:str, guess:Literal["heads", "tails"]):
		try:
			await inter.response.defer()
		except:
			pass

		amount, E, user_data = await self.is_allowed_to_bet(inter, bet)

		# if the already has a description, an issue was found
		if E.description is not None:
			return await inter.followup.send(embed=E)
		roulette=False
		for element in user_data["effects"]:
			if "gain" or "bet" in element:
				roulette = True
				
		if roulette:
			E = await self.embed(inter, E)
		choice = random.choice(["heads", "tails"])

		if "change_bet_method" in user_data["effects"]:
			user_data["effects"].remove("change_bet_method")
			upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
			return await self.change_next_method(inter, bet, self.flip)
			
		multiplicator=1
		divide=False
		double=False

		if "next_bet_all" in user_data["effects"]:	
			user_data["effects"].remove("next_bet_all")
			upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
			E.description = f"Oops you accidently bet all"
			E.colour = discord.Colour.purple()
			await inter.followup.send(embed=E)
		
		elif guess==choice and "next_gain" in user_data["effects"]:
			multiplicator  = await self.change_next_gain(E, inter, multiplicator, user_data)
			
		elif "chances_next_bet_x2" in user_data["effects"]:
			double=True
			user_data["effects"].remove("chances_next_bet_x2")
		elif "chances_next_bet_/2" in user_data["effects"]:
			divide=True
			user_data["effects"].remove("chances_next_bet_/2")
		
		double_tails=0
		double_heads=0
		divide_heads=0
		divide_tails=0

		if double:
			if guess=="heads":
				double_heads=1
			else:
				double_tails=1
		elif divide:
			if guess=="heads":
				divide_tails=1
			else:
				divide_heads=1

		if double or divide:
			choice = random.choices(["heads", "tails"], [1 + double_heads + divide_heads, 1 + double_tails + divide_tails])[0]

		if choice == "tails":
			image = "https://media.discordapp.net/attachments/709313685226782751/1126924584973774868/ttails.png"
		else:
			image = "https://media.discordapp.net/attachments/709313685226782751/1126924585191882833/hheads.png"
		E.title = f"{choice.capitalize()}!"
		E.set_image(url=image)


		if guess == choice:
			cash = int(int(amount*1.8)*multiplicator)
			E.description = f"You guessed it right and won **{cash}🌹!** 🎉"
			E.color = discord.Color.green()
		else:
			cash = 0
			E.color = discord.Color.red()
			E.description = f"You guessed it wrong..."
			
		user_data["roses"] += - amount + cash
		upd_data(user_data, f"games/users/{inter.user.id}")

		await inter.followup.send(embed=E)



	async def ladder(self, inter:discord.Interaction, bet:str):
		try:
			await inter.response.defer()
		except:
			pass

		amount, E, user_data = await self.is_allowed_to_bet(inter, bet)
		# if the already has a description, an issue was found
		if E.description is not None:
			return await inter.followup.send(embed=E)
		
		for element in user_data["effects"]:
			if "gain" or "bet" in element:
				roulette = True
				
		if roulette:
			E = await self.embed(inter, E)

		r = random.randint(1,8)
		multiplicator=1
		double=False
		divide=False
		if "change_bet_method" in user_data["effects"]:
			user_data["effects"].remove("change_bet_method")
			upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
			return await self.change_next_method(inter, bet, self.ladder)

		elif r>=6:
			multiplicator  = await self.change_next_gain(E, inter, multiplicator, user_data)
		elif "chances_next_bet_x2" in user_data["effects"]:
			user_data["effects"].remove("chances_next_bet_x2")
			double=True
		elif "chances_next_bet_/2" in user_data["effects"]:
			user_data["effects"].remove("chances_next_bet_/2")
			divide=True

		
		
		
		if double:
			r = max(random.randint(1,8),random.randint(1,8))
		elif divide:
			r = min(random.randint(1,8),random.randint(1,8))

		if r <= 4:
			E.color = discord.Color.red()
		if r == 5: 
			E.color = discord.Color.blurple()
		if 8>r>5:
			E.color = discord.Color.green()
		if r == 8:
			E.color = discord.Color.gold()

		equivalents = {
			1: 0.1,
			2: 0.3,
			3: 0.4,
			4: 0.5,
			5: 1.0,
			6: 1.2,
			7: 1.5,
			8: 2.2
		}
		display = [
			"╠══╣||x2.2||",
			"╠══╣||x1.5||",
			"╠══╣||x1.2||",
			"╠══╣||x1.0||",
			"╠══╣||x0.5||", 
			"╠══╣||x0.4||", 
			"╠══╣||x0.3||",
			"╠══╣||x0.1||", 
		]

		display[8-r] = display[8-r].replace("||", "**") + ' ⬅️'
		E.description = "\n".join(display)

		cash = int(int(amount * equivalents[r])*multiplicator)

		E.add_field(name="Multiplier", value=f"**x{equivalents[r]}**")
		E.add_field(name="Won", value=f"**{cash}🌹 **")

		user_data["roses"] += - amount + cash
		upd_data(user_data, f"games/users/{inter.user.id}")

		await inter.followup.send(embed=E)

	async def roulette(self, inter:discord.Interaction, other_user:discord.Member):
		assert inter.guild
		
		has_been_answered = False


		E, user_data = await self.check(inter)

		
		if user_data["candies"]<1:
			E.description = f"{inter.user.mention}, You don't have enough 🍬"
			E.color = discord.Color.red()
			return await inter.response.send_message(embed=E)
		
		try :
			other_user_data : dict = get_data(f"games/users/{other_user.id}")
		except :
			return await inter.response.send_message("This user doesn't have an account", ephemeral=True)
		
		if other_user_data==user_data:
			return await inter.response.send_message("You can't choose yourself", ephemeral=True)
		
		url = random_avatar()
		if inter.user.avatar:
			url = inter.user.avatar.url
		E.set_author(name=inter.user.display_name, url = await GetLogLink(self.bot, url))
		E.set_footer(text="Roulette by Scylla and Ceisal")
		E = discord.Embed(title="Roulette")
		E.description = f"{inter.user.mention} used the roulette! It costs only one 🍬."
		E.color = discord.Color.purple()

		await inter.response.send_message(embed = E)
		upd_data(user_data["candies"]-1, f"games/users/{inter.user.id}/candies")

		consequences = {
			"level_up" : 2,  #ça marche
			"level_down" : 2, #ça marche
			"tech_up" : 5, #ça marche
			"tech_down" : 5, #ça marche
			"timeout_someone" : 5, #ça marche
			"timeout_myself" : 7.5, #ça marche
			"next_bet_all" : 5, #ça marche
			"wordle_guess_reduced" : 5, #ça marche
			#local_sum = 31.5
			"traveler_spawn" : 5.5, # ça marche
			"create_next_traveler" : 8, # je garde ça pour plus tard
			"fail_next_traveler" : 5, # ça marche
			#local_sum = 18.5
			"chances_next_bet_x2" : 4, # ça marche 
			"chances_next_bet_/2" : 4, # ça marche
			"next_gain_x3" : 4, # ça marche
			"next_gain_/3" : 4, # ça marche
			"next_bet_someone_else" : 3, # ça marche
			"steal_collect_x2" : 3, # ça marche
			"choose_name_level_up" : 3, # ça marche 
			"choose_name_level_down" : 3, # ça marche
			"next_collect_x3" : 3, # ça marche
			"next_gain_x10" : 2, # ça marche
			"next_gain_/10" : 2, # ça marche
			"change_bet_method" : 5, # ça marche
			"free_flip_when_collect" : 5, # ça marche
			"bank_double": 2, # ça marche
			"bank_robbery" : 2, # ça marche
			#local_sum = 46
			#total_sum = 96
		}

		#Modify this line to make tests.
		cons = random.choices(list(consequences.keys()), list(consequences.values()))[0]
		cons = "create_next_traveler"
		print(cons) 


		has_been_answered = False

		
		url = random_avatar()

		if inter.user.avatar:
			url = inter.user.avatar.url
		E.set_author(name=inter.user.display_name, url = await GetLogLink(self.bot, url))
		E.set_footer(text="Roulette by Scylla and Ceisal")
		E = discord.Embed(title="Roulette")
		if cons=="level_up":
			has_been_answered = True
			user_data["level"]+=1
			upd_data(user_data["level"], f"games/users/{inter.user.id}/level")
			E.colour = discord.Colour.green()
			E.description = f"Congratulations you leveled-up to level **{user_data['level']}**!"
			await inter.followup.send(embed=E)
			
		elif cons=="level_down":
			has_been_answered = True
			if user_data["level"]>0:
				user_data["level"]-=1
				upd_data(user_data["level"], f"games/users/{inter.user.id}/level")
				E.colour = discord.Colour.red()
				E.description = f"Haha noob you leveled-down to level **{user_data['level']}**"
				await inter.followup.send(embed=E)
			else:
				E.colour = discord.Colour.red()
				E.description = f"You didn't level down cause you're already level 0..."
				await inter.followup.send(embed=E)

		elif cons=="tech_up":
			has_been_answered = True
			user_data["tech"]+=1
			upd_data(user_data["tech"], f"games/users/{inter.user.id}/tech")
			E.colour = discord.Colour.purple()
			E.description = f"Congratulations you upgraded your tech to level **{user_data['tech']}**:gear:!"
			await inter.followup.send(embed=E)

		elif cons=="tech_down":
			has_been_answered = True
			if user_data["tech"]>0:
				user_data["tech"]-=1
				upd_data(user_data["tech"], f"games/users/{inter.user.id}/tech")
				E.colour = discord.Colour.purple()
				E.description = f"Haha noob you downgraded your tech to level **{user_data['tech']}**:gear:!"
				await inter.followup.send(embed=E)
			else:
				E.colour = discord.Colour.purple()
				E.description = f"You didn't tech level down cause you're already level 0..."
				await inter.followup.send(embed=E)

		elif cons=="timeout_someone": #inter user -> discord member 
			has_been_answered = True
			try :
				await other_user.timeout(dt.timedelta(minutes=30), reason="haha mskn")
			except : 
				member = inter.guild.get_member(inter.user.id)
				assert member
				await member.timeout(dt.timedelta(minutes=30), reason="haha mskn encore plus")
				E.description = f"{inter.user.mention} tried to timeout {other_user.mention} and got karmadd"
				await inter.followup.send(embed=E)
				return
			
			E.colour = discord.Colour.green()
			E.description = f"{inter.user.mention} got {other_user.mention} timed out! I see some beef coming." 
			await inter.followup.send(embed=E)

		elif cons == "traveler_spawn":
			has_been_answered = True
			traveler.start(bot=self.bot)
			try :
				await other_user.timeout(dt.timedelta(minutes=30), reason="haha mskn")
			except : 
				E.description = f"{inter.user.mention} tried to timeout {other_user.mention} and got karmadd"
			E.colour = discord.Colour.purple()
			E.description = f"Look, there, a traveler!" 
			await inter.followup.send(embed=E)
		
		elif cons=="timeout_myself":
			has_been_answered = True
			member = inter.guild.get_member(inter.user.id)
			assert member #j'ai un petit pb avec modal ça marche pas
			await member.timeout(dt.timedelta(minutes=60), reason="haha mskn encore plus")
			E.description = f"{inter.user.mention} got themselves timed out. See you later!" 
			await inter.followup.send(embed=E)

		elif cons == "bank_robbery":
			has_been_answered = True
			robber_money = get_data(f"games/users/{inter.user.id}/bank/roses")
			robber_money += get_data(f"games/robber_total")
			upd_data(0, f"games/users/{inter.user.id}/bank/roses")
			upd_data(robber_money, "games/robber_total")
			E.colour = discord.Colour.purple()
			E.description = f"{inter.user.mention} your bank got robbed.\nThe Robber got all the money you put in there."
			await inter.followup.send(embed=E)

		elif cons == "bank_double":
			has_been_answered = True
			double_money = get_data(f"games/users/{inter.user.id}/bank/roses")
			double_money+=double_money
			upd_data(double_money, f"games/users/{inter.user.id}/bank/roses")
			E.colour = discord.Colour.purple()
			E.description = f"{inter.user.mention} your bank got multiplied by two!"
			await inter.followup.send(embed=E)

		elif cons == "steal_collect_x2":
			has_been_answered = True
			value = get_value(other_user_data)*2
			user_data["roses"] += value
			other_user_data["roses"] -= value
			upd_data(other_user_data["roses"], f"games/users/{other_user.id}/roses")
			upd_data(user_data["roses"], f"games/users/{inter.user.id}/roses")

			E.colour = discord.Colour.purple()
			E.description = f"{inter.user.mention} stole two collects from {other_user.mention}!"
			await inter.followup.send(embed=E)

		elif cons=="choose_name_level_up":
			has_been_answered = True
			other_user_data["level"]+=1
			upd_data(other_user_data["level"], f"games/users/{other_user.id}/level")
			E.colour = discord.Colour.purple()
			E.description = f"Congratulations you leveled-up {other_user.mention} to level **{other_user_data['level']}**!"
			await inter.followup.send(embed=E)

		elif cons=="choose_name_level_down":
			has_been_answered = True
			other_user_data["level"]-=1
			upd_data(other_user_data["level"], f"games/users/{other_user.id}/level")
			E.colour = discord.Colour.purple()
			E.description = f"Haha, you leveled-down {other_user.mention} to level **{other_user_data['level']}**!"
			await inter.followup.send(embed=E)

		elif cons=="next_bet_all":
			user_data["effects"].append("next_bet_all")


		elif cons=="wordle_guess_reduced":
			user_data["effects"].append("wordle_guess_reduced")

		elif cons == "next_gain_x3":
			user_data["effects"].append("next_gain_x3")
			user_data["effects"].append("next_gain")

		elif cons == "next_gain_/3":
			user_data["effects"].append("next_gain_/3")
			user_data["effects"].append("next_gain")

		elif cons == "next_gain_x10":
			user_data["effects"].append("next_gain_x10")
			user_data["effects"].append("next_gain")

		elif cons == "next_gain_/10":
			user_data["effects"].append("next_gain_/10")
			user_data["effects"].append("next_gain")

		elif cons == "next_bet_someone_else":
			other_user_data["effects"].append("next_bet_all")
			upd_data(other_user_data["effects"], f"games/users/{other_user.id}/effects")

		elif cons == "chances_next_bet_x2":
			user_data["effects"].append("chances_next_bet_x2")

		elif cons == "chances_next_bet_/2":
			user_data["effects"].append("chances_next_bet_/2")

		elif cons == "fail_next_traveler":
			user_data["effects"].append("fail_next_traveler")

		elif cons == "change_bet_method":
			user_data["effects"].append("change_bet_method")

		elif cons == "free_flip_when_collect":
			user_data["effects"].append("free_flip_when_collect")

		elif cons == "next_collect_x3":
			user_data["effects"].append("next_collect_x3")
			
		elif cons == "create_next_traveler":
			print("Start")
			await self.create_next_traveler(inter)
			print("Done")

		
		if not has_been_answered:
			await inter.followup.send("A random effect has been applied to one of you, wait and see...", ephemeral=True)

		upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
class Gambling(commands.Cog):
	def __init__(self,bot):
		self.bot : commands.Bot = bot
		self.GH = GamblingHelper(bot)

	@app_commands.command(description="Rolls a dice")
	@app_commands.checks.cooldown(1, 1, key=lambda i: (i.guild_id, i.user.id))
	@app_commands.guild_only()
	@app_commands.describe(bet="The amount to bet")
	async def roll(self, inter:discord.Interaction, bet:str):
		await self.GH.roll(inter, bet)
	@app_commands.command(description="Flips a coin")
	@app_commands.checks.cooldown(1, 1, key=lambda i: (i.guild_id, i.user.id))
	@app_commands.guild_only()
	@app_commands.describe(bet="The amount to bet", guess="Your guess")
	async def flip(self, inter:discord.Interaction, bet:str, guess:Literal["heads", "tails"]):
		await self.GH.flip(inter, bet, guess)

	@app_commands.command(description="Lucky Ladder, each step has equal chances of occuring")
	@app_commands.checks.cooldown(1, 1, key=lambda i: (i.guild_id, i.user.id))
	@app_commands.guild_only()
	@app_commands.describe(bet="The amount to bet")
	async def ladder(self, inter:discord.Interaction, bet:str):
		await self.GH.ladder(inter, bet)
	
	@app_commands.command(description="Spins the wheel")
	@app_commands.checks.cooldown(1, 1, key=lambda i: (i.guild_id, i.user.id))
	@app_commands.guild_only()
	async def roulette(self, inter:discord.Interaction, other_user:discord.Member):
		await self.GH.roulette(inter, other_user)
	
async def setup(bot:commands.Bot):
	await bot.add_cog(Gambling(bot))