import discord
from discord.ui import Button
from utils.helpers import update_event_message
from shared import events

class PresenceButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.green, label="✅ Présence", custom_id=f"presence_{event_id}")
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
        await update_event_message(interaction.client, event)

class AbsenceButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.red, label="❌ Absence", custom_id=f"absence_{event_id}")
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
        await update_event_message(interaction.client, event)

class MaybeButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="🤔 Peut-être", custom_id=f"maybe_{event_id}")
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
        await update_event_message(interaction.client, event)

class ReplacementButton(Button):
    def __init__(self, event_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="🔄 Remplacement", custom_id=f"replacement_{event_id}")
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
        await update_event_message(interaction.client, event)