import discord 
from discord.ext import commands, tasks

import html
import random
import asyncio
import requests
from typing import Optional

from settings import BOT_CHANNEL_ID
from utils import log, get_data, upd_data, get_value, new_user, get_user_data

class Games(commands.Cog):
	def __init__(self,bot):
		self.bot : commands.Bot = bot

		#traveler.start(bot=self.bot)


@tasks.loop()
async def traveler(*, bot: commands.Bot):
	# get the bot channel and make sure it is not none
	bot_channel = await bot.fetch_channel(BOT_CHANNEL_ID)
	assert isinstance(bot_channel, discord.TextChannel)

	# 17 science&nature, 18 computer, 19 maths, 22 geography, 24 politics, 27 animals
	r = random.choice([17, 18, 19, 22, 24, 27])
	url = f"https://opentdb.com/api.php?amount=1&category={r}"

	response = requests.get(url)
	data = response.json()

	if data["response_code"] != 0:

		return log('WARNING', "opentdb api returned 0 response code")
	
	
	# extract the data
	category:str = data["results"][0]["category"]
	difficulty:str = data["results"][0]["difficulty"]

	question_type:str = data["results"][0]["type"]
	# convert html entities to normal unicode text
	question:str = html.unescape(data["results"][0]["question"])
	correct_answer:str = html.unescape(data["results"][0]["correct_answer"])
	incorrect_answers:list = list(map(html.unescape, data["results"][0]["incorrect_answers"]))

	# create a list of answers and randomize them
	answers = []
	answers.append(correct_answer)
	answers.extend(incorrect_answers)
	random.shuffle(answers)

	correct_answer_index = answers.index(correct_answer)

	# create embed
	E = discord.Embed(title='Traveler', description=f"**{question}**")
	E.description = f"## **{question}**\n\n"
	E.set_footer(text=f"Category: {category} | Difficulty: {difficulty} | Type: {question_type}")
	E.set_thumbnail(url="https://media.discordapp.net/attachments/709313685226782751/1127893104402386966/traveler.png")

	if difficulty == "easy":
		E.color = discord.Color.green()
	elif difficulty == "medium":
		E.color = discord.Color.gold()
	elif difficulty == "hard":
		E.color = discord.Color.red()
	
	# check if it will be a traveler or a robber : traveler = 1 and robber = 0
	traveler = random.getrandbits(1)
	if traveler:
		photo = "https://media.discordapp.net/attachments/709313685226782751/1127893104402386966/traveler.png"
	else:
		photo = "https://cdn.discordapp.com/attachments/709313685226782751/1205143937052839946/bandit.png"

	# handle the correct and incorrect cases
	async def correct(inter:discord.Interaction):
		E = discord.Embed(title="Correct!", color=discord.Color.green())
		E.set_thumbnail(url=photo)

		# user_id : {user data}
		user_data = get_user_data(inter.user.id)
		if traveler:
			value = get_value(user_data) 
		else:
			value = int(get_value(user_data)*1.5)

		user_data["roses"] += value
		user_data["ideas"] += 7

		upd_data(user_data, f"games/users/{inter.user.id}")

		if traveler:
			E.description = f"You earned **{value}🌹** and **7💡**"
		else:
			E.description = f"The robber is impressed by your knowledge! You earned **{value}🌹** and **7💡**"

		await inter.followup.send(inter.user.mention, embed=E)

	async def incorrect(inter:discord.Interaction):
		E = discord.Embed(title="Incorrect!", color=discord.Color.red())
		E.set_thumbnail(url=photo)

		# user_id : {user data}
		user_data = get_user_data(inter.user.id)
		robber_money=0
		E.description = f"The correct answer was **{correct_answer}**\n"
		if traveler:
			value = 50
			E.description += "The traveler left **50🌹** by accident on the ground" 
		else:

			double_collect_value = get_value(user_data)*2
			value = get_value(user_data)*(-2)
			
		
		
		if user_data["roses"]<0 and not traveler:
			E.description += f"You're already in debt so the robber didn't take you anything"
		else:
			robber_money=(-1)*value
			if user_data["roses"]+value<=0:
				robber_money=user_data["roses"]
			user_data["roses"] += value
			if not traveler:
				if user_data["roses"]<0:
					user_data["roses"]=-1
					E.description += f"The robber took you all of your roses 🌹"
				else:
					E.description += f"The robber took you **{double_collect_value}** 🌹"
				robber_money += get_data(f"games/robber_total")
				upd_data(robber_money, "games/robber_total")
			upd_data(user_data, f"games/users/{inter.user.id}")
		await inter.followup.send(inter.user.mention, embed=E)

	# subclass of discord.ui.Button, all buttons will have the same callback (no need for functions)
	class CallbackButton(discord.ui.Button):
		def __init__(self, parent_view:'B_choices', *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.parent_view = parent_view

		async def callback(self, inter: discord.Interaction):
			await inter.response.defer()

			user_data = get_user_data(inter.user.id)
			fail_next = False
			if "fail_next_traveler" in user_data["effects"]:
				user_data["effects"].remove("fail_next_traveler")
				upd_data(user_data["effects"], f"games/users/{inter.user.id}/effects")
				await incorrect(inter)
				fail_next = True
			else:
				if question_type == "boolean":
					if correct_answer.upper() == self.label:
						await correct(inter)
					else:
						await incorrect(inter)

				else:
					if str(correct_answer_index+1) == self.label:
						await correct(inter)
					else:
						await incorrect(inter)
			if fail_next:
				await inter.followup.send("You had 100% chances of losing today... ", ephemeral=True)
			if isinstance(self.parent_view.message, discord.Message):
				await self.parent_view.message.delete()
			self.parent_view.stop()

	class B_choices(discord.ui.View):
		def __init__(self, timeout=3600):
			super().__init__(timeout=timeout)
			self.message : Optional[discord.Message]

		# traveler leaves: removes message after timeout
		async def on_timeout(self):
			try:
				if isinstance(self.message, discord.Message):
					await self.message.delete()
			except discord.NotFound:
				pass

	# add the necessary buttons
	b_choices = B_choices()
	if question_type == "boolean":
		b_choices.add_item(CallbackButton(parent_view=b_choices, label="TRUE", style=discord.ButtonStyle.green))
		b_choices.add_item(CallbackButton(parent_view=b_choices, label="FALSE", style=discord.ButtonStyle.red))
	else:
		for i in range(4):
			E.description += f"{i+1}. {answers[i]}\n"
			b_choices.add_item(CallbackButton(parent_view=b_choices, label=str(i+1), style=discord.ButtonStyle.blurple))

	b_choices.message = await bot_channel.send(embed=E, view=b_choices, silent=True)

	await b_choices.wait()

	# come back in 2 to 10 hours
	random_time = random.randint(7200, 36000)

	await asyncio.sleep(random_time)

async def setup(bot:commands.Bot):
	await bot.add_cog(Games(bot))
