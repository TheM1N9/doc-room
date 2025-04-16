import os
from dotenv import load_dotenv
from discord_bot.bot import create_bot

# Load environment variables from .env file
load_dotenv()

# Get the Discord token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("No Discord token found. Please set DISCORD_TOKEN in your .env file")

# Create and run the bot
bot = create_bot()
bot.run(DISCORD_TOKEN)
