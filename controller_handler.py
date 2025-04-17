from typing import Optional
import discord
from discord.ext import commands

class ControllerHandler:
    def __init__(self, bot_control):
        self.bot_control = bot_control

    async def handle_message(self, message: discord.Message) -> Optional[bool]:
        """Handle messages from controllers
        
        Args:
            message (discord.Message): The message to handle
            
        Returns:
            Optional[bool]: True if message was handled, None if not from controller
        """
        if message.author.bot:
            return None

        user_id = str(message.author.id)
        
        # Check if the message is from a controller with control
        if self.bot_control.has_control(user_id):
            # If the message starts with !, it's a command
            if not message.content.startswith('!'):
                # Echo the message directly without any additional text
                await message.channel.send(message.content)
                return True
                
        return None