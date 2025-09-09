import discord
from datetime import datetime, timezone

from bot.services.boss_progression import BossProgressionService


class LeaderboardManager:
    
    def __init__(self, bot, db, boss_service: BossProgressionService):
        self.bot = bot
        self.db = db
        self.boss_service = boss_service
    
    async def get_user_display_name(self, guild_id: int, user_id: int) -> str:
        user = None
        guild = self.bot.get_guild(guild_id)
        
        user = self.bot.get_user(user_id)
        
        if not user:
            try:
                user = await self.bot.fetch_user(user_id)
            except:
                pass
        
        if not user and guild:
            try:
                user = guild.get_member(user_id)
            except:
                pass
        
        if user:
            if hasattr(user, 'display_name') and user.display_name:
                return user.display_name
            elif hasattr(user, 'global_name') and user.global_name:
                return user.global_name
            else:
                return user.name
        else:
            return f"User {user_id}"
    
    async def get_channel_by_id(self, guild_id: int, difficulty: str):
        try:
            channel_id = self.db.get_discord_resource(guild_id, f"channel_{difficulty}")
            if channel_id:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    return guild.get_channel(channel_id)
            return None
        except Exception as e:
            print(f"Error getting channel for {difficulty}: {e}")
            return None
    
    def get_rank_medal(self, rank: int) -> str:
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        else:
            return f"{rank}."
    
    def get_user_mode_rank(self, guild_id: int, user_id: int, mode: str) -> int:
        all_leaderboard = self.db.get_leaderboard(guild_id, limit=1000)
        mode_leaderboard = [user for user in all_leaderboard if user.get('mode', 'normal') == mode]
        
        for i, user_data in enumerate(mode_leaderboard, 1):
            if user_data['user_id'] == user_id:
                return i
        return 0
    
    async def create_normal_mode_content(self, channel, guild_id: int):
        try:

            has_content = False
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    embed = message.embeds[0]
                    if embed.title and ("Boss Progression" in embed.title or "Leaderboard" in embed.title):
                        has_content = True
                        break
            
            if not has_content:

                normal_embed = discord.Embed(
                    title="🛡️ Normal Mode Boss Progression",
                    description="Obor → Phosani's Nightmare",
                    color=discord.Color.blue()
                )
                
                normal_max = self.boss_service.get_max_bosses_for_mode("normal")
                

                normal_text1 = ""
                for i in range(min(23, normal_max)):
                    boss_name = self.boss_service.get_boss_name(i)
                    normal_text1 += f"{i+1}. **{boss_name}**\n"
                
                normal_embed.add_field(
                    name="Bosses 1-23",
                    value=normal_text1,
                    inline=True
                )
                

                if normal_max > 23:
                    normal_text2 = ""
                    for i in range(23, normal_max):
                        boss_name = self.boss_service.get_boss_name(i)
                        normal_text2 += f"{i+1}. **{boss_name}**\n"
                    
                    normal_embed.add_field(
                        name="Bosses 24-46",
                        value=normal_text2,
                        inline=True
                    )
                
                normal_embed.set_footer(text="Normal Mode: Perfect for most players!")
                

                await channel.send(embed=normal_embed)
                await self.ensure_mode_leaderboard(channel, guild_id, "normal")
                
        except Exception as e:
            print(f"Error creating normal mode content: {e}")
    
    async def create_hard_mode_content(self, channel, guild_id: int):
        try:

            has_content = False
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    embed = message.embeds[0]
                    if embed.title and ("Boss Progression" in embed.title or "Leaderboard" in embed.title):
                        has_content = True
                        break
            
            if not has_content:

                hard_embed = discord.Embed(
                    title="💀 Hard Mode Boss Progression",
                    description="Obor → Sol Heredit (All 50 bosses)",
                    color=discord.Color.red()
                )
                

                hard_text1 = ""
                for i in range(min(25, len(self.boss_service.boss_list))):
                    boss_name = self.boss_service.get_boss_name(i)
                    hard_text1 += f"{i+1}. **{boss_name}**\n"
                
                hard_embed.add_field(
                    name="Bosses 1-25",
                    value=hard_text1,
                    inline=True
                )
                

                if len(self.boss_service.boss_list) > 25:
                    hard_text2 = ""
                    for i in range(25, len(self.boss_service.boss_list)):
                        boss_name = self.boss_service.get_boss_name(i)
                        hard_text2 += f"{i+1}. **{boss_name}**\n"
                    
                    hard_embed.add_field(
                        name="Bosses 26-50",
                        value=hard_text2,
                        inline=True
                    )
                
                hard_embed.set_footer(text="Hard Mode: For the bravest challengers!")
                

                await channel.send(embed=hard_embed)
                await self.ensure_mode_leaderboard(channel, guild_id, "hard")
                
        except Exception as e:
            print(f"Error creating hard mode content: {e}")
    
    async def create_difficulty_content(self, channel, guild_id: int, difficulty: str):
        try:
            has_content = await self._check_existing_content(channel)
            
            if not has_content:
                embed = self._create_boss_list_embed(difficulty)
                await channel.send(embed=embed)
                await self.ensure_mode_leaderboard(channel, guild_id, difficulty)
                
        except Exception as e:
            print(f"Error creating {difficulty} mode content: {e}")
    
    async def _check_existing_content(self, channel):
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds:
                embed = message.embeds[0]
                if embed.title and ("Boss Progression" in embed.title or "Leaderboard" in embed.title):
                    return True
        return False
    
    def _create_boss_list_embed(self, difficulty: str):
        mode_info = self.boss_service.get_mode_info(difficulty)
        color_map = {
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "purple": discord.Color.purple()
        }
        color = color_map.get(mode_info['color_name'], discord.Color.blue())
        
        embed = discord.Embed(
            title=f"{mode_info['emoji']} {mode_info['name']} Boss Progression",
            description=mode_info['description'],
            color=color
        )
        
        boss_list = self.boss_service.get_difficulty_boss_list(difficulty)
        
        if difficulty == "extreme":
            embed.add_field(
                name="Starting Boss",
                value="**Corrupted Hunleff**",
                inline=False
            )
            embed.add_field(
                name="After Completion",
                value="Random bosses from the entire boss list",
                inline=False
            )
        else:
            boss_text1, boss_text2 = self._format_boss_list(boss_list)
            
            embed.add_field(
                name=f"Bosses 1-{min(25, len(boss_list))}",
                value=boss_text1,
                inline=True
            )
            
            if len(boss_list) > 25:
                embed.add_field(
                    name=f"Bosses 26-{len(boss_list)}",
                    value=boss_text2,
                    inline=True
                )
        
        embed.set_footer(text=f"{mode_info['name']}: {mode_info['description']}")
        return embed
    
    def _format_boss_list(self, boss_list):
        boss_text1 = ""
        boss_text2 = ""
        
        for i, boss_name in enumerate(boss_list):
            if i < 25:
                boss_text1 += f"{i+1}. **{boss_name}**\n"
            else:
                boss_text2 += f"{i+1}. **{boss_name}**\n"
        
        return boss_text1, boss_text2
    
    async def ensure_mode_leaderboard(self, channel, guild_id: int, mode: str):
        try:
            # Check if we have a stored message ID for this mode
            resource_type = f"leaderboard_{mode}"
            stored_message_id = self.db.get_discord_resource(guild_id, resource_type)
            
            if stored_message_id:
                try:
                    # Try to fetch the stored message
                    stored_message = await channel.fetch_message(stored_message_id)
                    # Message exists and is accessible, we're good
                    return
                except:
                    # Message was deleted, remove from storage
                    self.db.remove_discord_resource(guild_id, resource_type)
            
            # Create initial leaderboard message and store its ID
            message = await self.create_initial_leaderboard(channel, guild_id, mode)
            if message:
                self.db.store_discord_resource(guild_id, resource_type, message.id, {'mode': mode})
                
        except Exception as e:
            print(f"Error ensuring {mode} mode leaderboard: {e}")
    
    async def create_initial_leaderboard(self, channel, guild_id: int, mode: str):
        try:
            mode_info = self.boss_service.get_mode_info(mode)
            color_map = {
                "green": discord.Color.green(),
                "blue": discord.Color.blue(),
                "red": discord.Color.red(),
                "purple": discord.Color.purple()
            }
            color = color_map.get(mode_info['color_name'], discord.Color.blue())
            
            if mode == "extreme":
                # Combine active and archived for extreme so past leavers remain visible
                live = self.db.get_extreme_live_with_archive(guild_id)
                embed = discord.Embed(
                    title=f"{mode_info['emoji']} Extreme Mode Live Progress",
                    description=f"Live rankings - {mode_info['description']}",
                    color=color
                )
                if live:
                    text = ""
                    for i, user_data in enumerate(live[:10], 1):
                        username = await self.get_user_display_name(guild_id, user_data['user_id'])
                        progress = user_data['progress']
                        next_boss = self.boss_service.get_next_boss_for_difficulty(progress, mode)
                        if not next_boss:
                            # fall back to assigned next extreme boss if exists
                            assigned = self.db.get_next_extreme_boss(guild_id, user_data['user_id'])
                            next_boss = assigned or "🎲 Random Boss"
                        medal = self.get_rank_medal(i)
                        text += f"{medal} **{username}** - {progress} defeated | Next: {next_boss}\n"
                    embed.add_field(name="Rankings", value=text, inline=False)
                else:
                    embed.add_field(name="No active participants",
                                    value="Use `/join` to start Extreme Mode.",
                                    inline=False)
                embed.set_footer(text="Last updated")
                embed.timestamp = discord.utils.utcnow()
            
            else:
                finalized = self.db.get_finalized_leaderboard(guild_id, mode)
                live = self.db.get_live_leaderboard(guild_id, mode)
                embed = discord.Embed(
                    title=f"{mode_info['emoji']} {mode_info['name']} Leaderboard",
                    description=f"{mode_info['description']}",
                    color=color
                )
                # Finished section
                if finalized:
                    fin_text = ""
                    for i, row in enumerate(finalized, 1):
                        username = await self.get_user_display_name(guild_id, row['user_id'])
                        medal = self.get_rank_medal(i)
                        when_raw = row.get('completion_time', '')
                        when_fmt = when_raw
                        try:
                            when_dt = datetime.fromisoformat(when_raw.replace('Z', ''))
                            if when_dt.tzinfo is None:
                                when_dt = when_dt.replace(tzinfo=timezone.utc)
                            unix_ts = int(when_dt.timestamp())
                            when_fmt = f"<t:{unix_ts}:f>"
                        except Exception:
                            pass
                        fin_text += f"{medal} **{username}** • finished at {when_fmt}\n"
                    embed.add_field(name="🏁 Finished", value=fin_text, inline=False)
                else:
                    embed.add_field(name="🏁 Finished", value="No finishers yet", inline=False)
                # Divider
                embed.add_field(name="\u200b", value="— — —", inline=False)
                # In-progress section
                if live:
                    prog_text = ""
                    for user_data in live[:10]:
                        username = await self.get_user_display_name(guild_id, user_data['user_id'])
                        progress = user_data['progress']
                        next_boss = self.boss_service.get_next_boss_for_difficulty(progress, mode) or "🎉 COMPLETED!"
                        prog_text += f"• **{username}** — {progress} defeated | Next: {next_boss}\n"
                    embed.add_field(name="⏳ In Progress", value=prog_text, inline=False)
                else:
                    embed.add_field(name="⏳ In Progress", value="No active participants", inline=False)
                embed.set_footer(text="Last updated")
                embed.timestamp = discord.utils.utcnow()
            
            # Send the message and return the message object
            message = await channel.send(embed=embed)
            return message
            
        except Exception as e:
            print(f"Error creating initial {mode} mode leaderboard: {e}")
            return None
    
    async def update_mode_leaderboard(self, channel, guild_id: int, mode: str):
        try:
            leaderboard_message = await self._get_leaderboard_message(channel, guild_id, mode)
            embed = await self._create_leaderboard_embed(guild_id, mode)
            
            if leaderboard_message:
                try:
                    await leaderboard_message.edit(embed=embed)
                except:
                    new_message = await channel.send(embed=embed)
                    self.db.store_discord_resource(guild_id, f"leaderboard_{mode}", new_message.id, {'mode': mode})
            else:
                new_message = await channel.send(embed=embed)
                self.db.store_discord_resource(guild_id, f"leaderboard_{mode}", new_message.id, {'mode': mode})
                
        except Exception as e:
            print(f"Error updating {mode} mode leaderboard: {e}")
    
    async def _get_leaderboard_message(self, channel, guild_id: int, mode: str):
        resource_type = f"leaderboard_{mode}"
        stored_message_id = self.db.get_discord_resource(guild_id, resource_type)
        
        leaderboard_message = None
        if stored_message_id:
            try:
                leaderboard_message = await channel.fetch_message(stored_message_id)
            except:
                self.db.remove_discord_resource(guild_id, resource_type)
                leaderboard_message = None
        
        if not leaderboard_message:
            leaderboard_message = await self._find_existing_leaderboard(channel, guild_id, mode, resource_type)
        
        return leaderboard_message
    
    async def _find_existing_leaderboard(self, channel, guild_id: int, mode: str, resource_type: str):
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds:
                embed = message.embeds[0]
                if mode == "extreme":
                    match_title = f"Extreme Mode Live Progress"
                else:
                    match_title = f"{mode.title()} Mode Finished Leaderboard"
                if embed.title and match_title in embed.title:
                    self.db.store_discord_resource(guild_id, resource_type, message.id, {'mode': mode})
                    return message
        return None
    
    async def _create_leaderboard_embed(self, guild_id: int, mode: str):
        mode_info = self.boss_service.get_mode_info(mode)
        color_map = {
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "purple": discord.Color.purple()
        }
        color = color_map.get(mode_info['color_name'], discord.Color.blue())
        
        if mode == "extreme":
            return await self._create_extreme_embed(guild_id, mode_info, color)
        else:
            return await self._create_standard_embed(guild_id, mode, mode_info, color)
    
    async def _create_extreme_embed(self, guild_id: int, mode_info: dict, color):
        live = self.db.get_extreme_live_with_archive(guild_id)
        embed = discord.Embed(
            title=f"{mode_info['emoji']} Extreme Mode Live Progress",
            description=f"Live rankings - {mode_info['description']}",
            color=color
        )
        if live:
            text = ""
            for i, user_data in enumerate(live[:10], 1):
                username = await self.get_user_display_name(guild_id, user_data['user_id'])
                progress = user_data['progress']
                next_boss = self.boss_service.get_next_boss_for_difficulty(progress, "extreme")
                if not next_boss:
                    assigned = self.db.get_next_extreme_boss(guild_id, user_data['user_id'])
                    next_boss = assigned or "🎲 Random Boss"
                medal = self.get_rank_medal(i)
                text += f"{medal} **{username}** - {progress} defeated | Next: {next_boss}\n"
            embed.add_field(name="Rankings", value=text, inline=False)
        else:
            embed.add_field(name="No active participants",
                            value="Use `/join` to start Extreme Mode.",
                            inline=False)
        embed.set_footer(text="Last updated")
        embed.timestamp = discord.utils.utcnow()
        return embed
    
    async def _create_standard_embed(self, guild_id: int, mode: str, mode_info: dict, color):
        finalized = self.db.get_finalized_leaderboard(guild_id, mode)
        live = self.db.get_live_leaderboard(guild_id, mode)
        embed = discord.Embed(
            title=f"{mode_info['emoji']} {mode_info['name']} Leaderboard",
            description=f"{mode_info['description']}",
            color=color
        )
        
        if finalized:
            fin_text = ""
            for i, row in enumerate(finalized, 1):
                username = await self.get_user_display_name(guild_id, row['user_id'])
                medal = self.get_rank_medal(i)
                when_raw = row.get('completion_time', '')
                when_fmt = when_raw
                try:
                    when_dt = datetime.fromisoformat(when_raw.replace('Z', ''))
                    if when_dt.tzinfo is None:
                        when_dt = when_dt.replace(tzinfo=timezone.utc)
                    unix_ts = int(when_dt.timestamp())
                    when_fmt = f"<t:{unix_ts}:f>"
                except Exception:
                    pass
                fin_text += f"{medal} **{username}** • finished at {when_fmt}\n"
            embed.add_field(name="🏁 Finished", value=fin_text, inline=False)
        else:
            embed.add_field(name="🏁 Finished", value="No finishers yet", inline=False)
        
        embed.add_field(name="\u200b", value="— — —", inline=False)
        
        if live:
            prog_text = ""
            for user_data in live[:10]:
                username = await self.get_user_display_name(guild_id, user_data['user_id'])
                progress = user_data['progress']
                next_boss = self.boss_service.get_next_boss_for_difficulty(progress, mode) or "🎉 COMPLETED!"
                prog_text += f"• **{username}** — {progress} defeated | Next: {next_boss}\n"
            embed.add_field(name="⏳ In Progress", value=prog_text, inline=False)
        else:
            embed.add_field(name="⏳ In Progress", value="No active participants", inline=False)
        
        embed.set_footer(text="Last updated")
        embed.timestamp = discord.utils.utcnow()
        return embed
