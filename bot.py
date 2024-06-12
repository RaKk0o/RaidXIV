import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.messages_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Salut ! Je suis ton nouveau bot Discord.')

token = os.getenv('DISCORD_TOKEN')
bot.run(token)