import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Salut ! Je suis ton nouveau bot Discord.')

@bot.command(name='heeelp')
async def hello(ctx):
    await ctx.send('Non.')

token = os.getenv('DISCORD_TOKEN')
bot.run(token)