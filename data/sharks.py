# data/sharks.py
# The 22 shark types — single source of truth
# emoji_name matches the custom Discord emoji name you uploaded

SHARKS = {
    "Great White": {"weight": 2434, "tier": "Common",    "emoji": "🦈", "emoji_name": "great_white",  "description": "The classic. Iconic. Still scary."},
    "Dog":         {"weight": 1826, "tier": "Common",    "emoji": "🐕", "emoji_name": "dog",          "description": "A dogfish shark. More bark than bite."},
    "Cat":         {"weight": 1217, "tier": "Common",    "emoji": "🐱", "emoji_name": "cat",          "description": "A catshark. The cult respects its roots."},
    "Spinner":     {"weight": 852,  "tier": "Uncommon",  "emoji": "🌀", "emoji_name": "spinner",      "description": "Leaps and spins out of the water. Showing off."},
    "Nurse":       {"weight": 669,  "tier": "Uncommon",  "emoji": "💉", "emoji_name": "nurse",        "description": "Gentle bottom-dweller. Don't step on it though."},
    "Lemon":       {"weight": 560,  "tier": "Uncommon",  "emoji": "🍋", "emoji_name": "lemon",        "description": "Yellow-ish. Lives in shallow warm waters."},
    "Bull":        {"weight": 487,  "tier": "Uncommon",  "emoji": "🐂", "emoji_name": "bull",         "description": "Aggressive. Freshwater tolerant. Do not mess with."},
    "Tiger":       {"weight": 426,  "tier": "Rare",      "emoji": "🐯", "emoji_name": "tiger",        "description": "Striped. Apex. Will eat literally anything."},
    "Hammerhead":  {"weight": 365,  "tier": "Rare",      "emoji": "🔨", "emoji_name": "hammerhead",   "description": "360 vision. Weird head. Incredible shark."},
    "Swell":       {"weight": 304,  "tier": "Rare",      "emoji": "🌊", "emoji_name": "swell",        "description": "Puffs up when threatened. Dramatic."},
    "Whale":       {"weight": 243,  "tier": "Rare",      "emoji": "🐋", "emoji_name": "whale",        "description": "Biggest fish in the sea. Gentle giant."},
    "School":      {"weight": 195,  "tier": "Rare",      "emoji": "🏫", "emoji_name": "school",       "description": "They travel in groups. You only caught one though."},
    "Thresher":    {"weight": 122,  "tier": "Epic",      "emoji": "⚡", "emoji_name": "thresher",     "description": "Uses its enormous tail to stun prey. Lethal elegance."},
    "Wobbegong":   {"weight": 85,   "tier": "Epic",      "emoji": "🪸", "emoji_name": "wobbegong",    "description": "Carpet shark. Master of disguise. Was it always there?"},
    "Sixgill":     {"weight": 61,   "tier": "Epic",      "emoji": "6️⃣", "emoji_name": "sixgill",      "description": "Ancient species. Six gills instead of five. Veteran."},
    "Greenland":   {"weight": 49,   "tier": "Epic",      "emoji": "🧊", "emoji_name": "greenland",    "description": "Lives under Arctic ice. Moves slowly. Lives 400+ years."},
    "Basking":     {"weight": 37,   "tier": "Legendary", "emoji": "🌅", "emoji_name": "basking",      "description": "Filters plankton with its massive mouth. Peaceful legend."},
    "Goblin":      {"weight": 24,   "tier": "Legendary", "emoji": "👺", "emoji_name": "goblin",       "description": "Deep sea nightmare with a protruding snout. Rare sighting."},
    "Ghost":       {"weight": 19,   "tier": "Legendary", "emoji": "👻", "emoji_name": "ghost",        "description": "Almost transparent. Haunts the deep. Are you sure you caught it?"},
    "Cookiecutter":{"weight": 12,   "tier": "Mythic",    "emoji": "🍪", "emoji_name": "cookiecutter", "description": "Takes perfect circular bites out of whales. Terrifying."},
    "Dwarf":       {"weight": 7,    "tier": "Mythic",    "emoji": "🔬", "emoji_name": "dwarf",        "description": "Smallest shark known to exist. Enormous power in tiny form."},
    "Ninja":       {"weight": 5,    "tier": "Mythic",    "emoji": "🥷", "emoji_name": "ninja",        "description": "The Ninja Lanternshark. So rare it's almost a myth."},
}

SHARK_NAMES   = list(SHARKS.keys())
SHARK_WEIGHTS = [SHARKS[name]["weight"] for name in SHARK_NAMES]

TIER_COLOURS = {
    "Common":    0x95a5a6,
    "Uncommon":  0x2ecc71,
    "Rare":      0x3498db,
    "Epic":      0x9b59b6,
    "Legendary": 0xf39c12,
    "Mythic":    0xe74c3c,
}

# Sell values per tier
SELL_VALUES = {
    "Common": 10, "Uncommon": 25, "Rare": 75,
    "Epic": 200, "Legendary": 600, "Mythic": 2000,
}

def get_tier_colour(shark_name: str) -> int:
    tier = SHARKS[shark_name]["tier"]
    return TIER_COLOURS.get(tier, 0xffffff)

def get_sell_value(shark_name: str) -> int:
    tier = SHARKS[shark_name]["tier"]
    return SELL_VALUES[tier]

def get_emoji(shark_name: str, guild=None) -> str:
    """Returns custom server emoji if available, falls back to default emoji."""
    shark = SHARKS[shark_name]
    if guild:
        import discord
        custom = discord.utils.get(guild.emojis, name=shark["emoji_name"])
        if custom:
            return str(custom)
    return shark["emoji"]
