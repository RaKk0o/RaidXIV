import os
import discord
from discord.ext import commands
import logging
from commands.create_event import create_event_command
from commands.edit_event import edit_event_command

# Logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')
    await bot.tree.sync()

# Register commands
bot.tree.add_command(create_event_command)
bot.tree.add_command(edit_event_command)

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)