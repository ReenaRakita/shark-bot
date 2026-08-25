# cogs/aquarium.py
# Phase 2 — coming soon

from discord.ext import commands

class Aquarium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Aquarium(bot))
