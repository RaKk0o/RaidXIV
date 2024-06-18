import discord
from discord.ui import Button, View
from bot_config import events, bot
from event_views import RoleSelectView, ClassSelectView
import os

def get_class_icon(cls):
    icon_path = f"../media/job_icons/{cls.replace(' ', '')}.png"
    if os.path.exists(icon_path):
        return icon_path
    return None

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
        await self.select_role_and_class(interaction)

    async def select_role_and_class(self, interaction):
        role_select_view = RoleSelectView()
        await interaction.user.send("Sélectionnez votre rôle:", view=role_select_view)
        await role_select_view.wait()

        if not role_select_view.children[0].role:
            await interaction.user.send("Aucun rôle sélectionné, opération annulée.")
            return

        role = role_select_view.children[0].role

        class_select_view = ClassSelectView(role)
        await interaction.user.send("Sélectionnez votre classe:", view=class_select_view)
        await class_select_view.wait()

        if not class_select_view.children[0].cls:
            await interaction.user.send("Aucune classe sélectionnée, opération annulée.")
            return

        cls = class_select_view.children[0].cls

        await self.handle_presence(interaction, role, cls)

    async def handle_presence(self, interaction, role, cls):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event["absences"].remove(user) if user in event["absences"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        if user not in event["participants"]:
            event["participants"].append((user, role, cls))

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

        roles_summary = {"Tank": 0, "DPS Melee": 0, "DPS Range": 0, "DPS Magical": 0, "Heal": 0}

        # Compter les rôles et préparer les champs pour l'embed
        for role in roles_summary.keys():
            role_users = [f"{get_class_icon_tag(cls)} {p.name}" for p, r, cls in event["participants"] if r == role]
            if role_users:
                embed.add_field(name=f"{role} ({len(role_users)})", value="\n".join(role_users), inline=False)

        if event["participants"]:
            participants = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["participants"]])
            embed.add_field(name="✅ Inscrits", value=participants, inline=False)
        if event["absences"]:
            absences = "\n".join([p.name for p in event["absences"]])
            embed.add_field(name="❌ Absents", value=absences, inline=False)
        if event["maybes"]:
            maybes = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["maybes"]])
            embed.add_field(name="🤔 Peut-être", value=maybes, inline=False)
        if event["replacements"]:
            replacements = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["replacements"]])
            embed.add_field(name="🔄 Remplaçants", value=replacements, inline=False)

        await message.edit(embed=embed)

def get_class_icon_tag(cls):
    icon_path = get_class_icon(cls)
    if icon_path:
        return f"![{cls}](attachment://{icon_path})"
    return cls


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
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        if user not in event["absences"]:
            event["absences"].append(user)

        await interaction.followup.send("Votre absence a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event["channel_id"])
        message = await channel.fetch_message(event["message_id"])
        embed = discord.Embed(
            title=event["title"], description=event["description"], color=0x00FF00
        )
        embed.add_field(name="📅 Date", value=event["date"], inline=True)
        embed.add_field(name="⏰ Heure", value=event["time"], inline=True)

        roles_summary = {"Tank": 0, "DPS Melee": 0, "DPS Range": 0, "DPS Magical": 0, "Heal": 0}

        # Compter les rôles et préparer les champs pour l'embed
        for role in roles_summary.keys():
            role_users = [f"{get_class_icon_tag(cls)} {p.name}" for p, r, cls in event["participants"] if r == role]
            if role_users:
                embed.add_field(name=f"{role} ({len(role_users)})", value="\n".join(role_users), inline=False)

        if event["participants"]:
            participants = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["participants"]])
            embed.add_field(name="✅ Inscrits", value=participants, inline=False)
        if event["absences"]:
            absences = "\n".join([p.name for p in event["absences"]])
            embed.add_field(name="❌ Absents", value=absences, inline=False)
        if event["maybes"]:
            maybes = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["maybes"]])
            embed.add_field(name="🤔 Peut-être", value=maybes, inline=False)
        if event["replacements"]:
            replacements = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["replacements"]])
            embed.add_field(name="🔄 Remplaçants", value=replacements, inline=False)

        await message.edit(embed=embed)

def get_class_icon_tag(cls):
    icon_path = get_class_icon(cls)
    if icon_path:
        return f"![{cls}](attachment://{icon_path})"
    return cls


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
        await self.select_role_and_class(interaction)

    async def select_role_and_class(self, interaction):
        role_select_view = RoleSelectView()
        await interaction.user.send("Sélectionnez votre rôle:", view=role_select_view)
        await role_select_view.wait()

        if not role_select_view.children[0].role:
            await interaction.user.send("Aucun rôle sélectionné, opération annulée.")
            return

        role = role_select_view.children[0].role

        class_select_view = ClassSelectView(role)
        await interaction.user.send("Sélectionnez votre classe:", view=class_select_view)
        await class_select_view.wait()

        if not class_select_view.children[0].cls:
            await interaction.user.send("Aucune classe sélectionnée, opération annulée.")
            return

        cls = class_select_view.children[0].cls

        await self.handle_maybe(interaction, role, cls)

    async def handle_maybe(self, interaction, role, cls):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["absences"].remove(user) if user in event["absences"] else None
        event["replacements"].remove(user) if user in event["replacements"] else None
        if user not in event["maybes"]:
            event["maybes"].append((user, role, cls))

        await interaction.followup.send("Votre réponse 'peut-être' a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event["channel_id"])
        message = await channel.fetch_message(event["message_id"])
        embed = discord.Embed(
            title=event["title"], description=event["description"], color=0x00FF00
        )
        embed.add_field(name="📅 Date", value=event["date"], inline=True)
        embed.add_field(name="⏰ Heure", value=event["time"], inline=True)

        roles_summary = {"Tank": 0, "DPS Melee": 0, "DPS Range": 0, "DPS Magical": 0, "Heal": 0}

        # Compter les rôles et préparer les champs pour l'embed
        for role in roles_summary.keys():
            role_users = [f"{get_class_icon_tag(cls)} {p.name}" for p, r, cls in event["participants"] if r == role]
            if role_users:
                embed.add_field(name=f"{role} ({len(role_users)})", value="\n".join(role_users), inline=False)

        if event["participants"]:
            participants = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["participants"]])
            embed.add_field(name="✅ Inscrits", value=participants, inline=False)
        if event["absences"]:
            absences = "\n".join([p.name for p in event["absences"]])
            embed.add_field(name="❌ Absents", value=absences, inline=False)
        if event["maybes"]:
            maybes = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["maybes"]])
            embed.add_field(name="🤔 Peut-être", value=maybes, inline=False)
        if event["replacements"]:
            replacements = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["replacements"]])
            embed.add_field(name="🔄 Remplaçants", value=replacements, inline=False)

        await message.edit(embed=embed)

def get_class_icon_tag(cls):
    icon_path = get_class_icon(cls)
    if icon_path:
        return f"![{cls}](attachment://{icon_path})"
    return cls

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
        await self.select_role_and_class(interaction)

    async def select_role_and_class(self, interaction):
        role_select_view = RoleSelectView()
        await interaction.user.send("Sélectionnez votre rôle:", view=role_select_view)
        await role_select_view.wait()

        if not role_select_view.children[0].role:
            await interaction.user.send("Aucun rôle sélectionné, opération annulée.")
            return

        role = role_select_view.children[0].role

        class_select_view = ClassSelectView(role)
        await interaction.user.send("Sélectionnez votre classe:", view=class_select_view)
        await class_select_view.wait()

        if not class_select_view.children[0].cls:
            await interaction.user.send("Aucune classe sélectionnée, opération annulée.")
            return

        cls = class_select_view.children[0].cls

        await self.handle_replacement(interaction, role, cls)

    async def handle_replacement(self, interaction, role, cls):
        event = events.get(self.event_id)
        if not event:
            await interaction.followup.send("Cet événement n'existe pas.", ephemeral=True)
            return

        user = interaction.user

        # Remove user from other lists
        event["participants"].remove(user) if user in event["participants"] else None
        event["absences"].remove(user) if user in event["absences"] else None
        event["maybes"].remove(user) if user in event["maybes"] else None
        if user not in event["replacements"]:
            event["replacements"].append((user, role, cls))

        await interaction.followup.send("Votre disponibilité comme remplacement a été enregistrée.", ephemeral=True)
        await self.update_event_message(event)

    async def update_event_message(self, event):
        channel = bot.get_channel(event["channel_id"])
        message = await channel.fetch_message(event["message_id"])
        embed = discord.Embed(
            title=event["title"], description=event["description"], color=0x00FF00
        )
        embed.add_field(name="📅 Date", value=event["date"], inline=True)
        embed.add_field(name="⏰ Heure", value=event["time"], inline=True)

        roles_summary = {"Tank": 0, "DPS Melee": 0, "DPS Range": 0, "DPS Magical": 0, "Heal": 0}

        # Compter les rôles et préparer les champs pour l'embed
        for role in roles_summary.keys():
            role_users = [f"{get_class_icon_tag(cls)} {p.name}" for p, r, cls in event["participants"] if r == role]
            if role_users:
                embed.add_field(name=f"{role} ({len(role_users)})", value="\n".join(role_users), inline=False)

        if event["participants"]:
            participants = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["participants"]])
            embed.add_field(name="✅ Inscrits", value=participants, inline=False)
        if event["absences"]:
            absences = "\n".join([p.name for p in event["absences"]])
            embed.add_field(name="❌ Absents", value=absences, inline=False)
        if event["maybes"]:
            maybes = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["maybes"]])
            embed.add_field(name="🤔 Peut-être", value=maybes, inline=False)
        if event["replacements"]:
            replacements = "\n".join([f"{get_class_icon_tag(cls)} {p.name}" for p, role, cls in event["replacements"]])
            embed.add_field(name="🔄 Remplaçants", value=replacements, inline=False)

        await message.edit(embed=embed)

def get_class_icon_tag(cls):
    icon_path = get_class_icon(cls)
    if icon_path:
        return f"![{cls}](attachment://{icon_path})"
    return cls