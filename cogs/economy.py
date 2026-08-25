# cogs/economy.py
import time
import discord
from discord.ext import commands
from discord import app_commands
import config
from data.sharks import SHARKS

SELL_VALUES = {
    "Common": 10, "Uncommon": 25, "Rare": 75,
    "Epic": 200, "Legendary": 600, "Mythic": 2000,
}

def get_sell_value(shark_name):
    return SELL_VALUES[SHARKS[shark_name]["tier"]]


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_user(self, user_id):
        await self.bot.db.execute(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
        )

    @app_commands.command(name="balance", description="Check your Shark Dollars")
    async def balance(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await self.ensure_user(interaction.user.id)
        row = await self.bot.db.fetchrow(
            "SELECT shark_dollars FROM users WHERE user_id=$1", interaction.user.id
        )
        embed = discord.Embed(
            title=f"💰 {interaction.user.display_name}'s Balance",
            description=f"**{row['shark_dollars']:,} Shark Dollars**",
            color=0xf1c40f,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily Shark Dollars")
    async def daily(self, interaction: discord.Interaction):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        await self.ensure_user(interaction.user.id)
        row = await self.bot.db.fetchrow(
            "SELECT daily_last FROM users WHERE user_id=$1", interaction.user.id
        )
        now = int(time.time())
        if now - row["daily_last"] < 86400:
            remaining = 86400 - (now - row["daily_last"])
            hours = remaining // 3600
            mins = (remaining % 3600) // 60
            await interaction.response.send_message(
                f"Already claimed! Come back in **{hours}h {mins}m**.", ephemeral=True
            )
            return
        await self.bot.db.execute(
            "UPDATE users SET shark_dollars=shark_dollars+$1, daily_last=$2 WHERE user_id=$3",
            config.DAILY_REWARD, now, interaction.user.id,
        )
        embed = discord.Embed(
            title="💰 Daily Claimed!",
            description=f"You received **{config.DAILY_REWARD:,} Shark Dollars**!\nCome back tomorrow!",
            color=0xf1c40f,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Sell a shark for Shark Dollars")
    @app_commands.describe(shark="The shark type to sell", amount="How many to sell")
    async def sell(self, interaction: discord.Interaction, shark: str, amount: int = 1):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        shark = shark.title()
        if shark not in SHARKS:
            await interaction.response.send_message(f"Unknown shark: **{shark}**", ephemeral=True)
            return
        if amount < 1:
            await interaction.response.send_message("Amount must be at least 1.", ephemeral=True)
            return
        row = await self.bot.db.fetchrow(
            "SELECT count FROM collection WHERE user_id=$1 AND shark_type=$2",
            interaction.user.id, shark,
        )
        if not row or row["count"] < amount:
            have = row["count"] if row else 0
            await interaction.response.send_message(f"You only have **{have}** {shark} Shark(s).", ephemeral=True)
            return
        value = get_sell_value(shark) * amount
        await self.ensure_user(interaction.user.id)
        await self.bot.db.execute(
            "UPDATE collection SET count=count-$1 WHERE user_id=$2 AND shark_type=$3",
            amount, interaction.user.id, shark,
        )
        await self.bot.db.execute(
            "UPDATE users SET shark_dollars=shark_dollars+$1 WHERE user_id=$2",
            value, interaction.user.id,
        )
        embed = discord.Embed(
            title="💰 Sharks Sold!",
            description=f"Sold **{amount}x {shark} Shark** {SHARKS[shark]['emoji']}\nEarned: **{value:,} Shark Dollars**",
            color=0xf1c40f,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Send Shark Dollars to another member")
    @app_commands.describe(member="Who to pay", amount="How much to send")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not await config.check_channel(interaction, config.CHANNEL_CATCHING):
            return
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot pay yourself.", ephemeral=True)
            return
        if amount < 1:
            await interaction.response.send_message("Amount must be at least 1.", ephemeral=True)
            return
        await self.ensure_user(interaction.user.id)
        await self.ensure_user(member.id)
        row = await self.bot.db.fetchrow(
            "SELECT shark_dollars FROM users WHERE user_id=$1", interaction.user.id
        )
        if row["shark_dollars"] < amount:
            await interaction.response.send_message(f"You only have **{row['shark_dollars']:,} SD**.", ephemeral=True)
            return
        await self.bot.db.execute(
            "UPDATE users SET shark_dollars=shark_dollars-$1 WHERE user_id=$2", amount, interaction.user.id
        )
        await self.bot.db.execute(
            "UPDATE users SET shark_dollars=shark_dollars+$1 WHERE user_id=$2", amount, member.id
        )
        embed = discord.Embed(
            title="💸 Payment Sent!",
            description=f"**{interaction.user.display_name}** sent **{amount:,} SD** to {member.mention}",
            color=0x2ecc71,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
