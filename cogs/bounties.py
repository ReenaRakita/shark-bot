# cogs/bounties.py
import time
import random
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS

TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]

DAILY_BOUNTIES = [
    # Easy
    {"task": "Catch {n} sharks of any type",  "type": "any",      "n": 5,  "tier": None,       "sd": 75,   "xp": 150},
    {"task": "Catch {n} sharks of any type",  "type": "any",      "n": 8,  "tier": None,       "sd": 75,   "xp": 150},
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Common",   "sd": 75,   "xp": 150},
    {"task": "Catch {n} Common sharks",       "type": "tier",     "n": 5,  "tier": "Common",   "sd": 75,   "xp": 150},
    # Medium
    {"task": "Catch {n} sharks of any type",  "type": "any",      "n": 15, "tier": None,       "sd": 200,  "xp": 400},
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Uncommon", "sd": 200,  "xp": 400},
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Rare",     "sd": 200,  "xp": 400},
    {"task": "Catch {n} Rare sharks",         "type": "tier",     "n": 3,  "tier": "Rare",     "sd": 200,  "xp": 400},
    {"task": "Catch {n} Uncommon sharks",     "type": "tier",     "n": 5,  "tier": "Uncommon", "sd": 200,  "xp": 400},
    # Hard
    {"task": "Catch {n} sharks of any type",  "type": "any",      "n": 30, "tier": None,       "sd": 400,  "xp": 700},
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Epic",     "sd": 400,  "xp": 700},
    {"task": "Catch {n} Epic sharks",         "type": "tier",     "n": 2,  "tier": "Epic",     "sd": 400,  "xp": 700},
    {"task": "Catch {n} Rare sharks",         "type": "tier",     "n": 8,  "tier": "Rare",     "sd": 400,  "xp": 700},
]

WEEKLY_BOUNTIES = [
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Legendary","sd": 1500, "xp": 1500},
    {"task": "Catch a {shark} Shark",         "type": "specific", "n": 1,  "tier": "Mythic",   "sd": 1500, "xp": 1500},
    {"task": "Catch {n} sharks of any type",  "type": "any",      "n": 100,"tier": None,       "sd": 1500, "xp": 1500},
    {"task": "Catch {n} Epic sharks",         "type": "tier",     "n": 5,  "tier": "Epic",     "sd": 1500, "xp": 1500},
    {"task": "Catch {n} Legendary sharks",    "type": "tier",     "n": 2,  "tier": "Legendary","sd": 1500, "xp": 1500},
]

DIFF_COLOURS = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴", "Weekly": "💜"}


def pick_shark_of_tier(tier: str) -> str:
    return random.choice([n for n, d in SHARKS.items() if d["tier"] == tier])


def generate_bounty(tmpl: dict) -> dict:
    b = dict(tmpl)
    if b["type"] == "specific":
        shark = pick_shark_of_tier(b["tier"])
        b["task"] = b["task"].format(shark=shark)
        b["target"] = shark
    elif b["type"] == "tier":
        b["task"] = b["task"].format(n=b["n"])
        b["target"] = b["tier"]
    elif b["type"] == "any":
        b["task"] = b["task"].format(n=b["n"])
        b["target"] = "any"
    b["goal"] = b["n"]
    return b


def get_difficulty(sd: int, is_weekly: bool) -> str:
    if is_weekly:
        return "Weekly"
    if sd == 75:
        return "Easy"
    if sd == 200:
        return "Medium"
    return "Hard"


def progress_bar(current: int, goal: int) -> str:
    filled = int((min(current, goal) / goal) * 10)
    return "█" * filled + "░" * (10 - filled)


class Bounties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_bounties(self, user_id: int):
        now = int(time.time())
        today_start = now - (now % 86400)
        week_start  = now - (now % 604800)

        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND completed=false AND expires_at>$2",
            user_id, now
        )
        has_daily  = any(not r["is_weekly"] for r in rows)
        has_weekly = any(r["is_weekly"] for r in rows)

        if not has_daily:
            await self.bot.db.execute(
                "DELETE FROM bounties WHERE user_id=$1 AND is_weekly=false", user_id
            )
            templates = random.sample(DAILY_BOUNTIES, 3)
            for tmpl in templates:
                b = generate_bounty(tmpl)
                await self.bot.db.execute(
                    """INSERT INTO bounties
                       (user_id, task, target, reward_sd, reward_xp, is_weekly, completed, expires_at, progress)
                       VALUES ($1,$2,$3,$4,$5,false,false,$6,0)""",
                    user_id, b["task"],
                    f"{b['type']}:{b['target']}:{b['goal']}",
                    b["sd"], b["xp"], today_start + 86400
                )

        if not has_weekly:
            await self.bot.db.execute(
                "DELETE FROM bounties WHERE user_id=$1 AND is_weekly=true", user_id
            )
            tmpl = random.choice(WEEKLY_BOUNTIES)
            b = generate_bounty(tmpl)
            await self.bot.db.execute(
                """INSERT INTO bounties
                   (user_id, task, target, reward_sd, reward_xp, is_weekly, completed, expires_at, progress)
                   VALUES ($1,$2,$3,$4,$5,true,false,$6,0)""",
                user_id, b["task"],
                f"{b['type']}:{b['target']}:{b['goal']}",
                b["sd"], b["xp"], week_start + 604800
            )

    async def update_bounties(self, user_id: int, shark_name: str, channel):
        now = int(time.time())
        rows = await self.bot.db.fetch(
            "SELECT * FROM bounties WHERE user_id=$1 AND completed=false AND expires_at>$2",
            user_id, now
        )
        shark_tier = SHARKS[shark_name]["tier"] if shark_name in SHARKS else None

        for row in rows:
            b_type, b_target, b_goal = row["target"].split(":")
            b_goal = int(b_goal)

            counts = (
                b_type == "any" or
                (b_type == "specific" and shark_name == b_target) or
                (b_type == "tier" and shark_tier == b_target)
            )
            if not counts:
                continue

            new_progress = (row["progress"] or 0) + 1
            await self.bot.db.execute(
                "UPDATE bounties SET progress=$1 WHERE id=$2",
                new_progress, row["id"]
            )

            if new_progress >= b_goal:
                await self.bot.db.execute(
                    "UPDATE bounties SET completed=true WHERE id=$1", row["id"]
                )
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
                label = "Weekly Bounty" if row["is_weekly"] else "Bounty"
                await channel.send(
                    f"🎯 <@{user_id}> completed a **{label}**: *{row['task']}*\n"
                    f"Reward: **{row['reward_sd']:,} SD** + **{row['reward_xp']:,} XP** 🎉"
                )

    @app_commands.command(name="bounties", description="View your daily and weekly bounties")
    async def bounties_cmd(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()
        user_id = interaction.user.id
        await self.ensure_bounties(user_id)

        now = int(time.time())
        rows = await self.bot.db.fetch(
            """SELECT * FROM bounties WHERE user_id=$1 AND expires_at>$2
               ORDER BY is_weekly ASC, id ASC""",
            user_id, now
        )

        embed = discord.Embed(
            title=f"🎯 {interaction.user.display_name}'s Bounties",
            color=0x9b59b6
        )

        for row in rows:
            b_type, b_target, b_goal = row["target"].split(":")
            b_goal = int(b_goal)
            current = row["progress"] or 0
            diff = get_difficulty(row["reward_sd"], row["is_weekly"])
            icon = DIFF_COLOURS[diff]
            bar = progress_bar(current, b_goal)
            expires_in = row["expires_at"] - now
            hrs = expires_in // 3600
            mins = (expires_in % 3600) // 60
            label = "Weekly" if row["is_weekly"] else diff
            status = "✅ Completed!" if row["completed"] else f"`{bar}` {current}/{b_goal}"

            embed.add_field(
                name=f"{icon} [{label}] {row['task']}",
                value=(
                    f"{status}\n"
                    f"**{row['reward_sd']:,} SD** + **{row['reward_xp']:,} XP**\n"
                    f"Expires in: {hrs}h {mins}m"
                ),
                inline=False
            )

        if not rows:
            embed.description = "No active bounties. Try again later!"

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Bounties(bot))
