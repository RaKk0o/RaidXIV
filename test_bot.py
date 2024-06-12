import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Charger les variables d'environnement depuis le fichier .env

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    await bot.close()  # Arrêter le bot après la connexion

# Lire le token depuis les variables d'environnement
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
