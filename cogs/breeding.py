# cogs/breeding.py
# Phase 2 — coming soon

from discord.ext import commands


class Breeding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Breeding(bot))