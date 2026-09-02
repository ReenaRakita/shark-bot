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
    return round(100 / (weight / 100), 2)

def fmt_time(seconds):
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{round(seconds, 2)}s"
    m = int(seconds // 60)
    s = round(seconds % 60, 2)
    return f"{m}m {s}s"


# ── Sharks sub-view (shown when Sharks is selected) ────────────────────────
class LeaderboardSharksView(discord.ui.View):
    def __init__(self, bot, guild):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild

    @discord.ui.select(
        placeholder="Main category...",
        row=0,
        options=[
            discord.SelectOption(label="Sharks", value="sharks", emoji="🦈", default=True),
            discord.SelectOption(label="Value", value="value", emoji="💰"),
            discord.SelectOption(label="Fast", value="fast", emoji="⚡"),
            discord.SelectOption(label="Slow", value="slow", emoji="🐢"),
            discord.SelectOption(label="Shark Dollars", value="sd", emoji="💵"),
        ]
    )
    async def main_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if choice == "sharks":
            await interaction.response.defer()
            return
        # Switch to main view for other categories
        view = LeaderboardMainView(self.bot, self.guild)
        embed = await view.build_embed(choice)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.select(
        placeholder="Select shark type...",
        row=1,
        options=[
            discord.SelectOption(label="All", value="All"),
            discord.SelectOption(label="Great White", value="Great White"),
            discord.SelectOption(label="Dog", value="Dog"),
            discord.SelectOption(label="Cat", value="Cat"),
            discord.SelectOption(label="Spinner", value="Spinner"),
            discord.SelectOption(label="Nurse", value="Nurse"),
            discord.SelectOption(label="Lemon", value="Lemon"),
            discord.SelectOption(label="Bull", value="Bull"),
            discord.SelectOption(label="Tiger", value="Tiger"),
            discord.SelectOption(label="Hammerhead", value="Hammerhead"),
            discord.SelectOption(label="Swell", value="Swell"),
            discord.SelectOption(label="Whale", value="Whale"),
            discord.SelectOption(label="School", value="School"),
            discord.SelectOption(label="Thresher", value="Thresher"),
            discord.SelectOption(label="Wobbegong", value="Wobbegong"),
            discord.SelectOption(label="Sixgill", value="Sixgill"),
            discord.SelectOption(label="Greenland", value="Greenland"),
            discord.SelectOption(label="Basking", value="Basking"),
            discord.SelectOption(label="Goblin", value="Goblin"),
            discord.SelectOption(label="Ghost", value="Ghost"),
            discord.SelectOption(label="Cookiecutter", value="Cookiecutter"),
            discord.SelectOption(label="Dwarf", value="Dwarf"),
            discord.SelectOption(label="Ninja", value="Ninja"),
        ]
    )
    async def shark_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        shark_type = select.values[0]
        embed = await self.build_sharks_embed(shark_type)
        await interaction.response.edit_message(embed=embed, view=self)

    async def build_sharks_embed(self, shark_type: str):
        medals = ["🥇", "🥈", "🥉"]
        if shark_type == "All":
            rows = await self.bot.db.fetch(
                """SELECT user_id, SUM(count) as total FROM collection
                   GROUP BY user_id ORDER BY total DESC LIMIT 10"""
            )
            lines = []
            for i, row in enumerate(rows):
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {row['total']:,} sharks")
            return discord.Embed(
                title="🦈 Most Sharks — All Types",
                description="\n".join(lines) if lines else "No catches yet!",
                color=0x3498db,
            )
        else:
            emoji = get_emoji(shark_type, self.guild)
            rows = await self.bot.db.fetch(
                """SELECT user_id, count FROM collection
                   WHERE shark_type=$1 AND count > 0
                   ORDER BY count DESC LIMIT 10""",
                shark_type
            )
            lines = []
            for i, row in enumerate(rows):
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {row['count']:,}")
            return discord.Embed(
                title=f"{emoji} Most {shark_type} Sharks",
                description="\n".join(lines) if lines else "Nobody has caught this shark yet!",
                color=0x3498db,
            )


# ── Main leaderboard view ──────────────────────────────────────────────────
class LeaderboardMainView(discord.ui.View):
    def __init__(self, bot, guild):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild

    @discord.ui.select(
        placeholder="Choose a leaderboard...",
        options=[
            discord.SelectOption(label="Sharks", value="sharks", emoji="🦈"),
            discord.SelectOption(label="Value", value="value", emoji="💰"),
            discord.SelectOption(label="Fast", value="fast", emoji="⚡"),
            discord.SelectOption(label="Slow", value="slow", emoji="🐢"),
            discord.SelectOption(label="Shark Dollars", value="sd", emoji="💵"),
        ]
    )
    async def main_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if choice == "sharks":
            # Switch to sharks view with sub-dropdown
            view = LeaderboardSharksView(self.bot, self.guild)
            embed = await view.build_sharks_embed("All")
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            embed = await self.build_embed(choice)
            await interaction.response.edit_message(embed=embed, view=self)

    async def build_embed(self, choice: str):
        medals = ["🥇", "🥈", "🥉"]

        if choice == "value":
            # Calculate total value per user
            rows = await self.bot.db.fetch(
                "SELECT user_id, shark_type, count FROM collection WHERE count > 0"
            )
            user_values = {}
            for row in rows:
                uid = row["user_id"]
                name = row["shark_type"]
                if name not in SHARKS:
                    continue
                val = get_value(name) * row["count"]
                user_values[uid] = user_values.get(uid, 0) + val

            sorted_users = sorted(user_values.items(), key=lambda x: x[1], reverse=True)[:10]
            lines = []
            for i, (uid, val) in enumerate(sorted_users):
                member = self.guild.get_member(uid)
                name = member.display_name if member else f"User {uid}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {round(val, 2):,} value")
            return discord.Embed(
                title="💰 Most Valuable Collections",
                description="\n".join(lines) if lines else "No data yet!",
                color=0xf1c40f,
            )

        elif choice == "fast":
            rows = await self.bot.db.fetch(
                """SELECT user_id, fastest_catch FROM users
                   WHERE fastest_catch IS NOT NULL
                   ORDER BY fastest_catch ASC LIMIT 10"""
            )
            lines = []
            for i, row in enumerate(rows):
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {fmt_time(row['fastest_catch'])}")
            return discord.Embed(
                title="⚡ Fastest Catches",
                description="\n".join(lines) if lines else "No catches yet!",
                color=0x2ecc71,
            )

        elif choice == "slow":
            rows = await self.bot.db.fetch(
                """SELECT user_id, slowest_catch FROM users
                   WHERE slowest_catch IS NOT NULL
                   ORDER BY slowest_catch DESC LIMIT 10"""
            )
            lines = []
            for i, row in enumerate(rows):
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {fmt_time(row['slowest_catch'])}")
            return discord.Embed(
                title="🐢 Slowest Catches",
                description="\n".join(lines) if lines else "No catches yet!",
                color=0xe74c3c,
            )

        elif choice == "sd":
            rows = await self.bot.db.fetch(
                """SELECT user_id, shark_dollars FROM users
                   ORDER BY shark_dollars DESC LIMIT 10"""
            )
            lines = []
            for i, row in enumerate(rows):
                member = self.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User {row['user_id']}"
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{medal} **{name}** — {row['shark_dollars']:,} SD")
            return discord.Embed(
                title="💵 Most Shark Dollars",
                description="\n".join(lines) if lines else "No data yet!",
                color=0xf39c12,
            )


# ── Cog ───────────────────────────────────────────────────────────────────
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

        # Default: sharks all
        view = LeaderboardSharksView(self.bot, interaction.guild)
        embed = await view.build_sharks_embed("All")
        embed.set_footer(text="Use the dropdowns to switch leaderboards")
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Leveling(bot))