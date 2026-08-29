# cogs/catching.py
import random
import time
import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import config
from data.sharks import SHARKS, SHARK_NAMES, SHARK_WEIGHTS, get_tier_colour, get_emoji


class Catching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sharks = {}
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(seconds=30)
    async def spawn_loop(self):
        now = time.time()
        try:
            rows = await self.bot.db.fetch(
                "SELECT channel_id FROM channels WHERE next_spawn <= $1", now
            )
        except Exception:
            return
        for row in rows:
            channel_id = row["channel_id"]
            if channel_id in self.active_sharks:
                continue
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
            await self.spawn_shark(channel)
            channel_row = await self.bot.db.fetchrow(
                "SELECT spawn_min, spawn_max FROM channels WHERE channel_id=$1", channel_id
            )
            spawn_min = channel_row["spawn_min"] if channel_row else config.SPAWN_MIN
            spawn_max = channel_row["spawn_max"] if channel_row else config.SPAWN_MAX
            next_spawn = now + random.randint(spawn_min, spawn_max)
            await self.bot.db.execute(
                "UPDATE channels SET last_spawn=$1, next_spawn=$2 WHERE channel_id=$3",
                now, next_spawn, channel_id,
            )

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        await self.bot.wait_until_ready()

    # ── Spawn a shark ─────────────────────────────────────────────────────
    async def spawn_shark(self, channel, forced_shark: str = None):
        # Use forced shark if specified, otherwise random
        if forced_shark and forced_shark in SHARKS:
            shark_name = forced_shark
        else:
            shark_name = random.choices(SHARK_NAMES, weights=SHARK_WEIGHTS, k=1)[0]

        shark = SHARKS[shark_name]

        self.active_sharks[channel.id] = {
            "type": shark_name,
            "spawned_at": time.time(),
            "message": None,
        }

        emoji = get_emoji(shark_name, channel.guild)

        embed = discord.Embed(
            title=f"{emoji} {shark_name} Shark has appeared!",
            description=f'Type **"nom"** to catch it!\n\n*{shark["description"]}*',
            color=get_tier_colour(shark_name),
        )

        image_name = shark_name.lower().replace(" ", "_") + ".png"
        image_path = f"assets/images/sharks/{image_name}"
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=image_name)
            embed.set_image(url=f"attachment://{image_name}")

        embed.set_footer(text="It will stay until someone catches it!")

        try:
            if file:
                msg = await channel.send(file=file, embed=embed)
            else:
                msg = await channel.send(embed=embed)
            if channel.id in self.active_sharks:
                self.active_sharks[channel.id]["message"] = msg
        except discord.Forbidden:
            self.active_sharks.pop(channel.id, None)

    # ── Catch by typing "nom" ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != config.CHANNEL_CATCHING:
            return
        if message.content.strip().lower() != "nom":
            return
        if message.channel.id not in self.active_sharks:
            return

        data = self.active_sharks.pop(message.channel.id)
        shark_name = data["type"]
        user_id = message.author.id

        await self.bot.db.execute(
            """INSERT INTO collection (user_id, shark_type, count) VALUES ($1, $2, 1)
               ON CONFLICT (user_id, shark_type) DO UPDATE SET count = collection.count + 1""",
            user_id, shark_name,
        )

        row = await self.bot.db.fetchrow(
            "SELECT count FROM collection WHERE user_id=$1 AND shark_type=$2",
            user_id, shark_name
        )
        new_count = row["count"] if row else 1

        total_seconds = round(time.time() - data["spawned_at"], 2)
        minutes = int(total_seconds // 60)
        seconds = round(total_seconds % 60, 2)
        time_str = f"{minutes} minutes {seconds} seconds" if minutes > 0 else f"{seconds} seconds"

        await self.bot.db.execute(
            """
            INSERT INTO users (user_id, total_catches, fastest_catch, slowest_catch)
            VALUES ($1, 1, $2, $2)
            ON CONFLICT (user_id) DO UPDATE SET
                total_catches = users.total_catches + 1,
                fastest_catch = CASE
                    WHEN users.fastest_catch IS NULL OR $2 < users.fastest_catch THEN $2
                    ELSE users.fastest_catch
                END,
                slowest_catch = CASE
                    WHEN users.slowest_catch IS NULL OR $2 > users.slowest_catch THEN $2
                    ELSE users.slowest_catch
                END
            """,
            user_id, total_seconds,
        )

        emoji = get_emoji(shark_name, message.guild)
        await message.channel.send(
            f"{message.author.display_name} cought {emoji} {shark_name} Shark!!!!1!\n"
            f"You now have {new_count} sharks of dat type!!!\n"
            f"this fella was cought in {time_str}!!!!"
        )

    # ── /forcespawn (admin only) ──────────────────────────────────────────
    @app_commands.command(name="forcespawn", description="Force a shark to spawn (admin only)")
    @app_commands.describe(shark_type="Which shark type to spawn (leave blank for random)")
    @app_commands.checks.has_permissions(administrator=True)
    async def forcespawn(self, interaction: discord.Interaction, shark_type: str = None):
        if interaction.channel_id in self.active_sharks:
            await interaction.response.send_message("There is already a shark here!", ephemeral=True)
            return

        if shark_type:
            shark_type = shark_type.title()
            if shark_type not in SHARKS:
                shark_list = ", ".join(SHARKS.keys())
                await interaction.response.send_message(
                    f"❌ Unknown shark: **{shark_type}**\nValid types: {shark_list}",
                    ephemeral=True
                )
                return
            await interaction.response.send_message(
                f"Spawning a **{shark_type} Shark**...", ephemeral=True
            )
        else:
            await interaction.response.send_message("Spawning a random shark...", ephemeral=True)

        await self.spawn_shark(interaction.channel, forced_shark=shark_type)

    # ── /setup (admin only) ───────────────────────────────────────────────
    @app_commands.command(name="setup", description="Set this channel as a shark catching zone (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        now = time.time()
        next_spawn = now + random.randint(config.SPAWN_MIN, config.SPAWN_MAX)
        await self.bot.db.execute(
            """INSERT INTO channels (channel_id, guild_id, next_spawn) VALUES ($1, $2, $3)
               ON CONFLICT (channel_id) DO UPDATE SET next_spawn=$3""",
            interaction.channel_id, interaction.guild_id, next_spawn,
        )
        await self.bot.db.execute(
            "INSERT INTO servers (server_id) VALUES ($1) ON CONFLICT DO NOTHING",
            interaction.guild_id,
        )
        embed = discord.Embed(
            title="🦈 Catching Zone Activated!",
            description=(
                f"{interaction.channel.mention} is now a shark catching zone.\n"
                f'Type **"nom"** to catch one when it appears!'
            ),
            color=0x2ecc71,
        )
        await interaction.response.send_message(embed=embed)

    # ── /setspawntime (admin only) ────────────────────────────────────────
    @app_commands.command(name="setspawntime", description="Set how often sharks spawn in seconds (admin only)")
    @app_commands.describe(
        min_seconds="Minimum time between spawns (30–300 seconds)",
        max_seconds="Maximum time between spawns (30–300 seconds)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setspawntime(self, interaction: discord.Interaction, min_seconds: int, max_seconds: int):
        if min_seconds < 30 or max_seconds < 30:
            await interaction.response.send_message("❌ Minimum value is **30 seconds**.", ephemeral=True)
            return
        if min_seconds > 300 or max_seconds > 300:
            await interaction.response.send_message("❌ Maximum value is **300 seconds (5 minutes)**.", ephemeral=True)
            return
        if min_seconds >= max_seconds:
            await interaction.response.send_message("❌ Min must be less than max.", ephemeral=True)
            return

        row = await self.bot.db.fetchrow(
            "SELECT channel_id FROM channels WHERE channel_id=$1", interaction.channel_id
        )
        if not row:
            await interaction.response.send_message("❌ Run `/setup` first.", ephemeral=True)
            return

        now = time.time()
        next_spawn = now + min_seconds
        await self.bot.db.execute(
            "UPDATE channels SET spawn_min=$1, spawn_max=$2, next_spawn=$3 WHERE channel_id=$4",
            min_seconds, max_seconds, next_spawn, interaction.channel_id,
        )

        def fmt(s):
            if s < 60:
                return f"{s}s"
            return f"{s // 60}m {s % 60}s" if s % 60 else f"{s // 60}m"

        embed = discord.Embed(
            title="⏱️ Spawn Time Updated!",
            description=(
                f"Sharks will now spawn every **{fmt(min_seconds)} – {fmt(max_seconds)}**.\n"
                f"First shark arriving in **{fmt(min_seconds)}**!"
            ),
            color=0x2ecc71,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Catching(bot))
