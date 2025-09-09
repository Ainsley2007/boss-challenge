"""Complete command for the boss challenge."""

import discord
from discord import app_commands

from bot.services.boss_progression import BossProgressionService
from bot.cogs.commands.leaderboard_manager import LeaderboardManager


class CompleteCommand:
    """Handles the /complete command functionality."""
    
    def __init__(self, bot, db, boss_service: BossProgressionService, image_service):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
        self.image_service = image_service
        self.leaderboard_manager = LeaderboardManager(bot, db, boss_service)
    
    @app_commands.command(name="submit", description="Submit a boss kill with before/after screenshots")
    @app_commands.describe(
        before="Before image - your gear/inventory before fighting the boss",
        after="After image - your loot/rewards after killing the boss"
    )
    async def submit(
        self, 
        interaction: discord.Interaction, 
        before: discord.Attachment, 
        after: discord.Attachment
    ):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        if not self.db.is_joined(guild_id, user_id):
            await interaction.response.send_message(
                "❓ You're not participating in the boss challenge. Use `/join` first!",
                ephemeral=True
            )
            return
        
        valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        
        if before.content_type not in valid_types:
            await interaction.response.send_message(
                f"❌ Before attachment must be an image. Got: {before.content_type}",
                ephemeral=True
            )
            return
            
        if after.content_type not in valid_types:
            await interaction.response.send_message(
                f"❌ After attachment must be an image. Got: {after.content_type}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            current_progress = self.db.get_user_progress(guild_id, user_id)
            boss_number = current_progress + 1
            
            before_path = await self.image_service.upload_from_url(
                before.url, guild_id, user_id, "before", boss_number
            )
            after_path = await self.image_service.upload_from_url(
                after.url, guild_id, user_id, "after", boss_number
            )
            
            if not before_path or not after_path:
                await interaction.followup.send(
                    "❌ Failed to save images. Please try again.",
                    ephemeral=True
                )
                return
            
            success = self.db.add_completion(guild_id, user_id, before_path, after_path)
            
            if success:
                new_progress = self.db.get_user_progress(guild_id, user_id)
                
                user_mode = self.db.get_user_mode(guild_id, user_id)
                mode_channel = f"boss-challenge-{user_mode}"
                await interaction.followup.send(
                    f"⚔️ Boss kill submitted successfully! Check #boss-completions for your defeat post and #{mode_channel} for leaderboard.",
                    ephemeral=True
                )
                
                await self._post_boss_completion(interaction, before, after, boss_number, new_progress, user_mode)
            else:
                await interaction.followup.send(
                    "❌ Failed to record boss kill. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"Error in submit command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your submission.",
                ephemeral=True
            )
    
    async def _post_boss_completion(self, interaction, before, after, boss_number, new_progress, user_mode):
        """Post the boss completion to the completions channel and update leaderboard."""
        completions_channel = discord.utils.get(
            interaction.guild.text_channels, 
            name="boss-completions"
        )
        
        channel_name = f"boss-challenge-{user_mode}"
        leaderboard_channel = discord.utils.get(
            interaction.guild.text_channels, 
            name=channel_name
        )
        
        if completions_channel:
            defeated_boss = self.boss_service.get_boss_name(boss_number - 1)
            next_boss = self.boss_service.get_next_boss(new_progress, user_mode)
            
            mode_info = self.boss_service.get_mode_info(user_mode)
            color = discord.Color.green() if user_mode == "normal" else discord.Color.red()
            
            embed = discord.Embed(
                title="⚔️ Boss Defeated!",
                description=f"**{interaction.user.display_name}** defeated **{defeated_boss}**! ({mode_info['emoji']} {mode_info['name']})",
                color=color
            )
            embed.add_field(
                name="📈 Progression", 
                value=f"**{new_progress}** bosses defeated", 
                inline=True
            )
            embed.add_field(
                name="🏆 Rank", 
                value=f"#{self.leaderboard_manager.get_user_mode_rank(interaction.guild_id, interaction.user.id, user_mode)}", 
                inline=True
            )
            if next_boss:
                embed.add_field(
                    name="🎯 Next Boss", 
                    value=f"**{next_boss}**", 
                    inline=True
                )
            
            embed.set_image(url=after.url)
            embed.set_thumbnail(url=before.url)
            embed.set_footer(text=f"{defeated_boss} defeated • Gear (small) | Loot (large)")
            embed.timestamp = discord.utils.utcnow()
            
            await completions_channel.send(embed=embed)
            
            if leaderboard_channel:
                await self.leaderboard_manager.update_mode_leaderboard(leaderboard_channel, interaction.guild_id, user_mode)
