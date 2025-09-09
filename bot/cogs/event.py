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
        app_commands.Choice(name="🌱 Easy Mode", value="easy"),
        app_commands.Choice(name="🛡️ Normal Mode", value="normal"),
        app_commands.Choice(name="🔥 Hard Mode", value="hard"),
        app_commands.Choice(name="💀 Extreme Mode", value="extreme")
    ])
    async def join(self, interaction: discord.Interaction, mode: str):
        if self.db.is_guild_locked(interaction.guild_id):
            await interaction.response.send_message("🔒 This server's challenge is locked. An admin must use /unlock.", ephemeral=True)
            return
        await self.join_cmd.join(interaction, mode)
    
    @app_commands.command(name="leave", description="Leave the boss progression challenge")
    async def leave(self, interaction: discord.Interaction):
        if self.db.is_guild_locked(interaction.guild_id):
            await interaction.response.send_message("🔒 This server's challenge is locked. An admin must use /unlock.", ephemeral=True)
            return
        await self.leave_cmd.leave(interaction)
    
    @app_commands.command(name="reset", description="Reset your boss progression (if you died)")
    async def reset(self, interaction: discord.Interaction):
        if self.db.is_guild_locked(interaction.guild_id):
            await interaction.response.send_message("🔒 This server's challenge is locked. An admin must use /unlock.", ephemeral=True)
            return
        await self.reset_cmd.reset(interaction)
    
    @app_commands.command(name="submit", description="Submit a boss kill with before/after screenshots")
    @app_commands.describe(
        before="Before image - your gear/inventory before fighting the boss",
        after="After image - your loot/rewards after killing the boss"
    )
    async def submit(self, interaction: discord.Interaction, before: discord.Attachment, after: discord.Attachment):
        if self.db.is_guild_locked(interaction.guild_id):
            await interaction.response.send_message("🔒 This server's challenge is locked. An admin must use /unlock.", ephemeral=True)
            return
        await self.submit_cmd.submit(interaction, before, after)

    
    @app_commands.command(name="unlock", description="[Admin] Unlock all commands for this server")
    async def unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
            return
        self.db.set_guild_locked(interaction.guild_id, False)
        await interaction.response.send_message("✅ Server unlocked. All commands are now available.", ephemeral=True)

    @app_commands.command(name="lock", description="[Admin] Lock all participant commands for this server")
    async def lock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
            return
        self.db.set_guild_locked(interaction.guild_id, True)
        await interaction.response.send_message("🔒 Server locked. Only admins can use commands.", ephemeral=True)
    
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

