import discord
from datetime import datetime

from bot.services.boss_progression import BossProgressionService
from bot.cogs.commands.leaderboard_manager import LeaderboardManager


class SubmitCommand:
    
    def __init__(self, bot, db, boss_service: BossProgressionService, image_service):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
        self.image_service = image_service
        self.leaderboard_manager = LeaderboardManager(bot, db, boss_service)
    
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

                rolled_next = None
                if user_mode == "extreme":
                    rolled_next = self.boss_service.get_random_boss_for_extreme()
                    self.db.set_next_extreme_boss(guild_id, user_id, rolled_next)
                
                # Check if difficulty is completed
                is_completed = self.boss_service.is_difficulty_complete(new_progress, user_mode)
                if is_completed and user_mode != "extreme":
                    completion_time = datetime.utcnow().isoformat()
                    self.db.mark_difficulty_complete(guild_id, user_id, user_mode, completion_time)
                
                completion_msg = "🎉 **DIFFICULTY COMPLETED!** " if is_completed and user_mode != "extreme" else ""
                await interaction.followup.send(
                    f"{completion_msg}⚔️ Boss kill submitted successfully! Check the completions channel for your defeat post and the {user_mode} channel for leaderboard.",
                    ephemeral=True
                )
                
                await self._post_boss_completion(interaction, before, after, boss_number, new_progress, user_mode, is_completed, rolled_next)
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
    
    async def _post_boss_completion(self, interaction, before, after, boss_number, new_progress, user_mode, is_completed=False, rolled_next: str | None = None):
        completions_channel_id = self.db.get_discord_resource(interaction.guild_id, "completions")
        completions_channel = None
        if completions_channel_id:
            completions_channel = interaction.guild.get_channel(completions_channel_id)
            if not completions_channel:
                print(f"Stored completions channel ID {completions_channel_id} is invalid, removing from DB")
                self.db.remove_discord_resource(interaction.guild_id, "completions")
        
        if not completions_channel:
            print(f"Creating completions channel for guild {interaction.guild_id}")
            try:
                completions_channel = await interaction.guild.create_text_channel(
                    "🏆・boss-completions",
                    topic="Boss Defeats and Progress Updates - View difficulty channels for rules and leaderboards"
                )
                self.db.store_discord_resource(interaction.guild_id, "completions", completions_channel.id, {'name': completions_channel.name})
                
                try:
                    await completions_channel.edit(position=1)
                except discord.Forbidden:
                    pass
            except Exception as e:
                print(f"Failed to create completions channel: {e}")
        
        leaderboard_channel = await self.leaderboard_manager.get_channel_by_id(interaction.guild_id, user_mode)
        if not leaderboard_channel:
            print(f"No leaderboard channel found for mode {user_mode}")
        
        if completions_channel:
            defeated_boss = self.boss_service.get_next_boss_for_difficulty(boss_number - 1, user_mode)
            next_boss = self.boss_service.get_next_boss_for_difficulty(new_progress, user_mode)
            if user_mode == "extreme" and not next_boss and rolled_next:
                next_boss = rolled_next
            
            mode_info = self.boss_service.get_mode_info(user_mode)
            color_map = {
                "green": discord.Color.green(),
                "blue": discord.Color.blue(),
                "red": discord.Color.red(),
                "purple": discord.Color.purple()
            }
            color = color_map.get(mode_info['color_name'], discord.Color.blue())
            
            title = (
                f"🎉 {mode_info['name']} Completed!" if is_completed and user_mode != "extreme" else "⚔️ Boss Defeated!"
            )
            description = f"**{interaction.user.display_name}** defeated **{defeated_boss}**! ({mode_info['emoji']} {mode_info['name']})"
            
            if is_completed and user_mode != "extreme":
                description += "\n🎊 **Congratulations on completing this difficulty!**"
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color
            )
            embed.add_field(
                name="📈 Progression", 
                value=f"**{new_progress}** bosses defeated", 
                inline=True
            )
            if not is_completed or user_mode == "extreme":
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
