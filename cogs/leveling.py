# cogs/leveling.py
# /rank removed as requested
# /leaderboard fixed with defer

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

MAIN_OPTIONS = [
    ("Sharks",        "sharks", "🦈"),
    ("Value",         "value",  "💰"),
    ("Fast",          "fast",   "⚡"),
    ("Slow",          "slow",   "🐢"),
    ("Shark Dollars", "sd",     "💵"),
]

SHARK_OPTIONS = ["All"] + list(SHARKS.keys())

def xp_for_level(level):
    return sum(i * 100 for i in range(1, level + 1))

def level_from_xp(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        level += 1
    return level

def get_value(shark_name: str) -> float:
    return round(100 / (SHARKS[shark_name]["weight"] / 100), 2)

def fmt_time(seconds):
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{round(seconds, 2)}s"
    m = int(seconds // 60)
    s = round(seconds % 60, 2)
    return f"{m}m {s}s"

def build_main_select(selected: str, row: int) -> discord.ui.Select:
    options = [
        discord.SelectOption(label=label, value=val, emoji=emoji, default=(val == selected))
        for label, val, emoji in MAIN_OPTIONS
    ]
    sel = discord.ui.Select(options=options, row=row)
    return sel

def build_shark_select(selected: str, row: int) -> discord.ui.Select:
    options = [
        discord.SelectOption(label=s, value=s, default=(s == selected))
        for s in SHARK_OPTIONS
    ]
    sel = discord.ui.Select(placeholder=selected, options=options, row=row)
    return sel


class LeaderboardSharksView(discord.ui.View):
    def __init__(self, bot, guild, shark_selected="All"):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.shark_selected = shark_selected

        main_sel = build_main_select("sharks", row=0)
        main_sel.callback = self.main_callback
        self.add_item(main_sel)

        shark_sel = build_shark_select(shark_selected, row=1)
        shark_sel.callback = self.shark_callback
        self.add_item(shark_sel)

    async def main_callback(self, interaction: discord.Interaction):
        choice = interaction.data["values"][0]
        if choice == "sharks":
            await interaction.response.defer()
            return
        view = LeaderboardMainView(self.bot, self.guild, selected=choice)
        embed = await view.build_embed(choice)
        await interaction.response.edit_message(embed=embed, view=view)

    async def shark_callback(self, interaction: discord.Interaction):
        shark_type = interaction.data["values"][0]
        view = LeaderboardSharksView(self.bot, self.guild, shark_selected=shark_type)
        embed = await self.build_sharks_embed(shark_type)
        await interaction.response.edit_message(embed=embed, view=view)

    async def build_sharks_embed(self, shark_type: str):
        if shark_type == "All":
            rows = await self.bot.db.fetch(
                """SELECT user_id, SUM(count) as total FROM collection
                   GROUP BY user_id ORDER BY total DESC LIMIT 15"""
            )
            lines = []
            for i, row in enumerate(rows, 1):
                member = self.guild.get_member(row["user_id"])
                name = member.mention if member else f"User {row['user_id']}"
                lines.append(f"{i}. **{row['total']:,}** sharks: {name}")
            return discord.Embed(
                title="🦈 Sharks — All",
                description="\n".join(lines) if lines else "No catches yet!",
                color=0x3498db,
            )
        else:
            emoji = get_emoji(shark_type, self.guild)
            rows = await self.bot.db.fetch(
                """SELECT user_id, count FROM collection
                   WHERE shark_type=$1 AND count > 0
                   ORDER BY count DESC LIMIT 15""",
                shark_type
            )
            lines = []
            for i, row in enumerate(rows, 1):
                member = self.guild.get_member(row["user_id"])
                name = member.mention if member else f"User {row['user_id']}"
                lines.append(f"{i}. **{row['count']:,}** {shark_type}: {name}")
            return discord.Embed(
                title=f"{emoji} Sharks — {shark_type}",
                description="\n".join(lines) if lines else "Nobody has caught this shark yet!",
                color=0x3498db,
            )


class LeaderboardMainView(discord.ui.View):
    def __init__(self, bot, guild, selected="value"):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.selected = selected

        main_sel = build_main_select(selected, row=0)
        main_sel.callback = self.main_callback
        self.add_item(main_sel)

    async def main_callback(self, interaction: discord.Interaction):
        choice = interaction.data["values"][0]
        if choice == "sharks":
            view = LeaderboardSharksView(self.bot, self.guild)
            embed = await view.build_sharks_embed("All")
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            view = LeaderboardMainView(self.bot, self.guild, selected=choice)
            embed = await view.build_embed(choice)
            await interaction.response.edit_message(embed=embed, view=view)

    async def build_embed(self, choice: str):
        if choice == "value":
            rows = await self.bot.db.fetch(
                "SELECT user_id, shark_type, count FROM collection WHERE count > 0"
            )
            user_values = {}
            for row in rows:
                uid = row["user_id"]
                n = row["shark_type"]
                if n not in SHARKS:
                    continue
                user_values[uid] = user_values.get(uid, 0) + get_value(n) * row["count"]
            sorted_users = sorted(user_values.items(), key=lambda x: x[1], reverse=True)[:15]
            lines = []
            for i, (uid, val) in enumerate(sorted_users, 1):
                member = self.guild.get_member(uid)
                name = member.mention if member else f"User {uid}"
                lines.append(f"{i}. **{round(val, 2):,}** value: {name}")
            return discord.Embed(title="💰 Value Leaderboard", description="\n".join(lines) if lines else "No data yet!", color=0xf1c40f)

        elif choice == "fast":
            rows = await self.bot.db.fetch(
                "SELECT user_id, fastest_catch FROM users WHERE fastest_catch IS NOT NULL ORDER BY fastest_catch ASC LIMIT 15"
            )
            lines = []
            for i, r in enumerate(rows, 1):
                member = self.guild.get_member(r["user_id"])
                name = member.mention if member else f"User {r['user_id']}"
                lines.append(f"{i}. **{fmt_time(r['fastest_catch'])}**: {name}")
            return discord.Embed(title="⚡ Fastest Catches", description="\n".join(lines) if lines else "No catches yet!", color=0x2ecc71)

        elif choice == "slow":
            rows = await self.bot.db.fetch(
                "SELECT user_id, slowest_catch FROM users WHERE slowest_catch IS NOT NULL ORDER BY slowest_catch DESC LIMIT 15"
            )
            lines = []
            for i, r in enumerate(rows, 1):
                member = self.guild.get_member(r["user_id"])
                name = member.mention if member else f"User {r['user_id']}"
                lines.append(f"{i}. **{fmt_time(r['slowest_catch'])}**: {name}")
            return discord.Embed(title="🐢 Slowest Catches", description="\n".join(lines) if lines else "No catches yet!", color=0xe74c3c)

        elif choice == "sd":
            rows = await self.bot.db.fetch(
                "SELECT user_id, shark_dollars FROM users ORDER BY shark_dollars DESC LIMIT 15"
            )
            lines = []
            for i, r in enumerate(rows, 1):
                member = self.guild.get_member(r["user_id"])
                name = member.mention if member else f"User {r['user_id']}"
                lines.append(f"{i}. **{r['shark_dollars']:,}** SD: {name}")
            return discord.Embed(title="💵 Shark Dollars Leaderboard", description="\n".join(lines) if lines else "No data yet!", color=0xf39c12)


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

    @app_commands.command(name="leaderboard", description="Server leaderboards")
    async def leaderboard(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()
        view = LeaderboardSharksView(self.bot, interaction.guild)
        embed = await view.build_sharks_embed("All")
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
