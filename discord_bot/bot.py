from pathlib import Path
import random
import re
from typing import List, Tuple, Union
import discord
from discord.ext import commands
from chatbot.chat import personal_parser, update_personal_details

# from langchain_core.messages import AIMessage, HumanMessage
from discord_bot.memory import (
    active_users,
    add_to_chat_history,
    chat_history,
    set_user_active,
    set_user_inactive,
    bot_id,
    get_user_data,
    update_user_data,
    clear_user_data,
)

# from discord_bot.parameters import (
#     CHROMA_COLLECTION_NAME,
#     OUTPUT_COLUMNS,
#     SQL_TABLE_NAME,
#     SQLITE_DB_FILE,
#     VECTORDB_PORT,
#     VECTORDB_HOST,
# )
from discord_bot.state import BotState, empty_active_users, new_user, user_exists

# from expert_system.conversation import Chatbot
# from nlqs.database.postgres import PostgresConnectionConfig
# from nlqs.database.sqlite import SQLiteConnectionConfig
# from nlqs.nlqs import NLQS, ChromaDBConfig, NLQSResult

# Global variable to store the state of the bot
global_state = BotState.IDLE


def create_bot(openai_client) -> commands.Bot:
    """Create a Discord Bot

    Returns:
        commands.Bot: The Discord Bot
    """
    global global_state

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    # Create the default bot behaviors here

    # Event
    @bot.event
    async def on_ready() -> None:
        """Prints a message when the bot is connected to Discord"""
        global global_state

        if bot.user is None:
            print("log the relevant error")
            return

        print(f"{bot.user.name} has connected to Discord!")  # Prints in the terminal
        print(f"Bot ID: {bot.user.id}")

        # Save the bot's ID
        bot_id = bot.user.id

        global_state = BotState.IDLE  # Initial State - Idle

    # Event
    @bot.event
    async def on_message(message) -> None:  # Whenever a msg is sent
        """Handles the message sent by the user

        Args:
            message (_type_): The message sent by the user
        """
        global global_state

        user_input = message.content  # Message from the user
        user_id = message.author.id  # ID of the user

        # Tracks the last 100 messages in chat_history
        add_to_chat_history(user_id, user_input)

        print(f"chat history: {chat_history}")
        print(active_users)

        # To prevent bot from replying to it's own message
        if message.author == bot.user:
            return

        if bot.user is None:
            print("log a relevant error")
            return

        # When the bot is mentioned in the message
        if bot.user.mentioned_in(message):
            user_input = remove_user_id(user_input)
            print(f"User Input: {user_input}")
            if user_id in active_users:
                if "!exit" in user_input:  # To remove conversation
                    await message.channel.send(
                        f"Conversation with the user <@{user_id}> Ended."
                    )
                    set_user_inactive(user_id)  # Removes the user from active_users
                    global_state = empty_active_users(
                        global_state
                    )  # Sets the bot state to Idle if active_users are empty
                else:  # Any other prompt
                    global_state = user_exists()  # Sets the bot state to Engaged
            else:
                # stopping the bot to only ask the users their personal details and adds the user to the active users.
                reply = (
                    f"<@{user_id}> "
                    + "Give us your personal details. Eg: I'm Mani, 21 Male. i'm currently working as a developer at Aegion."
                )
                await message.channel.send(reply)
                set_user_active(
                    user_id
                )  # Adding the user to the current going-on conversations
                global_state = new_user()  # Sets the bot state to Engaged
                return

        # To Check the state of the bot
        if (
            global_state == BotState.ENGAGED
        ):  # If the bot is in Engaged state (user_conversations exist)
            if user_id in active_users:
                # Assume interaction with the user ......
                # Set the typing state on the channel
                await message.channel.typing()

                corrected_chat_history = change_chat_history(chat_history)
                # print(f"corrected_chat_history: {corrected_chat_history}")

                # Get existing user data
                previous_data = get_user_data(user_id)

                if not previous_data:
                    # First time user - use personal_parser
                    data, reply = personal_parser(openai_client, user_input)
                    if data:
                        update_user_data(user_id, data)
                else:
                    # Update existing data
                    data, reply = update_personal_details(
                        openai_client, user_input, previous_data, chat_history
                    )
                    if data:
                        update_user_data(user_id, data)

                chat_history.append((user_input, reply))
                reply = f"<@{user_id}> " + reply

                # reply = f"processing.........."

                await message.channel.send(reply)
        # To process the commands
        await bot.process_commands(message)

    # Commands

    # BYE
    @bot.command(name="bye", help="-Will end the conversation")
    async def bye(ctx) -> None:
        """Ends the conversation with the user

        Args:
            ctx (Unknown): The context of the command
        """
        global global_state
        user_id = ctx.author.id
        replies = [
            f"Goodbye <@{user_id}>! Have a great day!",
            f"Bye <@{user_id}>! Hope to see you soon!",
            f"See you later <@{user_id}>!",
        ]
        reply = random.choice(replies)
        await ctx.send(reply)
        empty_active_users(global_state)

    # STATE
    @bot.command(name="state", help="-Prompts the current state of bot")
    async def state(ctx) -> None:
        """Prompts the current state of the bot

        Args:
            ctx (Unknown): The context of the command
        """
        global global_state

        # Check the state of the bot is it Idle or Engaged and
        # send the message accordingly
        if global_state == BotState.IDLE:
            await ctx.send("Idle")
        else:
            await ctx.send("Engaged")

    return bot


def change_chat_history(
    user_chat_history: List[Tuple[str, str]],
) -> List[str]:
    """Converts a list of tuples representing chat history to a list of HumanMessage and AIMessage objects.

    Args:
        user_chat_history (List[Tuple[str, str]]): A list of tuples where each tuple represents a message in the chat history.
                                                    The first element of the tuple is the sender (either "Human" or "AI")
                                                    and the second element is the message content.

    Returns:
        List[Union[HumanMessage, AIMessage]]: A list of HumanMessage and AIMessage objects representing the chat history.
    """
    corrected_chat_history = []
    for sender, message in user_chat_history:
        if sender is bot_id:
            # Remove user IDs from the message
            message = remove_user_id(message)
            corrected_chat_history.append(message)
        else:
            corrected_chat_history.append(message)

    return corrected_chat_history


def remove_user_id(input_string: str) -> str:
    """Removes user IDs from a string

    Args:
        input_string (str): The input string

    Returns:
        str: The string with user IDs removed
    """

    # Regular expression pattern to match user IDs in the format <@user_id>
    pattern = r"<@\d+>"

    # Replace all occurrences of the pattern with an empty string
    result = re.sub(pattern, "", input_string)

    # Strip any leading or trailing whitespace
    return result.strip()
