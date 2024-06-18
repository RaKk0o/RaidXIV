import os
import discord
from discord.ext import commands
import logging
from bot_config import intents, bot
from event_commands import create_event, edit_event

logging.basicConfig(level=logging.INFO)

@bot.event
async def on_ready():
    logging.info(f"We have logged in as {bot.user}")
    await bot.tree.sync()

token = os.getenv("DISCORD_TOKEN")
bot.run(token)