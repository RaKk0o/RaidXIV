import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

USER_ID = int(os.getenv('NILS_ID'))

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Salut ! Je suis ton nouveau bot Discord.')

@bot.command(name='heeelp')
async def heeelp(ctx):
    await ctx.send('Non.')

@bot.event
async def on_message(message):
    if message.author.id == USER_ID:
        await message.channel.send(f"{message.author.display_name} dans le doute ta gueule.")

    await bot.process_commands(message)

token = os.getenv('DISCORD_TOKEN')
bot.run(token)