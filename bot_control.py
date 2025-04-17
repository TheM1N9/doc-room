from typing import Dict, Optional, List
import discord

class BotControl:
    def __init__(self):
        self.controllers: Dict[str, str] = {}  # user_id -> control_token
        self.active_controller: Optional[str] = None
        self.control_messages: Dict[str, List[str]] = {}  # user_id -> list of messages

    def request_control(self, user_id: str, control_token: str) -> bool:
        """Request control of the bot
        
        Args:
            user_id (str): The Discord user ID
            control_token (str): A unique token for control verification
            
        Returns:
            bool: True if control is granted, False otherwise
        """
        if user_id in self.controllers and self.controllers[user_id] == control_token:
            self.active_controller = user_id
            self.control_messages[user_id] = []
            return True
        return False

    def release_control(self, user_id: str) -> bool:
        """Release control of the bot
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            bool: True if control was released, False otherwise
        """
        if self.active_controller == user_id:
            self.active_controller = None
            return True
        return False

    def add_controller(self, user_id: str, control_token: str) -> None:
        """Add a new controller with their control token
        
        Args:
            user_id (str): The Discord user ID
            control_token (str): A unique token for control verification
        """
        self.controllers[user_id] = control_token

    def remove_controller(self, user_id: str) -> bool:
        """Remove a controller
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            bool: True if controller was removed, False otherwise
        """
        if user_id in self.controllers:
            del self.controllers[user_id]
            if self.active_controller == user_id:
                self.active_controller = None
            return True
        return False

    def is_controller(self, user_id: str) -> bool:
        """Check if a user is a registered controller
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            bool: True if user is a controller, False otherwise
        """
        return user_id in self.controllers

    def has_control(self, user_id: str) -> bool:
        """Check if a user currently has control of the bot
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            bool: True if user has control, False otherwise
        """
        return self.active_controller == user_id

    def add_control_message(self, user_id: str, message: str) -> None:
        """Add a message to be sent by the controller
        
        Args:
            user_id (str): The Discord user ID
            message (str): The message to be sent
        """
        if user_id in self.control_messages:
            self.control_messages[user_id].append(message)

    def get_control_messages(self, user_id: str) -> List[str]:
        """Get all pending messages for a controller
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            List[str]: List of pending messages
        """
        if user_id in self.control_messages:
            messages = self.control_messages[user_id].copy()
            self.control_messages[user_id] = []
            return messages
        return [] 