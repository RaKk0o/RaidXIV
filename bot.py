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

class RegisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.green, label="S'inscrire", custom_id=f"register_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_registration(interaction)

    async def handle_registration(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user
        if user in event['participants']:
            await interaction.followup.send("Vous êtes déjà inscrit à cet événement.", ephemeral=True)
        else:
            event['participants'].append(user)
            await interaction.followup.send("Vous vous êtes inscrit à l'événement!", ephemeral=True)
            await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = message.embeds[0]
        participants = ', '.join([p.name for p in event['participants']])
        embed.set_field_at(2, name="Inscriptions", value=participants, inline=False)
        await message.edit(embed=embed)

class UnregisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.red, label="Se désinscrire", custom_id=f"unregister_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_unregistration(interaction)

    async def handle_unregistration(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user
        if user not in event['participants']:
            await interaction.followup.send("Vous n'êtes pas inscrit à cet événement.", ephemeral=True)
        else:
            event['participants'].remove(user)
            await interaction.followup.send("Votre inscription a été annulée.", ephemeral=True)
            await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event['channel_id'])
        message = await channel.fetch_message(event['message_id'])
        embed = message.embeds[0]
        participants = ', '.join([p.name for p in event['participants']])
        embed.set_field_at(2, name="Inscriptions", value=participants if participants else "Aucun pour le moment.", inline=False)
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
        'channel_id': channel_id,
        'organizer': interaction.user.id
    }

    await interaction.user.send("L'événement a été créé avec succès!")

    channel = bot.get_channel(channel_id)
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Heure", value=time, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(RegisterButton(event_id))
    view.add_item(UnregisterButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]['message_id'] = message.id
    await interaction.followup.send("L'événement a été annoncé dans le canal sélectionné.", ephemeral=True)

@bot.tree.command(name="modify_event", description="Modifier un événement existant")
@app_commands.describe(event_id="L'identifiant de l'événement à modifier")
async def modify_event(interaction: discord.Interaction, event_id: str):
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

    embed = message.embeds[0]
    embed.title = event['title']
    embed.description = event['description']
    embed.set_field_at(0, name="Date", value=event['date'], inline=True)
    embed.set_field_at(1, name="Heure", value=event['time'], inline=True)
    await message.edit(embed=embed)
    await interaction.followup.send("L'événement a été modifié avec succès.", ephemeral=True)

@bot.tree.command(name="edit_event", description="Éditer un événement")
async def edit_event(interaction: discord.Interaction):
    if not events:
        await interaction.response.send_message("Il n'y a pas d'événements à éditer.", ephemeral=True)
        return

    event_options = [
        discord.SelectOption(label=f"{event_id} | {event['date']} | {interaction.user.name} | {event['title']}", value=event_id)
        for event_id, event in events.items()
    ]

    class EditEventSelect(Select):
        def __init__(self, options):
            super().__init__(placeholder="Sélectionnez un événement à éditer...", min_values=1, max_values=1, options=options)
            self.event_id = None

        async def callback(self, interaction: discord.Interaction):
            self.event_id = self.values[0]
            await interaction.response.send_message(f"Événement sélectionné : {self.event_id}", ephemeral=True)
            self.view.stop()

    view = View()
    select = EditEventSelect(event_options)
    view.add_item(select)

    await interaction.response.send_message("Veuillez sélectionner l'événement que vous souhaitez éditer :", view=view)
    await view.wait()

    if select.event_id is not None:
        await modify_event(interaction, select.event_id)

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
