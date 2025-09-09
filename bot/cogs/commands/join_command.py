import discord

from bot.services.boss_progression import BossProgressionService


class JoinCommand:
    
    def __init__(self, bot, db, boss_service: BossProgressionService):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
    
    async def join(
        self, 
        interaction: discord.Interaction,
        mode: str
    ):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        mode = mode.lower()
        if mode not in ["easy", "normal", "hard", "extreme"]:
            await interaction.response.send_message(
                "❌ Invalid mode! Choose one of: easy, normal, hard, extreme.",
                ephemeral=True
            )
            return
            
        if self.db.is_joined(guild_id, user_id):
            await interaction.response.send_message(
                "⚔️ You're already participating in the boss challenge!",
                ephemeral=True
            )
            return
        
        success = self.db.join_user_with_mode(guild_id, user_id, mode)
        if success:
            starting_boss = self.boss_service.get_next_boss(0, mode)
            mode_info = self.boss_service.get_mode_info(mode)
            await interaction.response.send_message(
                f"🎉 Welcome to the boss challenge - **{mode_info['name']} ({mode_info['description']})**!\n"
                f"Start with **{starting_boss}** and work your way up. Use `/submit` to submit boss kills!",
                ephemeral=True
            )
            
            user_mode = self.db.get_user_mode(guild_id, user_id)
            from bot.cogs.commands.leaderboard_manager import LeaderboardManager
            leaderboard_manager = LeaderboardManager(self.bot, self.db, self.boss_service)
            channel = await leaderboard_manager.get_channel_by_id(guild_id, user_mode)
            if channel:
                await leaderboard_manager.update_mode_leaderboard(channel, guild_id, user_mode)
            else:
                print(f"No leaderboard channel found for mode {user_mode}")
        else:
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True
            )
