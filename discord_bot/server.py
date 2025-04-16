from bot import create_bot

from parameters import DISCORD_TOKEN

print(f"discord token: {DISCORD_TOKEN}")


def run_server():
    bot = create_bot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_server()
