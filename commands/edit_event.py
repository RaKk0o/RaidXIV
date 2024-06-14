import discord
from discord import app_commands
from datetime import datetime
import logging
from shared import events

@app_commands.command(name="edit_event", description="Éditer un événement")
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
    new_title = (await interaction.client.wait_for('message', check=check)).content
    if new_title:
        event['title'] = new_title

    await interaction.user.send("Entrez la nouvelle description de l'événement (ou laissez vide pour ne pas changer):")
    new_description = (await interaction.client.wait_for('message', check=check)).content
    if new_description:
        event['description'] = new_description

    await interaction.user.send("Entrez la nouvelle date de l'événement (format: JJ/MM/AAAA) (ou laissez vide pour ne pas changer):")
    new_date_str = (await interaction.client.wait_for('message', check=check)).content
    if new_date_str:
        try:
            new_date = datetime.strptime(new_date_str, '%d/%m/%Y').date()
            event['date'] = new_date_str
        except ValueError:
            await interaction.user.send("Date invalide. Veuillez entrer une date au format JJ/MM/AAAA.")

    await interaction.user.send("Entrez la nouvelle heure de l'événement (format: HH:MM) (ou laissez vide pour ne pas changer):")
    new_time_str = (await interaction.client.wait_for('message', check=check)).content
    if new_time_str:
        try:
            new_time = datetime.strptime(new_time_str, '%H:%M').time()
            event['time'] = new_time_str
        except ValueError:
            await interaction.user.send("Heure invalide. Veuillez entrer une heure au format HH:MM.")

    await interaction.user.send("L'événement a été modifié avec succès!")

    channel = interaction.client.get_channel(event['channel_id'])
    message = await channel.fetch_message(event['message_id'])

    embed = discord.Embed(title=event['title'], description=event['description'], color=0x00ff00)
    embed.add_field(name="📅 Date", value=event['date'], inline=True)
    embed.add_field(name="⏰ Heure", value=event['time'], inline=True)

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
    logging.info(f"Autocomplete called with current: {current}")
    choices = [
        app_commands.Choice(name=f"{event_id} | {event['date']} | {interaction.guild.get_member(event['organizer']).display_name} | {event['title']}", value=event_id)
        for event_id, event in events.items() if current.lower() in event_id.lower() or current.lower() in event['title'].lower()
    ]
    logging.info(f"Choices generated: {choices}")
    return choices

edit_event_command = app_commands.Command(
    name="edit_event",
    description="Éditer un événement",
    callback=edit_event
)