import os
import discord
from discord.ext import commands
from discord import app_commands
import uuid
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionnaire pour stocker les informations des événements
events = {}

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')
    await bot.tree.sync()

@bot.tree.command(name="create_event", description="Créer un nouvel événement")
async def create_event(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # Définir les informations de l'événement pour simplifier
    event_id = str(uuid.uuid4())
    title = "Titre de l'événement"
    description = "Description de l'événement"
    date = "14/06/2024"
    time = "16:30"
    organizer_id = interaction.user.id

    events[event_id] = {
        'title': title,
        'description': description,
        'date': date,
        'time': time,
        'organizer': organizer_id
    }

    # Debug: Log event details to ensure it is stored
    logging.info(f"Event created: {event_id} - {events[event_id]}")

    await interaction.followup.send(f"Événement créé avec succès! ID: {event_id}", ephemeral=True)

@bot.tree.command(name="edit_event", description="Éditer un événement")
@app_commands.describe(event_id="L'identifiant de l'événement à modifier")
async def edit_event(interaction: discord.Interaction, event_id: str):
    if event_id in events:
        event = events[event_id]
        await interaction.response.send_message(f"Modification de l'événement : {event['title']} ({event['date']} à {event['time']})", ephemeral=True)
    else:
        await interaction.response.send_message("Cet événement n'existe pas.", ephemeral=True)

@edit_event.autocomplete("event_id")
async def edit_event_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = [
        app_commands.Choice(name=f"{event_id} | {event['date']} | {event['title']}", value=event_id)
        for event_id, event in events.items() if current.lower() in event_id.lower() or current.lower() in event['title'].lower()
    ]
    return choices

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
