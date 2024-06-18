import discord
from discord.ui import Select, View

role_classes = {
    "Melee": ["Monk", "Dragoon", "Ninja", "Samurai", "Reaper", "Viper"],
    "Range": ["Bard", "Machinist", "Dancer"],
    "Magical": ["BlackMage", "Summoner", "RedMage", "BlueMage", "Pictomancer"],
    "Tank": ["Paladin", "Warrior", "DarkKnight", "Gunbreaker"],
    "Healer": ["WhiteMage", "Scholar", "Astrologian", "Sage"],
    "AllRounder": []
}

class CreateEventSelect(Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Sélectionnez un canal...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.channel_id = None

    async def callback(self, interaction: discord.Interaction):
        self.channel_id = int(self.values[0])
        await interaction.response.send_message("Canal sélectionné.", ephemeral=True)
        self.view.stop()

class CreateEventView(View):
    def __init__(self, options):
        super().__init__()
        self.add_item(CreateEventSelect(options))

class RoleSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=role, value=role)
            for role in role_classes.keys()
        ]
        super().__init__(
            placeholder="Sélectionnez un rôle...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.role = None

    async def callback(self, interaction: discord.Interaction):
        self.role = self.values[0]
        await interaction.response.send_message("Rôle sélectionné.", ephemeral=True)
        self.view.stop()

class ClassSelect(Select):
    def __init__(self, role):
        options = [
            discord.SelectOption(label=cls, value=cls)
            for cls in role_classes[role]
        ]
        super().__init__(
            placeholder="Sélectionnez une classe...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.cls = None

    async def callback(self, interaction: discord.Interaction):
        self.cls = self.values[0]
        await interaction.response.send_message("Classe sélectionnée.", ephemeral=True)
        self.view.stop()

class RoleSelectView(View):
    def __init__(self):
        super().__init__()
        self.add_item(RoleSelect())

class ClassSelectView(View):
    def __init__(self, role):
        super().__init__()
        self.add_item(ClassSelect(role))