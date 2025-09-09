import discord

from bot.services.boss_progression import BossProgressionService


class LeaveCommand:
    
    def __init__(self, bot, db, boss_service: BossProgressionService):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
    
    async def leave(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        if not self.db.is_joined(guild_id, user_id):
            await interaction.response.send_message(
                "❓ You're not currently participating in the boss challenge.",
                ephemeral=True
            )
            return
        
        user_mode = self.db.get_user_mode(guild_id, user_id)
        if user_mode == "extreme":
            archived = self.db.archive_extreme_participant(guild_id, user_id)
            if archived:
                await interaction.response.send_message(
                    "🗂️ You left Extreme. Your current position was archived and remains visible on the board. Re-join to start over.",
                    ephemeral=True
                )
                from bot.cogs.commands.leaderboard_manager import LeaderboardManager
                leaderboard_manager = LeaderboardManager(self.bot, self.db, self.boss_service)
                channel = await leaderboard_manager.get_channel_by_id(guild_id, "extreme")
                if channel:
                    await leaderboard_manager.update_mode_leaderboard(channel, guild_id, "extreme")
            else:
                await interaction.response.send_message(
                    "❌ Could not archive your Extreme progress.",
                    ephemeral=True
                )
        else:
            success = self.db.leave_user(guild_id, user_id)
            if success:
                await interaction.response.send_message(
                    "👋 You've left the boss challenge. Your progression has been removed.",
                    ephemeral=True
                )
                from bot.cogs.commands.leaderboard_manager import LeaderboardManager
                leaderboard_manager = LeaderboardManager(self.bot, self.db, self.boss_service)
                channel = await leaderboard_manager.get_channel_by_id(guild_id, user_mode)
                if channel:
                    await leaderboard_manager.update_mode_leaderboard(channel, guild_id, user_mode)
            else:
                await interaction.response.send_message(
                    "❌ Something went wrong. Please try again.",
                    ephemeral=True
                )
