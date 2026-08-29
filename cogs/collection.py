# cogs/collection.py
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS, get_emoji


class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="catalogue", description="View all 22 shark types and their drop rates")
    async def catalogue(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return

        lines = []
        for name, data in SHARKS.items():
            emoji = get_emoji(name, interaction.guild)
            lines.append(f"{emoji} **{name}** — {data['weight']/100:.2f}%")

        embed = discord.Embed(
            title="🦈 Shark Catalogue",
            description="\n".join(lines),
            color=0x3498db,
        )
        await interaction.response.send_message(embed=embed)

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

        total = sum(r["count"] for r in rows)
        lines = []
        for row in rows:
            name = row["shark_type"]
            emoji = get_emoji(name, interaction.guild) if name in SHARKS else "🦈"
            lines.append(f"{emoji} **{name}** — {row['count']}")

        embed = discord.Embed(
            title=f"🦈 {target.display_name}'s Tank",
            description="\n".join(lines),
            color=0x2980b9,
        )
        embed.set_footer(text=f"Total sharks: {total}")
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Collection(bot))
