# cogs/collection.py
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS, get_emoji


def get_value(shark_name: str) -> str:
    """Calculate shark value using same formula as cat-bot: 100 / drop_rate%"""
    weight = SHARKS[shark_name]["weight"]
    drop_rate = weight / 100  # convert to percentage
    value = round(100 / drop_rate, 2)
    return f"{value}"


class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="catalogue", description="View all 22 shark types and their values")
    async def catalogue(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return

        await interaction.response.defer()

        # Get server-wide counts for all shark types in one query
        rows = await self.bot.db.fetch(
            "SELECT shark_type, SUM(count) as total FROM collection GROUP BY shark_type"
        )
        server_counts = {row["shark_type"]: row["total"] for row in rows}

        embed = discord.Embed(
            title="🦈 The Catalogue",
            color=0x3498db,
        )

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

    @app_commands.command(name="tank", description="View your shark collection")
    @app_commands.describe(member="Whose collection to view (leave blank for yourself)")
    async def tank(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return

        target = member or interaction.user

        rows = await self.bot.db.fetch(
            "SELECT shark_type, count FROM collection WHERE user_id=$1 AND count > 0 ORDER BY count DESC",
            target.id,
        )

        if not rows:
            await interaction.response.send_message(
                f"{target.display_name} has not caught any sharks yet!", ephemeral=True
            )
            return

        total_sharks = sum(r["count"] for r in rows)

        # Calculate total SD value of collection
        total_value = 0
        lines = []
        for row in rows:
            name = row["shark_type"]
            count = row["count"]
            emoji = get_emoji(name, interaction.guild) if name in SHARKS else "🦈"
            value_each = float(get_value(name)) if name in SHARKS else 0
            value_total = round(value_each * count, 2)
            total_value += value_total
            lines.append(f"{emoji} **{name}** x{count} — {value_total} value")

        embed = discord.Embed(
            title=f"🦈 {target.display_name}'s Tank",
            description="\n".join(lines),
            color=0x2980b9,
        )
        embed.set_footer(text=f"Total: {total_sharks} sharks — {round(total_value, 2)} total value")
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Collection(bot))