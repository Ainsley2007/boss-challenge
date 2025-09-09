import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.services.boss_progression import BossProgressionService

load_dotenv()

class EventBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        await self.load_extension('bot.cogs.event')
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await self.ensure_leaderboard_channels()
    
    async def ensure_leaderboard_channels(self):
        for guild in self.guilds:
            category = await self.ensure_boss_challenge_category(guild)
            svc = BossProgressionService()
            easy_count = svc.get_max_bosses_for_mode("easy")
            normal_count = svc.get_max_bosses_for_mode("normal")
            hard_count = svc.get_max_bosses_for_mode("hard")
            difficulties = [
                ("easy", "🌱", f"Easy Mode Challenge - Obor to TOA 150 Invocation ({easy_count} bosses)"),
                ("normal", "🛡️", f"Normal Mode Challenge - Obor to Phosani's Nightmare ({normal_count} bosses)"),
                ("hard", "🔥", f"Hard Mode Challenge - Obor to Sol Heredit ({hard_count} bosses)"),
                ("extreme", "💀", "Extreme Mode Challenge - Corrupted Hunleff to Infinite Random")
            ]
            for difficulty, emoji, topic in difficulties:
                await self.ensure_difficulty_channel(guild, difficulty, emoji, topic, category)
            await self.ensure_completions_channel(guild, category)
            await self.ensure_info_channel(guild, category)
            await self.position_category_channels(guild, category)
    
    async def ensure_boss_challenge_category(self, guild):
        styled_name = "╔═══Boss Challenge═══╗"
        existing = discord.utils.get(guild.categories, name=styled_name)
        if existing:
            return existing
        try:
            category = await guild.create_category(styled_name)
            return category
        except discord.Forbidden:
            return None
        except Exception:
            return None
    
    async def ensure_difficulty_channel(self, guild, difficulty, emoji, topic, category):
        try:
            from bot.db.tiny import get_database
            db = get_database()
            
            channel_name = f"{emoji}・{difficulty}"
            channel = None
            
            stored_channel_id = db.get_discord_resource(guild.id, f"channel_{difficulty}")
            
            if stored_channel_id:
                channel = guild.get_channel(stored_channel_id)
                if channel:
                    print(f"Found valid {difficulty} channel: {channel.name}")
                    if category and channel.category != category:
                        try:
                            await channel.edit(category=category)
                        except discord.Forbidden:
                            pass
                    try:
                        await self._create_channel_content(channel, guild.id, difficulty)
                    except Exception as e:
                        print(f"Error creating content for {difficulty} channel: {e}")
                    return
                else:
                    print(f"Stored {difficulty} channel ID {stored_channel_id} is invalid, removing from DB")
                    db.remove_discord_resource(guild.id, f"channel_{difficulty}")
            
            print(f"Creating new {difficulty} channel: {channel_name}")
            channel = await guild.create_text_channel(
                channel_name,
                topic=topic,
                category=category
            )
            self._store_channel_id(guild.id, difficulty, channel.id, channel_name)
            await self._create_channel_content(channel, guild.id, difficulty)
                    
        except discord.Forbidden:
            print(f"No permission to create boss-challenge-{difficulty} channel in {guild.name}")
        except Exception as e:
            print(f"Error with boss-challenge-{difficulty} channel in {guild.name}: {e}")
    
    def _store_channel_id(self, guild_id, difficulty, channel_id, channel_name):
        from bot.db.tiny import get_database
        db = get_database()
        db.store_discord_resource(guild_id, f"channel_{difficulty}", channel_id, {'name': channel_name})
    
    async def _create_channel_content(self, channel, guild_id, difficulty):
        event_cog = self.get_cog('EventCog')
        if not event_cog:
            return
            
        if difficulty == "normal":
            await event_cog.create_normal_mode_content(channel, guild_id)
        elif difficulty == "hard":
            await event_cog.create_hard_mode_content(channel, guild_id)
        else:
            await event_cog.create_difficulty_content(channel, guild_id, difficulty)
        
        await event_cog.ensure_mode_leaderboard(channel, guild_id, difficulty)
    
    async def ensure_completions_channel(self, guild, category):
        try:
            from bot.db.tiny import get_database
            db = get_database()
            
            completions_channel_name = "🏆・boss-completions"
            
            stored_channel_id = db.get_discord_resource(guild.id, "completions")
            
            if stored_channel_id:
                channel = guild.get_channel(stored_channel_id)
                if channel:
                    print(f"Found valid completions channel: {channel.name}")
                    if category and channel.category != category:
                        try:
                            await channel.edit(category=category)
                        except discord.Forbidden:
                            pass
                    return
                else:
                    print(f"Stored completions channel ID {stored_channel_id} is invalid, removing from DB")
                    db.remove_discord_resource(guild.id, "completions")
            print(f"Creating new completions channel: {completions_channel_name}")
            channel = await guild.create_text_channel(
                completions_channel_name,
                topic="Boss Defeats and Progress Updates - View difficulty channels for rules and leaderboards",
                category=category
            )
            db.store_discord_resource(guild.id, "completions", channel.id, {'name': completions_channel_name})
            
            try:
                await channel.edit(position=1)
            except discord.Forbidden:
                pass
                        
        except discord.Forbidden:
            print(f"No permission to create boss-completions channel in {guild.name}")
        except Exception as e:
            print(f"Error with boss-completions channel in {guild.name}: {e}")

    async def position_category_channels(self, guild, category):
        if not category:
            return
        try:
            from bot.db.tiny import get_database
            db = get_database()
            info_channel_id = db.get_discord_resource(guild.id, "info")
            if info_channel_id:
                info = guild.get_channel(info_channel_id)
                if info and info.category == category:
                    try:
                        await info.edit(position=0)
                    except discord.Forbidden:
                        pass
            completions_channel_id = db.get_discord_resource(guild.id, "completions")
            if completions_channel_id:
                completions = guild.get_channel(completions_channel_id)
                if completions and completions.category == category:
                    try:
                        await completions.edit(position=1)
                    except discord.Forbidden:
                        pass
            order = [
                ("easy", "🌱"),
                ("normal", "🛡️"),
                ("hard", "🔥"),
                ("extreme", "💀"),
            ]
            next_pos = 2
            for difficulty, emoji in order:
                name = f"{emoji}・{difficulty}"
                ch = discord.utils.get(guild.text_channels, name=name)
                if ch and ch.category == category:
                    try:
                        await ch.edit(position=next_pos)
                        next_pos += 1
                    except discord.Forbidden:
                        continue
        except Exception:
            pass

    async def ensure_info_channel(self, guild, category):
        try:
            info_icon = "ℹ️"
            base_name = "boss-challenge-info"
            full_name = f"{info_icon}・{base_name}"
            info_channel = discord.utils.get(guild.text_channels, name=full_name)
            if not info_channel:
                info_channel = await guild.create_text_channel(full_name, category=category)
                from bot.db.tiny import get_database
                db = get_database()
                db.store_discord_resource(guild.id, "info", info_channel.id, {'name': full_name})
            elif category and info_channel.category != category:
                try:
                    await info_channel.edit(category=category)
                except discord.Forbidden:
                    pass
            try:
                await info_channel.edit(position=0)
            except discord.Forbidden:
                pass
            try:
                messages = [msg async for msg in info_channel.history(limit=10)]
                has_commands_embed = any(
                    msg.embeds and msg.author == self.user and 
                    msg.embeds[0].title == "🏆 Boss Challenge Commands" 
                    for msg in messages
                )
                has_event_embed = any(
                    msg.embeds and msg.author == self.user and 
                    msg.embeds[0].title == "📖 About the Boss Challenge"
                    for msg in messages
                )
                
                if not has_event_embed:
                    svc = BossProgressionService()
                    easy_count = svc.get_max_bosses_for_mode("easy")
                    normal_count = svc.get_max_bosses_for_mode("normal")
                    hard_count = svc.get_max_bosses_for_mode("hard")
                    event_embed = discord.Embed(
                        title="📖 About the Boss Challenge",
                        description="Progress through RuneScape bosses in order. Complete one boss, move to the next.",
                        color=discord.Color.blue()
                    )
                    event_embed.add_field(
                        name="🌱 Easy Mode", 
                        value=f"{easy_count} bosses: Obor → TOA 150 Invocation", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="🛡️ Normal Mode", 
                        value=f"{normal_count} bosses: Obor → Phosani's Nightmare", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="🔥 Hard Mode", 
                        value=f"{hard_count} bosses: Obor → Sol Heredit", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="💀 Extreme Mode", 
                        value="Infinite: Corrupted Hunleff → Random bosses", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="📝 Core Rules", 
                        value="• Submit before/after screenshots\n• One boss at a time in order\n• Death = reset progress to 0", 
                        inline=False
                    )
                    event_embed.add_field(
                        name="💰 Economy Rules", 
                        value="• Only boss loot can be sold for money\n• No other money-making methods\n• Can buy from Grand Exchange & shops\n• No picking up spawned items", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="⚔️ Gear Restrictions", 
                        value="• Only items buyable from GE/shops\n• No void, dragon defender, arclight, etc.\n• Start with nothing after death", 
                        inline=True
                    )
                    event_embed.add_field(
                        name="🎥 Example", 
                        value="[Settled - Killing every Boss in Runescape, using ONLY their loot](https://www.youtube.com/watch?v=9eMCUVVmgBs)", 
                        inline=False
                    )
                    await info_channel.send(embed=event_embed)
                    
                if not has_commands_embed:
                    embed = discord.Embed(
                        title="🏆 Boss Challenge Commands",
                        description="Use these slash commands to participate in the boss challenge!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="🎯 ```/join```", 
                        value="Join the boss challenge by selecting a difficulty mode", 
                        inline=False
                    )
                    embed.add_field(
                        name="🚪 ```/leave```", 
                        value="Leave the challenge", 
                        inline=False
                    )
                    embed.add_field(
                        name="🔄 ```/reset```", 
                        value="Reset your progress back to **0**, if you died", 
                        inline=False
                    )
                    embed.add_field(
                        name="✅ ```/submit```", 
                        value="Submit **before** & **after** screenshots of your boss kill", 
                        inline=False
                    )
                    await info_channel.send(embed=embed)
            except Exception:
                pass
        except discord.Forbidden:
            pass

async def main():
    bot = EventBot()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())

