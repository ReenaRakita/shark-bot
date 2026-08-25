# config.py
# Loads all settings from .env
# Add new config values here — never hardcode secrets in the bot files

import os
from dotenv import load_dotenv

load_dotenv()

# ── Discord ──────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN")

# ── Database ─────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "shark_bot")
DB_USER = os.getenv("DB_USER", "shark_bot")
DB_PASS = os.getenv("DB_PASS", "")

# ── Leveling ─────────────────────────────────────────────
XP_MIN          = 15    # minimum XP per message
XP_MAX          = 25    # maximum XP per message
XP_COOLDOWN     = 60    # seconds between XP awards

# ── Economy ──────────────────────────────────────────────
DAILY_REWARD     = 1000  # Shark Dollars from /daily
BLACK_MARKET_FEE = 0.05 # 5% fee on black market sales

# ── Breeding ─────────────────────────────────────────────
BREED_BASE_HOURS = 96   # base breeding timer in hours
BREED_MIN_HOURS  = 48   # minimum after upgrades
BLESS_CHANCE     = 0.001 # 0.1% base bless chance

# ── Aquarium ─────────────────────────────────────────────
AQUARIUM_BASE_SLOTS = 3 # starting aquarium slots
HUNGER_INTERVAL     = 24 # hours until shark goes hungry

# ── Spawning ─────────────────────────────────────────────
SPAWN_MIN     = 60      # minimum seconds between spawns
SPAWN_MAX     = 600     # maximum seconds between spawns
SPAWN_TIMEOUT = 300     # seconds before uncaught shark disappears

# ── Channel IDs ───────────────────────────────────────────
CHANNEL_RULES        = 1532459163475640321
CHANNEL_ANNOUNCEMENTS= 1532460364833362151
CHANNEL_GET_ROLES    = 1532460142979715142
CHANNEL_BIRTHDAY     = 1533791361281822740
CHANNEL_HALL_SHAME   = 1532230652609433600
CHANNEL_CHIT_CHAT    = 1531903203954659341
CHANNEL_MEMES        = 1532462037597290516
CHANNEL_SUGGESTIONS  = 1532110335941673010
CHANNEL_HELP         = 1532812103700840689
CHANNEL_CATCHING     = 1535607417696559224
CHANNEL_BOT_COMMANDS = 1535609466660323420
CHANNEL_TOURNAMENT   = 1535609614161285200
CHANNEL_MEOW         = 1531906356406128710
CHANNEL_SLOW_MEOW    = 1532452149232009360
CHANNEL_BARK         = 1532111492206301345
CHANNEL_WORDLE       = 1532465140555976885
CHANNEL_BLOOD_BATH   = 1532710110668001290
CHANNEL_BOT_TESTING  = 1532465361658843176
CHANNEL_MUSIC_UPDATES= 1534960954868109322

# ── Channel Restriction Helper ────────────────────────────────────────────
async def check_channel(interaction, allowed_channel_id):
    """Returns True if the command is used in the correct channel."""
    if interaction.channel_id != allowed_channel_id:
        await interaction.response.send_message(
            f"❌ Use this command in <#{allowed_channel_id}>",
            ephemeral=True
        )
        return False
    return True