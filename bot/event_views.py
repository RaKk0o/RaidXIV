from discord.ui import Select, View
from event_buttons import PresenceButton, AbsenceButton, MaybeButton, ReplacementButton

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
