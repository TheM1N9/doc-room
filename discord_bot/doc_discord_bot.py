import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "Enter your discord token")

# Set up intents once
intents = discord.Intents.all()
intents.message_content = True  # Needed to read message content
intents.guilds = True
intents.messages = True

# Create bot with command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Queue to keep track of which channel to reply in
pending_channels = asyncio.Queue()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Start background task to read terminal input
    asyncio.create_task(read_from_terminal())


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Avoid responding to itself

    if bot.user in message.mentions:
        print(f"Bot was pinged in #{message.channel} by {message.author}")
        await pending_channels.put(message.channel)

    await bot.process_commands(message)  # Important for handling commands


async def read_from_terminal():
    while True:
        channel = await pending_channels.get()
        user_input = await asyncio.get_event_loop().run_in_executor(
            None, input, "Reply to mention: "
        )

        if user_input.strip().lower() == "exit":
            print("Shutting down bot...")
            await bot.close()
            break

        if channel:
            await channel.send(user_input)


# Start the bot
bot.run(TOKEN)
