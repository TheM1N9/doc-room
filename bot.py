from pathlib import Path
import random
import re
from typing import List, Tuple, Union
import discord
from discord.ext import commands
from chatbot.chat import personal_parser, update_personal_details, check_diagnosis

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
    get_medical_data,
    update_medical_data,
    clear_medical_data,
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
from discord_bot.bot_control import BotControl
from discord_bot.controller_handler import ControllerHandler

# Global variable to store the state of the bot
global_state = BotState.IDLE
bot_control = BotControl()  # Initialize bot control system


def create_bot(openai_client) -> commands.Bot:
    """Create a Discord Bot

    Returns:
        commands.Bot: The Discord Bot
    """
    global global_state

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
    controller_handler = ControllerHandler(bot_control)

    # Event
    @bot.event
    async def on_ready() -> None:
        """Prints a message when the bot is connected to Discord"""
        global global_state

        if bot.user is None:
            print("log the relevant error")
            return

        print(f"{bot.user.name} has connected to Discord!")
        print(f"Bot ID: {bot.user.id}")

        bot_id = bot.user.id
        global_state = BotState.IDLE

    @bot.command(name="addcontroller", help="Add a new bot controller (Admin only)")
    @commands.has_permissions(administrator=True)
    async def add_controller(ctx, user: discord.User, control_token: str) -> None:
        """Add a new bot controller
        
        Args:
            user (discord.User): The user to add as controller
            control_token (str): The control token for the user
        """
        bot_control.add_controller(str(user.id), control_token)
        await ctx.send(f"Added {user.mention} as a bot controller")

    @bot.command(name="removecontroller", help="Remove a bot controller (Admin only)")
    @commands.has_permissions(administrator=True)
    async def remove_controller(ctx, user: discord.User) -> None:
        """Remove a bot controller
        
        Args:
            user (discord.User): The user to remove as controller
        """
        if bot_control.remove_controller(str(user.id)):
            await ctx.send(f"Removed {user.mention} as a bot controller")
        else:
            await ctx.send(f"{user.mention} is not a controller")

    @bot.command(name="takecontrol", help="Take control of the bot")
    async def take_control(ctx, control_token: str) -> None:
        """Take control of the bot
        
        Args:
            control_token (str): The control token
        """
        user_id = str(ctx.author.id)
        if bot_control.request_control(user_id, control_token):
            # Control granted silently
            return
        else:
            await ctx.send("Invalid control token or you are not authorized")

    @bot.command(name="releasecontrol", help="Release control of the bot")
    async def release_control(ctx) -> None:
        """Release control of the bot"""
        user_id = str(ctx.author.id)
        if bot_control.release_control(user_id):
            await ctx.send(f"{ctx.author.mention} has released control of the bot")
        else:
            await ctx.send("You don't have control of the bot")

    # Event
    @bot.event
    async def on_message(message) -> None:
        """Handles the message sent by the user"""
        global global_state

        user_input = message.content
        user_id = str(message.author.id)

        add_to_chat_history(user_id, user_input)

        if message.author == bot.user:
            return

        if bot.user is None:
            print("log a relevant error")
            return

        # Handle controller messages
        handled = await controller_handler.handle_message(message)
        if handled:
            return

        # Process commands first
        await bot.process_commands(message)

        # When the bot is mentioned in the message
        if bot.user.mentioned_in(message):
            user_input = remove_user_id(user_input)
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
                previous_data = get_user_data(int(user_id))  # Convert to int for compatibility

                if not previous_data:
                    # First time user - use personal_parser
                    data, reply = personal_parser(openai_client, user_input)
                    if data:
                        update_user_data(int(user_id), data)  # Convert to int for compatibility
                else:
                    # Update existing data
                    data, reply = update_personal_details(
                        openai_client, user_input, previous_data, chat_history
                    )
                    if data:
                        update_user_data(int(user_id), data)  # Convert to int for compatibility

                chat_history.append((user_input, reply))
                reply = f"<@{user_id}> " + reply

                await message.channel.send(reply)

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
