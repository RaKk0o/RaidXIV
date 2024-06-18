import discord
from discord import app_commands
from datetime import datetime
import uuid
from bot_config import bot, events
from event_views import CreateEventView
from event_buttons import PresenceButton, AbsenceButton, MaybeButton, ReplacementButton

@bot.tree.command(name="create_event", description="Créer un nouvel événement")
async def create_event(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(
            "Veuillez créer l'événement en envoyant la commande dans un canal du serveur.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.user.send(
        "Nous allons configurer votre événement. Veuillez répondre aux questions suivantes."
    )

    def check(m):
        return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

    await interaction.user.send("Saisissez un titre pour cet événement.")
    title_msg = await bot.wait_for("message", check=check)
    title = title_msg.content

    await interaction.user.send("Saisissez une description pour cet événement.")
    desc_msg = await bot.wait_for("message", check=check)
    description = desc_msg.content

    while True:
        await interaction.user.send("Entrez la date de cet événement. (Format: dd-MM-yyyy)")
        date_msg = await bot.wait_for("message", check=check)
        event_date = date_msg.content
        try:
            date = datetime.strptime(event_date, "%d-%m-%Y").date()
            break
        except ValueError:
            await interaction.user.send("Date invalide. Veuillez entrer une date au bon format.")

    while True:
        await interaction.user.send("Entrez l'heure de l'événement (format: HH:MM):")
        time_str = (await bot.wait_for("message", check=check)).content
        try:
            time = datetime.strptime(time_str, "%H:%M").time()
            break
        except ValueError:
            await interaction.user.send("Heure invalide. Veuillez entrer une heure au format HH:MM.")

    guild = interaction.guild
    channels = guild.text_channels
    select_options = [
        discord.SelectOption(label=channel.name, value=str(channel.id))
        for channel in channels
    ]

    view = CreateEventView(select_options)
    await interaction.user.send("Sélectionnez le canal où l'événement sera annoncé:", view=view)
    await view.wait()

    if view.children[0].channel_id is None:
        await interaction.user.send("Aucun canal sélectionné, opération annulée.")
        return

    event_id = str(uuid.uuid4())
    channel_id = view.children[0].channel_id
    events[event_id] = {
        "title": title,
        "description": description,
        "date": date,
        "time": time,
        "participants": [],
        "absences": [],
        "maybes": [],
        "replacements": [],
        "channel_id": channel_id,
        "organizer": interaction.user.id,
    }

    await interaction.user.send("L'événement a été créé avec succès!")

    channel = bot.get_channel(channel_id)
    embed = discord.Embed(title=title, description=description, color=0x00FF00)
    embed.add_field(name="📅 Date", value=date, inline=True)
    embed.add_field(name="⏰ Heure", value=time, inline=True)
    embed.add_field(name="✅ Inscrits", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="❌ Absents", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="🤔 Peut-être", value="Aucun pour le moment.", inline=False)
    embed.add_field(name="🔄 Remplaçants", value="Aucun pour le moment.", inline=False)

    view = View()
    view.add_item(PresenceButton(event_id))
    view.add_item(AbsenceButton(event_id))
    view.add_item(MaybeButton(event_id))
    view.add_item(ReplacementButton(event_id))

    message = await channel.send(embed=embed, view=view)
    events[event_id]["message_id"] = message.id
    await interaction.followup.send("L'événement a été annoncé dans le canal sélectionné.", ephemeral=True)

@bot.tree.command(name="edit_event", description="Éditer un événement")
@app_commands.describe(event_id="L'identifiant de l'événement à modifier")
async def edit_event(interaction: discord.Interaction, event_id: str):
    event = events.get(event_id)
    if not event:
        await interaction.response.send_message("Cet événement n'existe pas.", ephemeral=True)
        return

    if interaction.user.id != event["organizer"]:
        await interaction.response.send_message("Vous n'avez pas la permission de modifier cet événement.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.user.send("Nous allons modifier votre événement. Veuillez répondre aux questions suivantes.")

    def check(m):
        return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

    await interaction.user.send("Entrez le nouveau titre de l'événement (ou laissez vide pour ne pas changer):")
    new_title = (await bot.wait_for("message", check=check)).content
    if new_title:
        event["title"] = new_title

    await interaction.user.send("Entrez la nouvelle description de l'événement (ou laissez vide pour ne pas changer):")
    new_description = (await bot.wait_for("message", check=check)).content
    if new_description:
        event["description"] = new_description

    await interaction.user.send("Entrez la nouvelle date de l'événement (format: JJ/MM/AAAA) (ou laissez vide pour ne pas changer):")
    new_date_str = (await bot.wait_for("message", check=check)).content
    if new_date_str:
        try:
            new_date = datetime.strptime(new_date_str, "%d/%m/%Y").date()
            event["date"] = new_date_str
        except ValueError:
            await interaction.user.send("Date invalide. Veuillez entrer une date au format JJ/MM/AAAA.")

    await interaction.user.send("Entrez la nouvelle heure de l'événement (format: HH:MM) (ou laissez vide pour ne pas changer):")
    new_time_str = (await bot.wait_for("message", check=check)).content
    if new_time_str:
        try:
            new_time = datetime.strptime(new_time_str, "%H:%M").time()
            event["time"] = new_time_str
        except ValueError:
            await interaction.user.send("Heure invalide. Veuillez entrer une heure au format HH:MM.")

    await interaction.user.send("L'événement a été modifié avec succès!")

    channel = bot.get_channel(event["channel_id"])
    message = await channel.fetch_message(event["message_id"])

    embed = discord.Embed(
        title=event["title"], description=event["description"], color=0x00FF00
    )
    embed.add_field(name="📅 Date", value=event["date"], inline=True)
    embed.add_field(name="⏰ Heure", value=event["time"], inline=True)

    if event["participants"]:
        participants = ", ".join([p.name for p in event["participants"]])
        embed.add_field(name="✅ Inscrits", value=participants, inline=False)
    if event["absences"]:
        absences = ", ".join([p.name for p in event["absences"]])
        embed.add_field(name="❌ Absents", value=absences, inline=False)
    if event["maybes"]:
        maybes = ", ".join([p.name for p in event["maybes"]])
        embed.add_field(name="🤔 Peut-être", value=maybes, inline=False)
    if event["replacements"]:
        replacements = ", ".join([p.name for p in event["replacements"]])
        embed.add_field(name="🔄 Remplaçants", value=replacements, inline=False)

    await message.edit(embed=embed)
    await interaction.followup.send("L'événement a été modifié avec succès.", ephemeral=True)

@edit_event.autocomplete("event_id")
async def edit_event_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = [
        app_commands.Choice(
            name=f"{event_id} | {event['date']} | {interaction.guild.get_member(event['organizer']).display_name} | {event['title']}",
            value=event_id,
        )
        for event_id, event in events.items()
        if current.lower() in event_id.lower() or current.lower() in event["title"].lower()
    ]
    return choices
