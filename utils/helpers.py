import discord
from datetime import datetime

async def validate_date(interaction, check):
    while True:
        await interaction.user.send("Entrez la date de l'événement (format: JJ/MM/AAAA):")
        date_str = (await interaction.client.wait_for('message', check=check)).content
        try:
            date = datetime.strptime(date_str, '%d/%m/%Y').date()
            return date_str
        except ValueError:
            await interaction.user.send("Date invalide. Veuillez entrer une date au format JJ/MM/AAAA.")

async def validate_time(interaction, check):
    while True:
        await interaction.user.send("Entrez l'heure de l'événement (format: HH:MM):")
        time_str = (await interaction.client.wait_for('message', check=check)).content
        try:
            time = datetime.strptime(time_str, '%H:%M').time()
            return time_str
        except ValueError:
            await interaction.user.send("Heure invalide. Veuillez entrer une heure au format HH:MM.")

class CreateEventSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Sélectionnez un canal...", min_values=1, max_values=1, options=options)
        self.channel_id = None

    async def callback(self, interaction: discord.Interaction):
        self.channel_id = int(self.values[0])
        await interaction.response.send_message("Canal sélectionné.", ephemeral=True)
        self.view.stop()

class CreateEventView(discord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.add_item(CreateEventSelect(options))

async def update_event_message(client, event):
    channel = client.get_channel(event['channel_id'])
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
