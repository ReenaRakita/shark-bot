# cogs/leveling.py
import time
import random
import discord
from discord.ext import commands
from discord import app_commands
import config

LEVEL_ROLES = {
    5:  "Fin",
    15: "Predator",
    30: "Apex",
    50: "Ancient One",
}

def xp_for_level(level):
    return sum(i * 100 for i in range(1, level + 1))

def level_from_xp(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        level += 1
    return level


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        user_id = message.author.id
        guild_id = message.guild.id
        now = int(time.time())
        profile = await self.bot.db.fetchrow(
            "SELECT xp, level, last_xp_ts FROM profiles WHERE user_id=$1 AND guild_id=$2",
            user_id, guild_id,
        )
        if profile and now - profile["last_xp_ts"] < config.XP_COOLDOWN:
            return
        xp_gained = random.randint(config.XP_MIN, config.XP_MAX)
        if not profile:
            await self.bot.db.execute(
                "INSERT INTO profiles (user_id, guild_id, xp, level, last_xp_ts) VALUES ($1,$2,$3,0,$4)",
                user_id, guild_id, xp_gained, now,
            )
            new_xp = xp_gained
            old_level = 0
        else:
            new_xp = profile["xp"] + xp_gained
            old_level = profile["level"]
            await self.bot.db.execute(
                "UPDATE profiles SET xp=$1, last_xp_ts=$2 WHERE user_id=$3 AND guild_id=$4",
                new_xp, now, user_id, guild_id,
            )
        new_level = level_from_xp(new_xp)
        if new_level > old_level:
            await self.bot.db.execute(
                "UPDATE profiles SET level=$1 WHERE user_id=$2 AND guild_id=$3",
                new_level, user_id, guild_id,
            )
            await message.channel.send(
                f"🦈 {message.author.mention} leveled up to **Level {new_level}**!"
            )
            await self.assign_level_role(message.author, message.guild, new_level)

    async def assign_level_role(self, member, guild, level):
        for required_level, role_name in sorted(LEVEL_ROLES.items()):
            if level >= required_level:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass

    @app_commands.command(name="rank", description="Check your level and XP")
    @app_commands.describe(member="The member to check (leave blank for yourself)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        target = member or interaction.user
        profile = await self.bot.db.fetchrow(
            "SELECT xp, level FROM profiles WHERE user_id=$1 AND guild_id=$2",
            target.id, interaction.guild_id,
        )
        if not profile:
            await interaction.response.send_message(
                f"{target.display_name} has not sent any messages yet!", ephemeral=True
            )
            return
        xp = profile["xp"]
        level = profile["level"]
        xp_needed = xp_for_level(level + 1)
        xp_current = xp_for_level(level)
        xp_progress = xp - xp_current
        xp_to_next = xp_needed - xp_current
        filled = int((xp_progress / xp_to_next) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        embed = discord.Embed(title=f"🦈 {target.display_name}'s Rank", color=0x3498db)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP", value=str(xp), inline=True)
        embed.add_field(
            name=f"Progress to Level {level+1}",
            value=f"`{bar}` {xp_progress}/{xp_to_next} XP",
            inline=False,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Top 10 members by XP in this server")
    async def leaderboard(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        rows = await self.bot.db.fetch(
            "SELECT user_id, xp, level FROM profiles WHERE guild_id=$1 ORDER BY xp DESC LIMIT 10",
            interaction.guild_id,
        )
        if not rows:
            await interaction.response.send_message("No one has earned XP yet!", ephemeral=True)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(rows):
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User {row['user_id']}"
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{medal} **{name}** — Level {row['level']} ({row['xp']} XP)")
        embed = discord.Embed(
            title="🦈 Shark Cult Leaderboard",
            description="\n".join(lines),
            color=0xf39c12,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
