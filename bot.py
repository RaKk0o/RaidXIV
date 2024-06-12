import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
DiscordComponents(bot)

# Dictionary to store event information
events = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def create_event(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Veuillez créer l'événement en message privé.")
        return
    
    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    await ctx.send("Entrez le titre de l'événement:")
    title = (await bot.wait_for('message', check=check)).content

    await ctx.send("Entrez la description de l'événement:")
    description = (await bot.wait_for('message', check=check)).content

    await ctx.send("Entrez la date de l'événement (format: JJ/MM/AAAA):")
    date = (await bot.wait_for('message', check=check)).content

    await ctx.send("Entrez l'heure de l'événement (format: HH:MM):")
    time = (await bot.wait_for('message', check=check)).content

    # Get list of channels
    guild = ctx.guild
    channels = guild.text_channels

    select_options = [SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
    await ctx.send("Sélectionnez le canal où l'événement sera annoncé:", components=[
        Select(placeholder="Sélectionnez un canal...", options=select_options)
    ])

    interaction = await bot.wait_for("select_option", check=lambda i: i.user.id == ctx.author.id)
    channel_id = int(interaction.values[0])

    await interaction.send("Canal sélectionné.")

    event_id = len(events) + 1
    events[event_id] = {
        'title': title,
        'description': description,
        'date': date,
        'time': time,
        'participants': [],
        'channel_id': channel_id
    }

    await ctx.send("L'événement a été créé avec succès!")

    # Send event to the selected channel
    channel = bot.get_channel(channel_id)
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Heure", value=time, inline=True)
    embed.add_field(name="Inscriptions", value="Aucun pour le moment.", inline=False)

    message = await channel.send(embed=embed, components=[Button(style=ButtonStyle.green, label="S'inscrire", custom_id=str(event_id))])

    events[event_id]['message_id'] = message.id

@bot.event
async def on_button_click(interaction):
    event_id = int(interaction.custom_id)
    event = events.get(event_id)

    if not event:
        await interaction.send("Cet événement n'existe pas.")
        return

    user = interaction.user
    if user in event['participants']:
        await interaction.send("Vous êtes déjà inscrit à cet événement.")
    else:
        event['participants'].append(user)
        await interaction.send("Vous vous êtes inscrit à l'événement!")

        channel = bot.get_channel(interaction.message.channel.id)
        message = await channel.fetch_message(event['message_id'])

        embed = message.embeds[0]
        participants = ', '.join([p.name for p in event['participants']])
        embed.set_field_at(2, name="Inscriptions", value=participants, inline=False)
        await message.edit(embed=embed)
        
token = os.getenv('DISCORD_TOKEN')
bot.run(token)