import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import uuid
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store event information
events = {}

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')
    await bot.tree.sync()

class CreateEventSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Sélectionnez un canal...", min_values=1, max_values=1, options=options)
        self.channel_id = None

    async def callback(self, interaction: discord.Interaction):
        self.channel_id = int(self.values[0])
        await interaction.response.send_message("Canal sélectionné.", ephemeral=True)
        self.view.stop()

class CreateEventView(View):
    def __init__(self, options):
        super().__init__()
        self.add_item(CreateEventSelect(options))

class PresenceButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.green, label="Présence", custom_id=f"presence_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_presence(interaction)

    async def handle_presence(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event['absences'].remove(user) if user in event['absences'] else None
        event['maybes'].remove(user) if user in event['maybes'] else None
        event['replacements'].remove(user) if user in event['replacements'] else None
        event['participants'].append(user) if user not in event['participants'] else None

        await interaction.followup.send("Votre présence a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
        embed.add_field(name="Date", value=event['date'], inline=True)
        embed.add_field(name="Heure", value=event['time'], inline=True)

        if event['participants']:
            participants = ', '.join([p.name for p in event['participants']])
            embed.add_field(name="Inscriptions", value=participants, inline=False)
        if event['absences']:
            absences = ', '.join([p.name for p in event['absences']])
            embed.add_field(name="Absences", value=absences, inline=False)
        if event['maybes']:
            maybes = ', '.join([p.name for p in event['maybes']])
            embed.add_field(name="Peut-être", value=maybes, inline=False)
        if event['replacements']:
            replacements = ', '.join([p.name for p in event['replacements']])
            embed.add_field(name="Remplacements", value=replacements, inline=False)

        await message.edit(embed=embed)

class AbsenceButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="Absence", custom_id=f"absence_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_absence(interaction)

    async def handle_absence(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event['participants'].remove(user) if user in event['participants'] else None
        event['maybes'].remove(user) if user in event['maybes'] else None
        event['replacements'].remove(user) if user in event['replacements'] else None
        event['absences'].append(user) if user not in event['absences'] else None

        await interaction.followup.send("Votre absence a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
        embed.add_field(name="Date", value=event['date'], inline=True)
        embed.add_field(name="Heure", value=event['time'], inline=True)

        if event['participants']:
            participants = ', '.join([p.name for p in event['participants']])
            embed.add_field(name="Inscriptions", value=participants, inline=False)
        if event['absences']:
            absences = ', '.join([p.name for p in event['absences']])
            embed.add_field(name="Absences", value=absences, inline=False)
        if event['maybes']:
            maybes = ', '.join([p.name for p in event['maybes']])
            embed.add_field(name="Peut-être", value=maybes, inline=False)
        if event['replacements']:
            replacements = ', '.join([p.name for p in event['replacements']])
            embed.add_field(name="Remplacements", value=replacements, inline=False)

        await message.edit(embed=embed)

class MaybeButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="Peut-être", custom_id=f"maybe_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_maybe(interaction)

    async def handle_maybe(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event['participants'].remove(user) if user in event['participants'] else None
        event['absences'].remove(user) if user in event['absences'] else None
        event['replacements'].remove(user) if user in event['replacements'] else None
        event['maybes'].append(user) if user not in event['maybes'] else None

        await interaction.followup.send("Votre réponse 'peut-être' a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
        embed.add_field(name="Date", value=event['date'], inline=True)
        embed.add_field(name="Heure", value=event['time'], inline=True)

        if event['participants']:
            participants = ', '.join([p.name for p in event['participants']])
            embed.add_field(name="Inscriptions", value=participants, inline=False)
        if event['absences']:
            absences = ', '.join([p.name for p in event['absences']])
            embed.add_field(name="Absences", value=absences, inline=False)
        if event['maybes']:
            maybes = ', '.join([p.name for p in event['maybes']])
            embed.add_field(name="Peut-être", value=maybes, inline=False)
        if event['replacements']:
            replacements = ', '.join([p.name for p in event['replacements']])
            embed.add_field(name="Remplacements", value=replacements, inline=False)

        await message.edit(embed=embed)

class ReplacementButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="Remplacement", custom_id=f"replacement_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_replacement(interaction)

    async def handle_replacement(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event['participants'].remove(user) if user in event['participants'] else None
        event['absences'].remove(user) if user in event['absences'] else None
        event['maybes'].remove(user) if user in event['maybes'] else None
        event['replacements'].append(user) if user not in event['replacements'] else None

        await interaction.followup.send("Votre disponibilité comme remplacement a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
        embed.add_field(name="Date", value=event['date'], inline=True)
        embed.add_field(name="Heure", value=event['time'], inline=True)

        if event['participants']:
            participants = ', '.join([p.name for p in event['participants']])
            embed.add_field(name="Inscriptions", value=participants, inline=False)
        if event['absences']:
            absences = ', '.join([p.name for p in event['absences']])
            embed.add_field(name="Absences", value=absences, inline=False)
        if event['maybes']:
            maybes = ', '.join([p.name for p in event['maybes']])
            embed.add_field(name="Peut-être", value=maybes, inline=False)
        if event['replacements']:
            replacements = ', '.join([p.name for p in event['replacements']])
            embed.add_field(name="Remplacements", value=replacements, inline=False)

        await message.edit(embed=embed)

@bot.tree.command(name="create_event", description="Créer un nouvel événement")
async def create_event(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Veuillez créer l'événement en envoyant la commande dans un canal du serveur.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.user.send("Nous allons configurer votre événement. Veuillez répondre aux questions suivantes.")
    
    def check(m):
        return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

    await interaction.user.send("Entrez le titre de l'événement:")
    title = (await bot.wait_for('message', check=check)).content

    await interaction.user.send("Entrez la description de l'événement:")
    description = (await bot.wait_for('message', check=check)).content

    await interaction.user.send("Entrez la date de l'événement (format: JJ/MM/AAAA):")
    date = (await bot.wait_for('message', check=check)).content

    await interaction.user.send("Entrez l'heure de l'événement (format: HH:MM):")
    time = (await bot.wait_for('message', check=check)).content

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
        'date': date,
        'time': time,
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

    channel = bot.get_channel(channel_id)
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Heure", value=time, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Absences", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Peut-être", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="Remplacements", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(PresenceButton(event_id))
    view.add_item(UnregisterButton(event_id))
    view.add_item(AbsenceButton(event_id))
    view.add_item(MaybeButton(event_id))
    view.add_item(ReplacementButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]['message_id'] = message.id
    await interaction.followup.send("L'événement a été annoncé dans le canal sélectionné.", ephemeral=True)

@bot.tree.command(name="edit_event", description="Éditer un événement")
@app_commands.describe(event_id="L'identifiant de l'événement à modifier")
async def edit_event(interaction: discord.Interaction, event_id: str):
    event = events.get(event_id)
    if not event:
        await interaction.response.send_message("Cet événement n'existe pas.", ephemeral=True)
        return

    if interaction.user.id != event['organizer']:
        await interaction.response.send_message("Vous n'avez pas la permission de modifier cet événement.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.user.send("Nous allons modifier votre événement. Veuillez répondre aux questions suivantes.")
    
    def check(m):
        return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

    await interaction.user.send("Entrez le nouveau titre de l'événement (ou laissez vide pour ne pas changer):")
    new_title = (await bot.wait_for('message', check=check)).content
    if new_title:
        event['title'] = new_title

    await interaction.user.send("Entrez la nouvelle description de l'événement (ou laissez vide pour ne pas changer):")
    new_description = (await bot.wait_for('message', check=check)).content
    if new_description:
        event['description'] = new_description

    await interaction.user.send("Entrez la nouvelle date de l'événement (format: JJ/MM/AAAA) (ou laissez vide pour ne pas changer):")
    new_date = (await bot.wait_for('message', check=check)).content
    if new_date:
        event['date'] = new_date

    await interaction.user.send("Entrez la nouvelle heure de l'événement (format: HH:MM) (ou laissez vide pour ne pas changer):")
    new_time = (await bot.wait_for('message', check=check)).content
    if new_time:
        event['time'] = new_time

    await interaction.user.send("L'événement a été modifié avec succès!")

    channel = bot.get_channel(event['channel_id'])
    message = await channel.fetch_message(event['message_id'])

    embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
    embed.add_field(name="Date", value=event['date'], inline=True)
    embed.add_field(name="Heure", value=event['time'], inline=True)

    if event['participants']:
        participants = ', '.join([p.name for p in event['participants']])
        embed.add_field(name="Inscriptions", value=participants, inline=False)
    if event['absences']:
        absences = ', '.join([p.name for p in event['absences']])
        embed.add_field(name="Absences", value=absences, inline=False)
    if event['maybes']:
        maybes = ', '.join([p.name for p in event['maybes']])
        embed.add_field(name="Peut-être", value=maybes, inline=False)
    if event['replacements']:
        replacements = ', '.join([p.name for p in event['replacements']])
        embed.add_field(name="Remplacements", value=replacements, inline=False)

    await message.edit(embed=embed)
    await interaction.followup.send("L'événement a été modifié avec succès.", ephemeral=True)

@edit_event.autocomplete("event_id")
async def edit_event_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = [
        app_commands.Choice(name=f"{event_id} | {event['date']} | {interaction.guild.get_member(event['organizer']).display_name} | {event['title']}", value=event_id)
        for event_id, event in events.items() if current.lower() in event_id.lower() or current.lower() in event['title'].lower()
    ]
    return choices

token = os.getenv('DISCORD_TOKEN')
bot.run(token)