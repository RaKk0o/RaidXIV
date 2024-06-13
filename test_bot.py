import os
import discord
from discord.ext import commands
from discord import app_commands
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')
    await bot.tree.sync()

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        logging.info(f'We have logged in as {self.user}')
        await self.tree.sync()

client = MyClient()
bot = commands.Bot(command_prefix="!", intents=intents)

@client.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!", ephemeral=True)

@client.tree.command(name="ping", description="Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

token = os.getenv('DISCORD_TOKEN')
client.run(token)
