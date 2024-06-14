import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
from datetime import datetime
import uuid
import logging
from utils.helpers import validate_date, validate_time, CreateEventSelect, CreateEventView
from .buttons import PresenceButton, AbsenceButton, MaybeButton, ReplacementButton

events = {}

async def create_event(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Veuillez créer l'événement en envoyant la commande dans un canal du serveur.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.user.send("Nous allons configurer votre événement. Veuillez répondre aux questions suivantes.")
    
    def check(m):
        return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

    await interaction.user.send("Entrez le titre de l'événement:")
    title = (await interaction.client.wait_for('message', check=check)).content

    await interaction.user.send("Entrez la description de l'événement:")
    description = (await interaction.client.wait_for('message', check=check)).content

    # Validate date
    date_str = await validate_date(interaction, check)

    # Validate time
    time_str = await validate_time(interaction, check)

    guild = interaction.guild
    channels = guild.text_channels
    select_options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]

    view = CreateEventView(select_options)
    await interaction.user.send("Sélectionnez le canal où l'événement sera annoncé:", view=view)
    await view.wait()

    if view.children[0].channel_id is None:
        await interaction.user.send("Aucun canal sélectionné, opération annulée.")
        return

    event_id = str(uuid.uuid4())
    channel_id = view.children[0].channel_id
    events[event_id] = {
        'title': title,
        'description': description,
        'date': date_str,
        'time': time_str,
        'participants': [],
        'absences': [],
        'maybes': [],
        'replacements': [],
        'channel_id': channel_id,
        'organizer': interaction.user.id
    }

    # Debug: Log event details to ensure it is stored
    logging.info(f"Event created: {event_id} - {events[event_id]}")

    await interaction.user.send("L'événement a été créé avec succès!")

    channel = interaction.client.get_channel(channel_id)
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="📅 Date", value=date_str, inline=True)
    embed.add_field(name="⏰ Heure", value=time_str, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Absences", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Peut-être", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Remplacements", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(PresenceButton(event_id))
    view.add_item(AbsenceButton(event_id))
    view.add_item(MaybeButton(event_id))
    view.add_item(ReplacementButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]['message_id'] = message.id
    await interaction.followup.send("L'événement a été annoncé dans le canal sélectionné.", ephemeral=True)

create_event_command = app_commands.Command(
    name="create_event",
    description="Créer un nouvel événement",
    callback=create_event
)
