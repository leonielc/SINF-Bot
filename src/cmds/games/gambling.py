import discord 
from discord import app_commands, ui
from discord.ext import commands, tasks

import random
import datetime as dt
from typing import Literal
import asyncio

from settings import BOT_CHANNEL_ID
from utils import get_data, upd_data, GetLogLink, get_amount, is_cutie, UnexpectedValue, get_value, random_avatar, get_belgian_time, get_user_data

class GamblingHelper:
	def __init__(self, bot:commands.Bot):
		self.bot : commands.Bot = bot
	
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
		roulette = False
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
			
		roulette = False
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
		if 8 > r > 5:
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

async def setup(bot:commands.Bot):
	await bot.add_cog(Gambling(bot))
