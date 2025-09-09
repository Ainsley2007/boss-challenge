import discord

from bot.services.boss_progression import BossProgressionService


class ResetCommand:
    
    def __init__(self, bot, db, boss_service: BossProgressionService):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
    
    async def reset(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        if not self.db.is_joined(guild_id, user_id):
            await interaction.response.send_message(
                "❓ You're not currently participating in the boss challenge. Use `/join` first.",
                ephemeral=True
            )
            return
        
        user_mode = self.db.get_user_mode(guild_id, user_id)
        current_progress = self.db.get_user_progress(guild_id, user_id)
        
        from bot.cogs.commands.leaderboard_manager import LeaderboardManager
        leaderboard_manager = LeaderboardManager(self.bot, self.db, self.boss_service)
        current_rank = leaderboard_manager.get_user_mode_rank(guild_id, user_id, user_mode)
        
        success = self.db.reset_user(guild_id, user_id)
        if success:
            starting_boss = self.boss_service.get_next_boss(0, user_mode)
            await interaction.response.send_message(
                f"💀 RIP! Your boss progression has been reset. Back to **{starting_boss}**!",
                ephemeral=True
            )
            
            await self._post_reset_announcement(interaction, user_mode, current_progress, current_rank, leaderboard_manager)
            
            channel = await leaderboard_manager.get_channel_by_id(guild_id, user_mode)
            if channel:
                await leaderboard_manager.update_mode_leaderboard(channel, guild_id, user_mode)
        else:
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True
            )
    
    async def _post_reset_announcement(self, interaction, user_mode, previous_progress, previous_rank, leaderboard_manager):
        completions_channel_id = self.db.get_discord_resource(interaction.guild_id, "completions")
        completions_channel = None
        if completions_channel_id:
            completions_channel = interaction.guild.get_channel(completions_channel_id)
        
        if completions_channel:
            username = await leaderboard_manager.get_user_display_name(interaction.guild_id, interaction.user.id)
            starting_boss = self.boss_service.get_next_boss(0, user_mode)
            
            embed = discord.Embed(
                title="💀 RIP",
                description=f"**{username}** died! Back to **{starting_boss}**, rookie!",
                color=discord.Color.dark_gray()
            )
            embed.set_footer(text=f"Was at {previous_progress} bosses defeated")
            embed.timestamp = discord.utils.utcnow()
            
            await completions_channel.send(embed=embed)
