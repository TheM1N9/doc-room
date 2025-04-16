import os
from dotenv import load_dotenv
from discord_bot.bot import create_bot
from openai import AzureOpenAI
from chatbot.chat import hello

# Load environment variables from .env file
load_dotenv()

# Get the Discord token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

if not DISCORD_TOKEN:
    raise ValueError(
        "No Discord token found. Please set DISCORD_TOKEN in your .env file"
    )

if not all([AZURE_API_KEY, AZURE_API_ENDPOINT]):
    print("⚠️ Missing Azure OpenAI credentials in .env file.")
    raise ValueError("No Azure OpenAI credentials in .env file.")

openai_client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_API_ENDPOINT,
)

# Create and run the bot
bot = create_bot(openai_client)
bot.run(DISCORD_TOKEN)


# response = hello(client)
