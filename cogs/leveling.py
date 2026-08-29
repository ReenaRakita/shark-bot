# cogs/leveling.py
import time
import random
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS, get_emoji

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

def get_value(shark_name: str) -> float:
    weight = SHARKS[shark_name]["weight"]
    drop_rate = weight / 100
    return round(100 / drop_rate, 2)


# ── Leaderboard dropdown view ──────────────────────────────────────────────
class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild, original_embed):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild = guild
        self.original_embed = original_embed

    @discord.ui.select(
        placeholder="Choose a leaderboard...",
        options=[
            discord.SelectOption(label="Top Catchers", value="catches", emoji="🎣", description="Most sharks caught total"),
            discord.SelectOption(label="Rarest Shark", value="rarest", emoji="💎", description="Who owns the rarest shark"),
            discord.SelectOption(label="Who Owns Most", value="owns_most", emoji="🦈", description="Top owner of each shark type"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        choice = select.values[0]

        if choice == "catches":
            embed = await self.build_catches_embed()
        elif choice == "rarest":
            embed = await self.build_rarest_embed()
        elif choice == "owns_most":
            embed = await self.build_owns_most_embed()

        await interaction.edit_original_response(embed=embed, view=self)

    async def build_catches_embed(self):
        rows = await self.bot.db.fetch(
            "SELECT user_id, total_catches FROM users ORDER BY total_catches DESC LIMIT 10"
        )
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(rows):
            member = self.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User {row['user_id']}"
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{medal} **{name}** — {row['total_catches']:,} catches")

        embed = discord.Embed(
            title="🎣 Top Catchers",
            description="\n".join(lines) if lines else "No catches yet!",
            color=0xf39c12,
        )
        return embed

    async def build_rarest_embed(self):
        # Get all users who have caught at least one shark
        rows = await self.bot.db.fetch(
            "SELECT DISTINCT user_id FROM collection WHERE count > 0"
        )

        user_rarest = []
        for row in rows:
            user_id = row["user_id"]
            # Get all sharks this user owns
            sharks = await self.bot.db.fetch(
                "SELECT shark_type FROM collection WHERE user_id=$1 AND count > 0",
                user_id
            )
            if not sharks:
                continue
            # Find rarest (highest value)
            rarest = max(
                [r["shark_type"] for r in sharks if r["shark_type"] in SHARKS],
                key=lambda s: get_value(s),
                default=None
            )
            if rarest:
                user_rarest.append((user_id, rarest, get_value(rarest)))

        # Sort by value descending
        user_rarest.sort(key=lambda x: x[2], reverse=True)

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, shark_name, value) in enumerate(user_rarest[:10]):
            member = self.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            emoji = get_emoji(shark_name, self.guild)
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{medal} **{name}** — {emoji} {shark_name} ({value} value)")

        embed = discord.Embed(
            title="💎 Rarest Shark Owned",
            description="\n".join(lines) if lines else "No sharks caught yet!",
            color=0x9b59b6,
        )
        return embed

    async def build_owns_most_embed(self):
        lines = []
        for shark_name in SHARKS:
            row = await self.bot.db.fetchrow(
                """SELECT user_id, count FROM collection
                   WHERE shark_type=$1 AND count > 0
                   ORDER BY count DESC LIMIT 1""",
                shark_name
            )
            emoji = get_emoji(shark_name, self.guild)
            if row:
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                lines.append(f"{emoji} **{shark_name}** — {name} ({row['count']})")
            else:
                lines.append(f"{emoji} **{shark_name}** — nobody yet")

        # Split into two columns
        mid = (len(lines) + 1) // 2
        col1 = "\n".join(lines[:mid])
        col2 = "\n".join(lines[mid:])

        embed = discord.Embed(
            title="🦈 Who Owns The Most",
            color=0x3498db,
        )
        embed.add_field(name="\u200b", value=col1, inline=True)
        embed.add_field(name="\u200b", value=col2, inline=True)
        return embed


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

    @app_commands.command(name="leaderboard", description="Server leaderboards")
    async def leaderboard(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return

        # Default view — top catchers
        rows = await self.bot.db.fetch(
            "SELECT user_id, total_catches FROM users ORDER BY total_catches DESC LIMIT 10"
        )
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(rows):
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User {row['user_id']}"
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{medal} **{name}** — {row['total_catches']:,} catches")

        embed = discord.Embed(
            title="🎣 Top Catchers",
            description="\n".join(lines) if lines else "No catches yet!",
            color=0xf39c12,
        )
        embed.set_footer(text="Use the dropdown to switch leaderboards")

        view = LeaderboardView(self.bot, interaction.guild, embed)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
