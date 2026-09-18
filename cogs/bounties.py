# cogs/bounties.py
import time
import random
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS

# ── Difficulty colours ────────────────────────────────────────────────────
DIFF_COLOURS = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴", "Weekly": "💜"}

# ── Helper: pick shark of tier ────────────────────────────────────────────
def pick_shark_of_tier(tier: str) -> str:
    return random.choice([n for n, d in SHARKS.items() if d["tier"] == tier])

# ── Daily bounty templates ────────────────────────────────────────────────
# target format: "type:value:goal"
# types: any, tier, specific, time, gift

EASY_TEMPLATES = [
    # quantity - any
    {"task": "Catch 5 sharks",                             "type": "any",      "target": "any",        "n": 5,   "sd": 75,  "xp": 150},
    {"task": "Catch 8 sharks",                             "type": "any",      "target": "any",        "n": 8,   "sd": 75,  "xp": 150},
    {"task": "Catch 10 sharks",                            "type": "any",      "target": "any",        "n": 10,  "sd": 75,  "xp": 150},
    {"task": "Catch 12 sharks",                            "type": "any",      "target": "any",        "n": 12,  "sd": 75,  "xp": 150},
    # tier - common
    {"task": "Catch 5 Common sharks",                      "type": "tier",     "target": "Common",     "n": 5,   "sd": 75,  "xp": 150},
    {"task": "Catch 8 Common sharks",                      "type": "tier",     "target": "Common",     "n": 8,   "sd": 75,  "xp": 150},
    # specific common
    {"task": "Catch a Great White Shark",                  "type": "specific", "target": "Great White","n": 1,   "sd": 75,  "xp": 150},
    {"task": "Catch a Dog Shark",                          "type": "specific", "target": "Dog",        "n": 1,   "sd": 75,  "xp": 150},
    {"task": "Catch a Cat Shark",                          "type": "specific", "target": "Cat",        "n": 1,   "sd": 75,  "xp": 150},
    {"task": "Catch 3 Great White Sharks",                 "type": "specific", "target": "Great White","n": 3,   "sd": 75,  "xp": 150},
    # gifting
    {"task": "Gift a shark to a friend",                   "type": "gift",     "target": "any",        "n": 1,   "sd": 75,  "xp": 150},
    # time based
    {"task": "Catch a shark in under 10 seconds",          "type": "time",     "target": "10",         "n": 1,   "sd": 75,  "xp": 150},
    {"task": "Catch a shark in under 20 seconds",          "type": "time",     "target": "20",         "n": 1,   "sd": 75,  "xp": 150},
]

MEDIUM_TEMPLATES = [
    # quantity - any
    {"task": "Catch 15 sharks",                            "type": "any",      "target": "any",        "n": 15,  "sd": 200, "xp": 400},
    {"task": "Catch 20 sharks",                            "type": "any",      "target": "any",        "n": 20,  "sd": 200, "xp": 400},
    {"task": "Catch 25 sharks",                            "type": "any",      "target": "any",        "n": 25,  "sd": 200, "xp": 400},
    # tier
    {"task": "Catch 5 Uncommon sharks",                    "type": "tier",     "target": "Uncommon",   "n": 5,   "sd": 200, "xp": 400},
    {"task": "Catch 8 Uncommon sharks",                    "type": "tier",     "target": "Uncommon",   "n": 8,   "sd": 200, "xp": 400},
    {"task": "Catch 3 Rare sharks",                        "type": "tier",     "target": "Rare",       "n": 3,   "sd": 200, "xp": 400},
    {"task": "Catch 5 Rare sharks",                        "type": "tier",     "target": "Rare",       "n": 5,   "sd": 200, "xp": 400},
    # specific uncommon
    {"task": "Catch a Spinner Shark",                      "type": "specific", "target": "Spinner",    "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Nurse Shark",                        "type": "specific", "target": "Nurse",      "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Lemon Shark",                        "type": "specific", "target": "Lemon",      "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Bull Shark",                         "type": "specific", "target": "Bull",       "n": 1,   "sd": 200, "xp": 400},
    # specific rare
    {"task": "Catch a Tiger Shark",                        "type": "specific", "target": "Tiger",      "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Hammerhead Shark",                   "type": "specific", "target": "Hammerhead", "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Whale Shark",                        "type": "specific", "target": "Whale",      "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a Swell Shark",                        "type": "specific", "target": "Swell",      "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch a School Shark",                       "type": "specific", "target": "School",     "n": 1,   "sd": 200, "xp": 400},
    # gifting
    {"task": "Gift 3 sharks to friends",                   "type": "gift",     "target": "any",        "n": 3,   "sd": 200, "xp": 400},
    {"task": "Gift a Rare shark to a friend",              "type": "gift",     "target": "Rare",       "n": 1,   "sd": 200, "xp": 400},
    # time based
    {"task": "Catch a shark in under 5 seconds",           "type": "time",     "target": "5",          "n": 1,   "sd": 200, "xp": 400},
    {"task": "Catch 3 sharks each in under 15 seconds",    "type": "time",     "target": "15",         "n": 3,   "sd": 200, "xp": 400},
]

HARD_TEMPLATES = [
    # quantity - any
    {"task": "Catch 30 sharks",                            "type": "any",      "target": "any",        "n": 30,  "sd": 400, "xp": 700},
    {"task": "Catch 40 sharks",                            "type": "any",      "target": "any",        "n": 40,  "sd": 400, "xp": 700},
    {"task": "Catch 50 sharks",                            "type": "any",      "target": "any",        "n": 50,  "sd": 400, "xp": 700},
    # tier
    {"task": "Catch 2 Epic sharks",                        "type": "tier",     "target": "Epic",       "n": 2,   "sd": 400, "xp": 700},
    {"task": "Catch 3 Epic sharks",                        "type": "tier",     "target": "Epic",       "n": 3,   "sd": 400, "xp": 700},
    {"task": "Catch 8 Rare sharks",                        "type": "tier",     "target": "Rare",       "n": 8,   "sd": 400, "xp": 700},
    {"task": "Catch 10 Uncommon sharks",                   "type": "tier",     "target": "Uncommon",   "n": 10,  "sd": 400, "xp": 700},
    # specific epic
    {"task": "Catch a Thresher Shark",                     "type": "specific", "target": "Thresher",   "n": 1,   "sd": 400, "xp": 700},
    {"task": "Catch a Wobbegong Shark",                    "type": "specific", "target": "Wobbegong",  "n": 1,   "sd": 400, "xp": 700},
    {"task": "Catch a Sixgill Shark",                      "type": "specific", "target": "Sixgill",    "n": 1,   "sd": 400, "xp": 700},
    {"task": "Catch a Greenland Shark",                    "type": "specific", "target": "Greenland",  "n": 1,   "sd": 400, "xp": 700},
    # specific rare x multiple
    {"task": "Catch 3 Tiger Sharks",                       "type": "specific", "target": "Tiger",      "n": 3,   "sd": 400, "xp": 700},
    {"task": "Catch 3 Hammerhead Sharks",                  "type": "specific", "target": "Hammerhead", "n": 3,   "sd": 400, "xp": 700},
    # gifting
    {"task": "Gift 5 sharks to friends",                   "type": "gift",     "target": "any",        "n": 5,   "sd": 400, "xp": 700},
    {"task": "Gift an Epic shark to a friend",             "type": "gift",     "target": "Epic",       "n": 1,   "sd": 400, "xp": 700},
    # time based
    {"task": "Catch a shark in under 3 seconds",           "type": "time",     "target": "3",          "n": 1,   "sd": 400, "xp": 700},
    {"task": "Catch 5 sharks each in under 10 seconds",    "type": "time",     "target": "10",         "n": 5,   "sd": 400, "xp": 700},
]

WEEKLY_TEMPLATES = [
    {"task": "Catch a Ninja Shark",                        "type": "specific", "target": "Ninja",      "n": 1,   "sd": 1500, "xp": 1500},
    {"task": "Catch a Dwarf Shark",                        "type": "specific", "target": "Dwarf",      "n": 1,   "sd": 1500, "xp": 1500},
    {"task": "Catch a Cookiecutter Shark",                 "type": "specific", "target": "Cookiecutter","n": 1,  "sd": 1500, "xp": 1500},
    {"task": "Catch a Ghost Shark",                        "type": "specific", "target": "Ghost",      "n": 1,   "sd": 1500, "xp": 1500},
    {"task": "Catch a Goblin Shark",                       "type": "specific", "target": "Goblin",     "n": 1,   "sd": 1500, "xp": 1500},
    {"task": "Catch a Basking Shark",                      "type": "specific", "target": "Basking",    "n": 1,   "sd": 1500, "xp": 1500},
    {"task": "Catch 100 sharks",                           "type": "any",      "target": "any",        "n": 100, "sd": 1500, "xp": 1500},
    {"task": "Catch 5 Epic sharks",                        "type": "tier",     "target": "Epic",       "n": 5,   "sd": 1500, "xp": 1500},
    {"task": "Catch 2 Legendary sharks",                   "type": "tier",     "target": "Legendary",  "n": 2,   "sd": 1500, "xp": 1500},
    {"task": "Catch 3 Mythic sharks",                      "type": "tier",     "target": "Mythic",     "n": 3,   "sd": 1500, "xp": 1500},
    {"task": "Gift 10 sharks to friends",                  "type": "gift",     "target": "any",        "n": 10,  "sd": 1500, "xp": 1500},
    {"task": "Catch a shark in under 2 seconds",           "type": "time",     "target": "2",          "n": 1,   "sd": 1500, "xp": 1500},
]


def progress_bar(current: int, goal: int) -> str:
    filled = int((min(current, goal) / goal) * 10)
    return "█" * filled + "░" * (10 - filled)


def encode_target(t: dict) -> str:
    return f"{t['type']}:{t['target']}:{t['n']}"


class Bounties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Ensure server-wide weekly bounty exists ────────────────────────────
    async def ensure_weekly(self) -> dict:
        now = int(time.time())
        week_start = now - (now % 604800)
        week_end = week_start + 604800

        row = await self.bot.db.fetchrow(
            "SELECT * FROM weekly_bounty WHERE week_start=$1", week_start
        )
        if not row:
            tmpl = random.choice(WEEKLY_TEMPLATES)
            await self.bot.db.execute(
                """INSERT INTO weekly_bounty (task, target, reward_sd, reward_xp, week_start, expires_at)
                   VALUES ($1,$2,$3,$4,$5,$6)""",
                tmpl["task"], encode_target(tmpl),
                tmpl["sd"], tmpl["xp"], week_start, week_end
            )
            row = await self.bot.db.fetchrow(
                "SELECT * FROM weekly_bounty WHERE week_start=$1", week_start
            )
        return dict(row)

    # ── Ensure user daily bounties ────────────────────────────────────────
    async def ensure_dailies(self, user_id: int):
        now = int(time.time())
        today_start = now - (now % 86400)
        today_end = today_start + 86400

        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND is_weekly=false AND expires_at>$2",
            user_id, now
        )
        if rows:
            return  # already has today's dailies

        await self.bot.db.execute(
            "DELETE FROM bounties WHERE user_id=$1 AND is_weekly=false", user_id
        )

        # Pick one from each difficulty
        picks = [
            random.choice(EASY_TEMPLATES),
            random.choice(MEDIUM_TEMPLATES),
            random.choice(HARD_TEMPLATES),
        ]
        for tmpl in picks:
            await self.bot.db.execute(
                """INSERT INTO bounties (user_id, task, target, reward_sd, reward_xp, is_weekly, completed, expires_at, progress)
                   VALUES ($1,$2,$3,$4,$5,false,false,$6,0)""",
                user_id, tmpl["task"], encode_target(tmpl),
                tmpl["sd"], tmpl["xp"], today_end
            )

    # ── Ensure user has weekly progress row ────────────────────────────────
    async def ensure_weekly_progress(self, user_id: int, weekly_id: int):
        await self.bot.db.execute(
            """INSERT INTO weekly_progress (user_id, weekly_id, progress, completed)
               VALUES ($1,$2,0,false) ON CONFLICT DO NOTHING""",
            user_id, weekly_id
        )

    # ── Update progress after a catch ─────────────────────────────────────
    async def update_bounties(self, user_id: int, shark_name: str, channel, catch_time: float = None):
        now = int(time.time())
        shark_tier = SHARKS[shark_name]["tier"] if shark_name in SHARKS else None

        # ── Daily bounties ────────────────────────────────────────────────
        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND completed=false AND expires_at>$2 AND is_weekly=false",
            user_id, now
        )
        for row in rows:
            b_type, b_target, b_goal = row["target"].split(":")
            b_goal = int(b_goal)
            counts = False

            if b_type == "any":
                counts = True
            elif b_type == "specific" and shark_name == b_target:
                counts = True
            elif b_type == "tier" and shark_tier == b_target:
                counts = True
            elif b_type == "time" and catch_time is not None:
                counts = catch_time <= float(b_target)

            if not counts:
                continue

            new_progress = (row["progress"] or 0) + 1
            await self.bot.db.execute(
                "UPDATE bounties SET progress=$1 WHERE id=$2", new_progress, row["id"]
            )
            if new_progress >= b_goal:
                await self._complete_daily(user_id, row, channel)

        # ── Weekly bounty ─────────────────────────────────────────────────
        weekly = await self.ensure_weekly()
        await self.ensure_weekly_progress(user_id, weekly["id"])

        wp = await self.bot.db.fetchrow(
            "SELECT * FROM weekly_progress WHERE user_id=$1 AND weekly_id=$2",
            user_id, weekly["id"]
        )
        if wp["completed"]:
            return

        b_type, b_target, b_goal = weekly["target"].split(":")
        b_goal = int(b_goal)
        counts = False

        if b_type == "any":
            counts = True
        elif b_type == "specific" and shark_name == b_target:
            counts = True
        elif b_type == "tier" and shark_tier == b_target:
            counts = True
        elif b_type == "time" and catch_time is not None:
            counts = catch_time <= float(b_target)

        if counts:
            new_progress = (wp["progress"] or 0) + 1
            await self.bot.db.execute(
                "UPDATE weekly_progress SET progress=$1 WHERE user_id=$2 AND weekly_id=$3",
                new_progress, user_id, weekly["id"]
            )
            if new_progress >= b_goal:
                await self._complete_weekly(user_id, weekly, channel)

    # ── Update progress after a gift ──────────────────────────────────────
    async def update_gift_bounties(self, user_id: int, shark_name: str, channel):
        now = int(time.time())
        shark_tier = SHARKS[shark_name]["tier"] if shark_name in SHARKS else None

        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND completed=false AND expires_at>$2 AND is_weekly=false",
            user_id, now
        )
        for row in rows:
            b_type, b_target, b_goal = row["target"].split(":")
            b_goal = int(b_goal)
            if b_type != "gift":
                continue
            counts = b_target == "any" or shark_tier == b_target
            if not counts:
                continue
            new_progress = (row["progress"] or 0) + 1
            await self.bot.db.execute(
                "UPDATE bounties SET progress=$1 WHERE id=$2", new_progress, row["id"]
            )
            if new_progress >= b_goal:
                await self._complete_daily(user_id, row, channel)

        # Weekly gift bounty
        weekly = await self.ensure_weekly()
        await self.ensure_weekly_progress(user_id, weekly["id"])
        wp = await self.bot.db.fetchrow(
            "SELECT * FROM weekly_progress WHERE user_id=$1 AND weekly_id=$2",
            user_id, weekly["id"]
        )
        if wp["completed"]:
            return
        b_type, b_target, b_goal = weekly["target"].split(":")
        b_goal = int(b_goal)
        if b_type == "gift":
            counts = b_target == "any" or shark_tier == b_target
            if counts:
                new_progress = (wp["progress"] or 0) + 1
                await self.bot.db.execute(
                    "UPDATE weekly_progress SET progress=$1 WHERE user_id=$2 AND weekly_id=$3",
                    new_progress, user_id, weekly["id"]
                )
                if new_progress >= b_goal:
                    await self._complete_weekly(user_id, weekly, channel)

    async def _complete_daily(self, user_id: int, row, channel):
        await self.bot.db.execute("UPDATE bounties SET completed=true WHERE id=$1", row["id"])
        await self.bot.db.execute(
            """INSERT INTO users (user_id, shark_dollars) VALUES ($1,$2)
               ON CONFLICT (user_id) DO UPDATE SET shark_dollars=users.shark_dollars+$2""",
            user_id, row["reward_sd"]
        )
        await self.bot.db.execute(
            """INSERT INTO profiles (user_id, guild_id, xp) VALUES ($1,$2,$3)
               ON CONFLICT (user_id, guild_id) DO UPDATE SET xp=profiles.xp+$3""",
            user_id, channel.guild.id, row["reward_xp"]
        )
        await channel.send(
            f"🎯 <@{user_id}> completed a **Daily Bounty**: *{row['task']}*\n"
            f"Reward: **{row['reward_sd']:,} SD** + **{row['reward_xp']:,} XP** 🎉"
        )

    async def _complete_weekly(self, user_id: int, weekly: dict, channel):
        await self.bot.db.execute(
            "UPDATE weekly_progress SET completed=true WHERE user_id=$1 AND weekly_id=$2",
            user_id, weekly["id"]
        )
        await self.bot.db.execute(
            """INSERT INTO users (user_id, shark_dollars) VALUES ($1,$2)
               ON CONFLICT (user_id) DO UPDATE SET shark_dollars=users.shark_dollars+$2""",
            user_id, weekly["reward_sd"]
        )
        await self.bot.db.execute(
            """INSERT INTO profiles (user_id, guild_id, xp) VALUES ($1,$2,$3)
               ON CONFLICT (user_id, guild_id) DO UPDATE SET xp=profiles.xp+$3""",
            user_id, channel.guild.id, weekly["reward_xp"]
        )
        await channel.send(
            f"💜 <@{user_id}> completed the **Weekly Bounty**: *{weekly['task']}*\n"
            f"Reward: **{weekly['reward_sd']:,} SD** + **{weekly['reward_xp']:,} XP** 🎊"
        )

    # ── /bounties ─────────────────────────────────────────────────────────
    @app_commands.command(name="bounties", description="View your daily and weekly bounties")
    async def bounties_cmd(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()
        user_id = interaction.user.id
        now = int(time.time())

        await self.ensure_dailies(user_id)
        weekly = await self.ensure_weekly()
        await self.ensure_weekly_progress(user_id, weekly["id"])

        embed = discord.Embed(
            title=f"🎯 {interaction.user.display_name}'s Bounties",
            color=0x9b59b6
        )

        # Daily bounties
        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND is_weekly=false AND expires_at>$2 ORDER BY reward_sd ASC",
            user_id, now
        )
        diff_map = {75: "Easy", 200: "Medium", 400: "Hard"}
        for row in rows:
            b_type, b_target, b_goal = row["target"].split(":")
            b_goal = int(b_goal)
            current = row["progress"] or 0
            diff = diff_map.get(row["reward_sd"], "Daily")
            icon = DIFF_COLOURS.get(diff, "🔵")
            bar = progress_bar(current, b_goal)
            expires_in = row["expires_at"] - now
            hrs = expires_in // 3600
            mins = (expires_in % 3600) // 60
            status = "✅ Done!" if row["completed"] else f"`{bar}` {current}/{b_goal}"
            embed.add_field(
                name=f"{icon} [{diff}] {row['task']}",
                value=f"{status}\n**{row['reward_sd']:,} SD** + **{row['reward_xp']:,} XP** — Expires {hrs}h {mins}m",
                inline=False
            )

        # Weekly bounty
        wp = await self.bot.db.fetchrow(
            "SELECT * FROM weekly_progress WHERE user_id=$1 AND weekly_id=$2",
            user_id, weekly["id"]
        )
        b_type, b_target, b_goal = weekly["target"].split(":")
        b_goal = int(b_goal)
        current = wp["progress"] if wp else 0
        bar = progress_bar(current, b_goal)
        expires_in = weekly["expires_at"] - now
        days = expires_in // 86400
        hrs = (expires_in % 86400) // 3600
        status = "✅ Done!" if (wp and wp["completed"]) else f"`{bar}` {current}/{b_goal}"
        embed.add_field(
            name=f"💜 [Weekly — same for everyone] {weekly['task']}",
            value=f"{status}\n**{weekly['reward_sd']:,} SD** + **{weekly['reward_xp']:,} XP** — Expires {days}d {hrs}h",
            inline=False
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Bounties(bot))
