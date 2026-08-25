# cogs/admin.py
import discord
from discord.ext import commands
from discord import app_commands
from data.sharks import SHARKS


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Auto assign Hatchling role + welcome message on join ──────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Assigns Hatchling role and sends welcome message when someone joins."""

        # ── Assign Hatchling role ─────────────────────────────────────────
        hatchling = discord.utils.get(member.guild.roles, name="Hatchling")
        if hatchling:
            try:
                await member.add_roles(hatchling)
            except discord.Forbidden:
                pass

        # ── Send welcome message ──────────────────────────────────────────
        channel = self.bot.get_channel(1531903203954659341)  # chit-chat
        if not channel:
            return

        embed = discord.Embed(
            title="🦈 A new member swims in!",
            description=(
                f"Welcome to **The Shark Cult**, {member.mention}!\n\n"
                f"🌊 Read the rules in <#1532459163475640321>\n"
                f"🎭 Grab your roles in <#1532460142979715142>\n"
                f"🎣 Catch your first shark in <#1535607417696559224>\n\n"
                f"*The depths welcome you. The sharks are watching.*"
            ),
            color=0x2fd6c8,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{member.guild.member_count}")

        await channel.send(embed=embed)

    # ── /givesd ───────────────────────────────────────────────────────────
    @app_commands.command(name="givesd", description="Give Shark Dollars to a user (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def givesd(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await self.bot.db.execute(
            """INSERT INTO users (user_id, shark_dollars) VALUES ($1, $2)
               ON CONFLICT (user_id) DO UPDATE SET shark_dollars=users.shark_dollars+$2""",
            member.id, amount,
        )
        await interaction.response.send_message(
            f"✅ Gave **{amount:,} Shark Dollars** to {member.mention}", ephemeral=True
        )

    # ── /giveshark ────────────────────────────────────────────────────────
    @app_commands.command(name="giveshark", description="Give a shark to a user (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveshark(self, interaction: discord.Interaction, member: discord.Member, shark: str, amount: int = 1):
        shark = shark.title()
        if shark not in SHARKS:
            await interaction.response.send_message(f"Unknown shark: {shark}", ephemeral=True)
            return
        await self.bot.db.execute(
            """INSERT INTO collection (user_id, shark_type, count) VALUES ($1,$2,$3)
               ON CONFLICT (user_id, shark_type) DO UPDATE SET count=collection.count+$3""",
            member.id, shark, amount,
        )
        await interaction.response.send_message(
            f"✅ Gave **{amount}x {shark} Shark** to {member.mention}", ephemeral=True
        )

    # ── /resetuser ────────────────────────────────────────────────────────
    @app_commands.command(name="resetuser", description="Reset a user's data (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def resetuser(self, interaction: discord.Interaction, member: discord.Member):
        await self.bot.db.execute("DELETE FROM collection WHERE user_id=$1", member.id)
        await self.bot.db.execute("DELETE FROM users WHERE user_id=$1", member.id)
        await self.bot.db.execute(
            "DELETE FROM profiles WHERE user_id=$1 AND guild_id=$2",
            member.id, interaction.guild_id
        )
        await interaction.response.send_message(
            f"✅ Reset all data for {member.mention}", ephemeral=True
        )

# ── Channel Restrictions ──────────────────────────────────────────────────

async def check_channel(interaction, allowed_channel_id):
    """Returns True if the command is being used in the correct channel."""
    if interaction.channel_id != allowed_channel_id:
        await interaction.response.send_message(
            f"❌ Use this command in <#{allowed_channel_id}>",
            ephemeral=True
        )
        return False
    return True

async def setup(bot):
    await bot.add_cog(Admin(bot))