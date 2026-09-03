# cogs/collection.py
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS, get_emoji

RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]


def get_value(shark_name: str) -> float:
    weight = SHARKS[shark_name]["weight"]
    drop_rate = weight / 100
    return round(100 / drop_rate, 2)


def fmt_time(seconds: float) -> str:
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{round(seconds, 2)}s"
    minutes = int(seconds // 60)
    secs = round(seconds % 60, 2)
    return f"{minutes}m {secs}s"


class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /catalogue ────────────────────────────────────────────────────────
    @app_commands.command(name="catalogue", description="View all 22 shark types and their values")
    async def catalogue(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()
        rows = await self.bot.db.fetch(
            "SELECT shark_type, SUM(count) as total FROM collection GROUP BY shark_type"
        )
        server_counts = {row["shark_type"]: row["total"] for row in rows}
        embed = discord.Embed(title="🦈 The Catalogue", color=0x3498db)
        for name in SHARKS:
            emoji = get_emoji(name, interaction.guild)
            drop = SHARKS[name]["weight"] / 100
            value = get_value(name)
            count = server_counts.get(name, 0)
            embed.add_field(
                name=f"{emoji} {name} ({drop:.2f}%)",
                value=f"{value} value\n{count:,} in this server",
                inline=True,
            )
        await interaction.followup.send(embed=embed)

    # ── /tank ─────────────────────────────────────────────────────────────
    @app_commands.command(name="tank", description="View your shark collection")
    @app_commands.describe(member="Whose collection to view (leave blank for yourself)")
    async def tank(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()
        target = member or interaction.user
        rows = await self.bot.db.fetch(
            "SELECT shark_type, count FROM collection WHERE user_id=$1 AND count > 0",
            target.id,
        )
        if not rows:
            await interaction.followup.send(
                f"{target.display_name} has not caught any sharks yet!", ephemeral=True
            )
            return
        user_row = await self.bot.db.fetchrow(
            "SELECT fastest_catch, slowest_catch FROM users WHERE user_id=$1", target.id
        )
        fastest = user_row["fastest_catch"] if user_row else None
        slowest = user_row["slowest_catch"] if user_row else None
        collection = {row["shark_type"]: row["count"] for row in rows}
        total_sharks = sum(collection.values())
        total_value = sum(
            get_value(name) * count
            for name, count in collection.items()
            if name in SHARKS
        )
        sorted_sharks = []
        for tier in RARITY_ORDER:
            for name in SHARKS:
                if SHARKS[name]["tier"] == tier and name in collection:
                    sorted_sharks.append(name)
        sharks_list = [
            f"{get_emoji(name, interaction.guild)} **{name}** {collection[name]}"
            for name in sorted_sharks
        ]
        mid = (len(sharks_list) + 1) // 2
        col1 = sharks_list[:mid]
        col2 = sharks_list[mid:]
        embed = discord.Embed(color=0x2980b9)
        embed.title = f"🦈 {target.display_name}"
        embed.description = (
            f"⚡ Fastest: {fmt_time(fastest)}, Slowest: {fmt_time(slowest)}\n"
            f"🦈 Sharks: {total_sharks:,}, Value: {round(total_value, 2):,}"
        )
        embed.add_field(name="\u200b", value="\n".join(col1), inline=True)
        if col2:
            embed.add_field(name="\u200b", value="\n".join(col2), inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    # ── /gift ─────────────────────────────────────────────────────────────
    @app_commands.command(name="gift", description="Gift a shark to another member")
    @app_commands.describe(member="Who to gift to", shark_type="Which shark to gift")
    async def gift(self, interaction: discord.Interaction, member: discord.Member, shark_type: str):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await interaction.response.defer()

        shark_type = shark_type.title()

        if member.id == interaction.user.id:
            await interaction.followup.send("You cannot gift yourself.", ephemeral=True)
            return
        if shark_type not in SHARKS:
            await interaction.followup.send(f"Unknown shark: **{shark_type}**", ephemeral=True)
            return

        row = await self.bot.db.fetchrow(
            "SELECT count FROM collection WHERE user_id=$1 AND shark_type=$2",
            interaction.user.id, shark_type
        )
        if not row or row["count"] < 1:
            await interaction.followup.send(
                f"You don't have any **{shark_type} Sharks** to gift!", ephemeral=True
            )
            return

        # Remove from giver
        await self.bot.db.execute(
            "UPDATE collection SET count=count-1 WHERE user_id=$1 AND shark_type=$2",
            interaction.user.id, shark_type
        )
        # Add to receiver
        await self.bot.db.execute(
            """INSERT INTO collection (user_id, shark_type, count) VALUES ($1, $2, 1)
               ON CONFLICT (user_id, shark_type) DO UPDATE SET count=collection.count+1""",
            member.id, shark_type
        )

        emoji = get_emoji(shark_type, interaction.guild)
        await interaction.followup.send(
            f"🎁 **{interaction.user.display_name}** gifted {emoji} **{shark_type} Shark** to {member.mention}!"
        )

    @gift.autocomplete("shark_type")
    async def gift_autocomplete(self, interaction: discord.Interaction, current: str):
        rows = await self.bot.db.fetch(
            "SELECT shark_type, count FROM collection WHERE user_id=$1 AND count > 0 ORDER BY count DESC",
            interaction.user.id
        )
        choices = [
            app_commands.Choice(
                name=f"{row['shark_type']} (x{row['count']})",
                value=row["shark_type"]
            )
            for row in rows
            if current.lower() in row["shark_type"].lower()
        ]
        return choices[:25]


async def setup(bot):
    await bot.add_cog(Collection(bot))
