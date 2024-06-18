import discord
from discord.ui import Button
from bot_config import events, bot

class PresenceButton(Button):
    def __init__(self, event_id):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Présence",
            custom_id=f"presence_{event_id}",
            emoji="✅",
        )
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
        event["absences"].remove(user) if user in event["absences"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        (
            event["participants"].append(user)
            if user not in event["participants"]
            else None
        )

        await interaction.followup.send("Votre présence a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
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

class AbsenceButton(Button):
    def __init__(self, event_id):
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Absence",
            custom_id=f"absence_{event_id}",
            emoji="❌",
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_absence(interaction)

    async def handle_absence(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send(
                "Cet événement n'existe pas.", ephemeral=True
            )
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        event["absences"].append(user) if user not in event["absences"] else None

        await interaction.followup.send(
            "Votre absence a été enregistrée.", ephemeral=True
        )
        await self.update_event_message(event)

    async def update_event_message(self, event):
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


class MaybeButton(Button):
    def __init__(self, event_id):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Peut-être",
            custom_id=f"maybe_{event_id}",
            emoji="🤔",
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_maybe(interaction)

    async def handle_maybe(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send(
                "Cet événement n'existe pas.", ephemeral=True
            )
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["absences"].remove(user) if user in event["absences"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        event["maybes"].append(user) if user not in event["maybes"] else None

        await interaction.followup.send(
            "Votre réponse 'peut-être' a été enregistrée.", ephemeral=True
        )
        await self.update_event_message(event)

    async def update_event_message(self, event):
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


class ReplacementButton(Button):
    def __init__(self, event_id):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Remplacement",
            custom_id=f"replacement_{event_id}",
            emoji="🔄",
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.handle_replacement(interaction)

    async def handle_replacement(self, interaction):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send(
                "Cet événement n'existe pas.", ephemeral=True
            )
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["absences"].remove(user) if user in event["absences"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        (
            event["replacements"].append(user)
            if user not in event["replacements"]
            else None
        )

        await interaction.followup.send(
            "Votre disponibilité comme remplacement a été enregistrée.", ephemeral=True
        )
        await self.update_event_message(event)

    async def update_event_message(self, event):
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
