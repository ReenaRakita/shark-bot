# bot.py
import discord
from discord.ext import commands
import asyncpg
import config

COGS = [
    "cogs.catching",
    "cogs.collection",
    "cogs.economy",
    "cogs.leveling",
    "cogs.aquarium",
    "cogs.breeding",
    "cogs.admin",
]

GUILD_ID = 1531903202457288844


class SharkBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, description="The Shark Cult Bot 🦈")
        self.db: asyncpg.Pool | None = None

    async def setup_hook(self):
        print("Connecting to database...")
        self.db = await asyncpg.create_pool(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS,
            min_size=2,
            max_size=10,
        )
        print("Database connected ✅")

        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"  Loaded {cog}")
            except Exception as e:
                print(f"  Failed to load {cog}: {e}")

        print("Syncing slash commands...")
        guild = discord.Object(id=GUILD_ID)

        # Clear global commands to remove duplicates
        self.tree.clear_commands(guild=None)
        await self.tree.sync()

        # Sync only to your guild — instant
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Commands synced ✅")

    async def on_ready(self):
        print(f"\n🦈 {self.user} is online!")
        print(f"   Serving {len(self.guilds)} server(s)")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the depths 🦈",
            )
        )

    async def on_guild_join(self, guild: discord.Guild):
        await self.db.execute(
            "INSERT INTO servers (server_id) VALUES ($1) ON CONFLICT DO NOTHING", guild.id
        )

    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()


bot = SharkBot()

if __name__ == "__main__":
    if not config.TOKEN:
        print("ERROR: DISCORD_TOKEN not set in .env")
        exit(1)
    bot.run(config.TOKEN)
