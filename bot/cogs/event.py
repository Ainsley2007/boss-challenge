import discord
from discord import app_commands
from discord.ext import commands

from bot.db.tiny import get_database
from bot.services.image_upload import get_image_service
from bot.services.boss_progression import BossProgressionService

from bot.cogs.commands.join_command import JoinCommand
from bot.cogs.commands.leave_command import LeaveCommand
from bot.cogs.commands.reset_command import ResetCommand
from bot.cogs.commands.submit_command import SubmitCommand
from bot.cogs.commands.leaderboard_manager import LeaderboardManager


class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = get_database()
        self.image_service = get_image_service()
        self.boss_service = BossProgressionService()
        
        self.join_cmd = JoinCommand(bot, self.db, self.boss_service)
        self.leave_cmd = LeaveCommand(bot, self.db, self.boss_service)
        self.reset_cmd = ResetCommand(bot, self.db, self.boss_service)
        self.submit_cmd = SubmitCommand(bot, self.db, self.boss_service, self.image_service)
        self.leaderboard_manager = LeaderboardManager(bot, self.db, self.boss_service)
    
    @app_commands.command(name="join", description="Join the RuneScape boss progression challenge")
    @app_commands.describe(mode="Challenge difficulty: Easy, Normal, Hard, or Extreme")
    @app_commands.choices(mode=[
        app_commands.Choice(name="🌱 Easy Mode (Obor → TOA 150 Invocation)", value="easy"),
        app_commands.Choice(name="🛡️ Normal Mode (Obor → Phosani's Nightmare)", value="normal"),
        app_commands.Choice(name="🔥 Hard Mode (Obor → Sol Heredit)", value="hard"),
        app_commands.Choice(name="💀 Extreme Mode (Corrupted Hunleff → Infinite)", value="extreme")
    ])
    async def join(self, interaction: discord.Interaction, mode: str):
        await self.join_cmd.join(interaction, mode)
    
    @app_commands.command(name="leave", description="Leave the boss progression challenge")
    async def leave(self, interaction: discord.Interaction):
        await self.leave_cmd.leave(interaction)
    
    @app_commands.command(name="reset", description="Reset your boss progression (if you died)")
    async def reset(self, interaction: discord.Interaction):
        await self.reset_cmd.reset(interaction)
    
    @app_commands.command(name="submit", description="Submit a boss kill with before/after screenshots")
    @app_commands.describe(
        before="Before image - your gear/inventory before fighting the boss",
        after="After image - your loot/rewards after killing the boss"
    )
    async def submit(self, interaction: discord.Interaction, before: discord.Attachment, after: discord.Attachment):
        await self.submit_cmd.submit(interaction, before, after)

    @app_commands.command(name="set_progress", description="[Admin/Test] Set your progress to second-to-last boss for a difficulty")
    @app_commands.describe(difficulty="Difficulty to set progress for")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="🌱 Easy", value="easy"),
        app_commands.Choice(name="🛡️ Normal", value="normal"),
        app_commands.Choice(name="🔥 Hard", value="hard"),
        app_commands.Choice(name="💀 Extreme", value="extreme"),
    ])
    async def set_progress(self, interaction: discord.Interaction, difficulty: str = "hard"):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
            return
        total = self.boss_service.get_max_bosses_for_mode(difficulty)
        if total == -1:
            await interaction.response.send_message("❌ Extreme has no fixed end.", ephemeral=True)
            return
        target = max(0, total - 1)
        self.db.set_user_progress(interaction.guild_id, interaction.user.id, target, difficulty)
        channel_name = f"boss-challenge-{difficulty}"
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if channel:
            await self.leaderboard_manager.update_mode_leaderboard(channel, interaction.guild_id, difficulty)
        await interaction.response.send_message(f"Set your {difficulty} progress to {target}/{total}.", ephemeral=True)
    
    async def create_normal_mode_content(self, channel, guild_id: int):
        await self.leaderboard_manager.create_normal_mode_content(channel, guild_id)
    
    async def create_hard_mode_content(self, channel, guild_id: int):
        await self.leaderboard_manager.create_hard_mode_content(channel, guild_id)
    
    async def create_difficulty_content(self, channel, guild_id: int, difficulty: str):
        await self.leaderboard_manager.create_difficulty_content(channel, guild_id, difficulty)
    
    async def ensure_mode_leaderboard(self, channel, guild_id: int, mode: str):
        await self.leaderboard_manager.ensure_mode_leaderboard(channel, guild_id, mode)
    
    async def update_mode_leaderboard(self, channel, guild_id: int, mode: str):
        await self.leaderboard_manager.update_mode_leaderboard(channel, guild_id, mode)


async def setup(bot):
    await bot.add_cog(EventCog(bot))

