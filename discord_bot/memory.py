from typing import List, Tuple

chat_history: List[Tuple[str, str]] = []  # Stores the tuple of  (user_id, message)
active_users: List[str] = []  # Stores the user_id of active users
bot_id: str = "Replace"  # Bot ID

CHAT_HISTORY_LIMIT = 100

# Dictionary to store user personal data
user_data = {}


def get_user_chat_history(user_id: str) -> List[str]:
    """Get the chat history of a user

    Args:
        user_id (str): User ID

    Returns:
        List[str]: List of messages
    """
    return [msg for uid, msg in chat_history if uid == user_id]


def add_to_chat_history(user_id: str, message: str) -> None:
    """Add a message to the chat history

    Args:
        user_id (str): User ID
        message (str): Message
    """
    if len(chat_history) >= CHAT_HISTORY_LIMIT:
        chat_history.pop(0)
    chat_history.append((user_id, message))


def set_user_active(user_id: str) -> None:
    """Set the user as active

    Args:
        user_id (str): User ID
    """
    if user_id not in active_users:
        active_users.append(user_id)


def set_user_inactive(user_id: str) -> None:
    """Set the user as inactive

    Args:
        user_id (str): User ID
    """
    if user_id in active_users:
        active_users.remove(user_id)


def get_user_data(user_id: int) -> dict:
    """Get user's personal data.

    Args:
        user_id: Discord user ID

    Returns:
        Dictionary containing user's personal data
    """
    return user_data.get(user_id, {})


def update_user_data(user_id: int, data: dict) -> None:
    """Update user's personal data.

    Args:
        user_id: Discord user ID
        data: Dictionary containing updated user data
    """
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id].update(data)


def clear_user_data(user_id: int) -> None:
    """Clear user's personal data.

    Args:
        user_id: Discord user ID
    """
    if user_id in user_data:
        del user_data[user_id]
