import os
import nextcord
from nextcord.ext import commands
from nextcord import SelectOption, Interaction, ButtonStyle
from nextcord.ui import Button, View, Select
import uuid

intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store event information
events = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

class CreateEventSelect(Select):
    def __init__(self, ctx, options):
        self.ctx = ctx
        self.channel_id = None
        super().__init__(placeholder="Sélectionnez un canal...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        self.channel_id = int(self.values[0])
        await interaction.response.send_message("Canal sélectionné.", ephemeral=True)
        self.view.stop()

class CreateEventView(View):
    def __init__(self, ctx, options):
        super().__init__()
        self.ctx = ctx
        self.add_item(CreateEventSelect(ctx, options))

class RegisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=ButtonStyle.green, label="S'inscrire", custom_id=f"register_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: Interaction):
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
            channel = bot.get_channel(event['channel_id'])
            message = await channel.fetch_message(event['message_id'])

            embed = message.embeds[0]
            participants = ', '.join([p.name for p in event['participants']])
            embed.set_field_at(2, name="Inscriptions", value=participants, inline=False)
            await message.edit(embed=embed)

class UnregisterButton(Button):
    def __init__(self, event_id):
        super().__init__(style=ButtonStyle.red, label="Se désinscrire", custom_id=f"unregister_{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: Interaction):
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
            channel = bot.get_channel(event['channel_id'])
            message = await channel.fetch_message(event['message_id'])

            embed = message.embeds[0]
            participants = ', '.join([p.name for p in event['participants']])
            embed.set_field_at(2, name="Inscriptions", value=participants if participants else "Aucun pour le moment.", inline=False)
            await message.edit(embed=embed)

@bot.command()
async def create_event(ctx):
    if isinstance(ctx.channel, nextcord.DMChannel):
        await ctx.send("Veuillez créer l'événement en envoyant la commande dans un canal du serveur.")
        return
    
    await ctx.author.send("Nous allons configurer votre événement. Veuillez répondre aux questions suivantes.")
    
    def check(m):
        return m.author == ctx.author and isinstance(m.channel, nextcord.DMChannel)

    await ctx.author.send("Entrez le titre de l'événement:")
    title = (await bot.wait_for('message', check=check)).content

    await ctx.author.send("Entrez la description de l'événement:")
    description = (await bot.wait_for('message', check=check)).content

    await ctx.author.send("Entrez la date de l'événement (format: JJ/MM/AAAA):")
    date = (await bot.wait_for('message', check=check)).content

    await ctx.author.send("Entrez l'heure de l'événement (format: HH:MM):")
    time = (await bot.wait_for('message', check=check)).content

    # Get list of channels
    guild = ctx.guild
    channels = guild.text_channels

    select_options = [SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
    
    view = CreateEventView(ctx, select_options)
    
    await ctx.author.send("Sélectionnez le canal où l'événement sera annoncé:", view=view)
    await view.wait()

    if view.children[0].channel_id is None:
        await ctx.author.send("Aucun canal sélectionné, opération annulée.")
        return

    event_id = str(uuid.uuid4())
    events[event_id] = {
        'title': title,
        'description': description,
        'date': date,
        'time': time,
        'participants': [],
        'channel_id': view.children[0].channel_id
    }

    await ctx.author.send("L'événement a été créé avec succès!")

    # Send event to the selected channel
    channel = bot.get_channel(view.children[0].channel_id)
    embed = nextcord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Heure", value=time, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(RegisterButton(event_id))
    view.add_item(UnregisterButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]['message_id'] = message.id

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
