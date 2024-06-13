import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle, SlashOption, SelectOption, Embed, Member, Message
from nextcord.ui import Button, View, Select
import uuid
import logging
from typing import Optional

# Configurer le logging
logging.basicConfig(level=logging.INFO)

MY_GUILD = nextcord.Object(id=123456789012345678)  # Remplacez par l'ID de votre serveur

class MyClient(nextcord.Client):
    def __init__(self, *, intents: nextcord.Intents):
        super().__init__(intents=intents)
        self.tree = nextcord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)

# Dictionary to store event information
events = {}

@client.event
async def on_ready():
    logging.info(f'We have logged in as {client.user} (ID: {client.user.id})')
    logging.info('------')


class CreateEventSelect(Select):
    def __init__(self, interaction: Interaction, options):
        self.interaction = interaction
        self.channel_id = None
        super().__init__(placeholder="Sélectionnez un canal...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        self.channel_id = int(self.values[0])
        await interaction.response.send_message("Canal sélectionné.", ephemeral=True)
        self.view.stop()


class CreateEventView(View):
    def __init__(self, interaction: Interaction, options):
        super().__init__()
        self.interaction = interaction
        self.add_item(CreateEventSelect(interaction, options))


class RegisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=ButtonStyle.green, label="S'inscrire", custom_id=f"register_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: Interaction):
        logging.info(f"RegisterButton clicked by {interaction.user.name}")
        await interaction.response.defer(ephemeral=True)
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

            # Mettre à jour l'embed avec les participants
            channel = client.get_channel(event['channel_id'])
            message = await channel.fetch_message(event['message_id'])

            embed = message.embeds[0]
            participants = ', '.join([p.name for p in event['participants']])
            embed.set_field_at(2, name="Inscriptions", value=participants, inline=False)
            await message.edit(embed=embed)
        logging.info(f"{interaction.user.name} registered for event {self.event_id}")


class UnregisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=ButtonStyle.red, label="Se désinscrire", custom_id=f"unregister_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: Interaction):
        logging.info(f"UnregisterButton clicked by {interaction.user.name}")
        await interaction.response.defer(ephemeral=True)
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

            # Mettre à jour l'embed avec les participants
            channel = client.get_channel(event['channel_id'])
            message = await channel.fetch_message(event['message_id'])

            embed = message.embeds[0]
            participants = ', '.join([p.name for p in event['participants']])
            embed.set_field_at(2, name="Inscriptions", value=participants if participants else "Aucun pour le moment.", inline=False)
            await message.edit(embed=embed)
        logging.info(f"{interaction.user.name} unregistered from event {self.event_id}")


@client.tree.command(name="create_event", description="Créer un nouvel événement")
async def create_event(interaction: Interaction):
    logging.info(f"Creating event command invoked by {interaction.user.name}")
    
    await interaction.response.send_message("Nous allons configurer votre événement. Veuillez répondre aux questions suivantes.", ephemeral=True)
    
    def check(m):
        return m.author == interaction.user and isinstance(m.channel, nextcord.DMChannel)

    await interaction.user.send("Entrez le titre de l'événement:")
    title = (await client.wait_for('message', check=check)).content

    await interaction.user.send("Entrez la description de l'événement:")
    description = (await client.wait_for('message', check=check)).content

    await interaction.user.send("Entrez la date de l'événement (format: JJ/MM/AAAA):")
    date = (await client.wait_for('message', check=check)).content

    await interaction.user.send("Entrez l'heure de l'événement (format: HH:MM):")
    time = (await client.wait_for('message', check=check)).content

    # Get list of channels
    guild = interaction.guild
    channels = guild.text_channels

    select_options = [SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
    
    view = CreateEventView(interaction, select_options)
    
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
    logging.info(f"Event {event_id} created by {interaction.user.name}")

    # Send event to the selected channel
    channel = client.get_channel(channel_id)
    embed = nextcord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Heure", value=time, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(RegisterButton(event_id))
    view.add_item(UnregisterButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]['message_id'] = message.id
    logging.info(f"Event {event_id} announced in channel {channel_id}")


@client.tree.command(name="modify_event", description="Modifier un événement existant")
async def modify_event(interaction: Interaction, event_id: str):
    logging.info(f"Modifying event {event_id} command invoked by {interaction.user.name}")
    event = events.get(event_id)
    if not event:
        await interaction.response.send_message("Cet événement n'existe pas.", ephemeral=True)
        return

    if interaction.user.id != event['organizer']:
        await interaction.response.send_message("Vous n'avez pas la permission de modifier cet événement.", ephemeral=True)
        return

    await interaction.user.send("Nous allons modifier votre événement. Veuillez répondre aux questions suivantes.")
    
    def check(m):
        return m.author == interaction.user and isinstance(m.channel, nextcord.DMChannel)

    await interaction.user.send("Entrez le nouveau titre de l'événement (ou laissez vide pour ne pas changer):")
    new_title = (await client.wait_for('message', check=check)).content
    if new_title:
        event['title'] = new_title

    await interaction.user.send("Entrez la nouvelle description de l'événement (ou laissez vide pour ne pas changer):")
    new_description = (await client.wait_for('message', check=check)).content
    if new_description:
        event['description'] = new_description

    await interaction.user.send("Entrez la nouvelle date de l'événement (format: JJ/MM/AAAA) (ou laissez vide pour ne pas changer):")
    new_date = (await client.wait_for('message', check=check)).content
    if new_date:
        event['date'] = new_date

    await interaction.user.send("Entrez la nouvelle heure de l'événement (format: HH:MM) (ou laissez vide pour ne pas changer):")
    new_time = (await client.wait_for('message', check=check)).content
    if new_time:
        event['time'] = new_time

    await interaction.user.send("L'événement a été modifié avec succès!")
    logging.info(f"Event {event_id} modified by {interaction.user.name}")

    # Update the event embed in the channel
    channel = client.get_channel(event['channel_id'])
    message = await channel.fetch_message(event['message_id'])

    embed = message.embeds[0]
    embed.title = event['title']
    embed.description = event['description']
    embed.set_field_at(0, name="Date", value=event['date'], inline=True)
    embed.set_field_at(1, name="Heure", value=event['time'], inline=True)
    await message.edit(embed=embed)
    logging.info(f"Event {event_id} embed updated in channel {event['channel_id']}")


@modify_event.autocomplete("event_id")
async def autocomplete_event_id(interaction: Interaction, value: str):
    choices = [
        nextcord.app_commands.Choice(name=f"{event_id} | {event['date']} | {event['title']}", value=event_id)
        for event_id, event in events.items() if value.lower() in event['title'].lower() or value.lower() in event_id
    ]
    await interaction.response.send_autocomplete(choices)


client.run(os.getenv('DISCORD_TOKEN'))
