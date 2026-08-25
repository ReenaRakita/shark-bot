# 🦈 Shark Bot

The official bot for **The Shark Cult** Discord server. Catch sharks, grow your collection, earn Shark Dollars, and climb the ranks.

---

## Features

**Catching**
- Sharks spawn randomly in the catching zone
- Type `shark` to catch one — first person wins
- 22 shark types with different drop rates

**Economy**
- Earn Shark Dollars by catching and selling sharks
- Claim daily rewards with `/daily`
- Pay other members with `/pay`

**Leveling**
- Earn XP by chatting
- Level up to unlock roles automatically
- Check your rank with `/rank`
- See the top 10 with `/leaderboard`

**Collection**
- View all 22 sharks and their drop rates with `/catalogue`
- Check your collection with `/tank`
- Sell sharks with `/sell`

---

## The 22 Sharks

| Drop Rate | Shark |
|---|---|
| 24.34% | Great White |
| 18.26% | Dog |
| 12.17% | Cat |
| 8.52% | Spinner |
| 6.69% | Nurse |
| 5.60% | Lemon |
| 4.87% | Bull |
| 4.26% | Tiger |
| 3.65% | Hammerhead |
| 3.04% | Swell |
| 2.43% | Whale |
| 1.95% | School |
| 1.22% | Thresher |
| 0.85% | Wobbegong |
| 0.61% | Sixgill |
| 0.49% | Greenland |
| 0.37% | Basking |
| 0.24% | Goblin |
| 0.19% | Ghost |
| 0.12% | Cookiecutter |
| 0.07% | Dwarf |
| 0.05% | Ninja |

---

## Commands

| Command | Description |
|---|---|
| `shark` | Catch the shark that appeared |
| `/catalogue` | View all 22 shark types |
| `/tank` | View your shark collection |
| `/rank` | Check your level and XP |
| `/leaderboard` | Top 10 members by XP |
| `/balance` | Check your Shark Dollars |
| `/daily` | Claim your daily Shark Dollars |
| `/sell` | Sell a shark for Shark Dollars |
| `/pay` | Send Shark Dollars to someone |

## Admin Commands

| Command | Description |
|---|---|
| `/setup` | Register a channel as a catching zone |
| `/setspawntime` | Set spawn timer (30–300 seconds) |
| `/forcespawn` | Force a shark to spawn |
| `/givesd` | Give Shark Dollars to a user |
| `/giveshark` | Give a shark to a user |
| `/resetuser` | Reset a user's data |

---

## Setup

**1. Clone the repo**
```
git clone https://github.com/ReenaBharath/shark-bot.git
cd shark-bot
```

**2. Install dependencies**
```
pip3 install -r requirements.txt
```

**3. Set up environment variables**
```
cp .env.example .env
# Edit .env and fill in your bot token and database password
```

**4. Set up PostgreSQL**
```
sudo -u postgres psql -c "CREATE USER shark_bot WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE shark_bot OWNER shark_bot;"
psql -U shark_bot -d shark_bot -f schema.sql
```

**5. Run the bot**
```
python3 bot.py
```

**6. In Discord, run `/setup` in your catching channel**

---

## Project Structure

```
shark-bot/
├── bot.py              — Entry point
├── config.py           — Config and constants
├── schema.sql          — Database schema
├── requirements.txt
├── data/
│   └── sharks.py       — The 22 shark types
├── cogs/
│   ├── catching.py     — Spawn and catch mechanic
│   ├── collection.py   — /catalogue, /tank
│   ├── economy.py      — Shark Dollars, /daily, /sell, /pay
│   ├── leveling.py     — XP, /rank, /leaderboard
│   ├── aquarium.py     — Phase 2
│   ├── breeding.py     — Phase 2
│   └── admin.py        — Admin tools, welcome message
└── assets/
    └── images/
        └── sharks/     — 22 shark images
```

---

## Contributing

1. Create a branch: `git checkout -b your-feature`
2. Make your changes
3. Push: `git push origin your-feature`
4. Open a pull request on GitHub

---

*Built for The Shark Club 🦈*