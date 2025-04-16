import os
from typing import Dict, Tuple, List
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import re
from typing import Dict, Tuple

load_dotenv()


# AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_API_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
# OPENAI_API_VERSION = os.getenv("os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")")
# CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

# if not all([AZURE_API_KEY, AZURE_API_ENDPOINT, AZURE_DEPLOYMENT_NAME]):
#     print("⚠️ Missing Azure OpenAI credentials in .env file.")
# else:


def hello(client) -> str:

    response = client.chat.completions.create(
        model="gpt-4o",  # model = "deployment_name".
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Who is the first president of India?",
            },
        ],
    )

    print(response.choices[0].message.content)

    return response.choices[0].message.content


def personal_parser(client, user_message: str) -> Tuple[Dict[str, str], str]:
    response = (
        client.chat.completions.create(
            model="gpt-4o",  # model = "deployment_name".
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Your task is to parse the given user response into a json format with the fields 1. Name, 2. Age, 3. Mobile, 4. Gender, 5. Address, 6. Occupation and 7. Family History. If you didn't find any of them in the users prompt leave those feilds empty.",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )
        .choices[0]
        .message.content
    )

    print(response)

    match = re.search(r"```json(.*?)```", response, re.DOTALL)
    if match:
        json_response = match.group(1)
        try:
            data = json.loads(json_response)
            missing_fields = [field for field, value in data.items() if not value]

            if data is None:
                reply = "I couldn't parse your details. Please try again with the format: I'm [Name], [Age] [Gender]. I'm currently working as [Occupation] at [Company]."
            elif missing_fields:
                reply = f"Please provide your {' and '.join(missing_fields)}."
            else:
                reply = (
                    "Thank you for providing your details! How can I help you today?"
                )
            return data, reply
        except json.JSONDecodeError as e:
            return {}, f"Error: {e}"
    return {}, "I don't know this error, check for yourself."


def update_personal_details(
    client,
    user_message: str,
    previous_data: Dict[str, str],
    chat_history: List[Tuple[str, str]],
) -> Tuple[Dict[str, str], str]:
    """Update user's personal details with new information from the message.

    Args:
        client: OpenAI client
        user_message: New message from user
        previous_data: Previously collected user data
        chat_history: List of previous conversation messages

    Returns:
        Tuple containing updated data and response message
    """
    # Format chat history for context
    context = "\n".join([f"{role}: {msg}" for role, msg in chat_history])

    print(f"chat context: {context}")

    response = (
        client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a helpful assistant. Your task is to update the user's personal details.
                    Previous data: {json.dumps(previous_data)}
                    Chat history: {context}
                    Update the following fields if new information is provided: Name, Age, Mobile, Gender, Address, Occupation, Family History.
                    Return only the updated fields in JSON format.""",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )
        .choices[0]
        .message.content
    )

    try:
        # Extract JSON from response
        match = re.search(r"```json(.*?)```", response, re.DOTALL)
        if match:
            new_data = json.loads(match.group(1))
            # Merge new data with previous data
            updated_data = {**previous_data, **new_data}

            # Check for missing fields
            missing_fields = [
                field for field, value in updated_data.items() if not value
            ]

            if missing_fields:
                reply = f"Please provide your {' and '.join(missing_fields)}."
            else:
                reply = "Thank you for providing all your details! How can I help you today?"

            return updated_data, reply
    except (json.JSONDecodeError, AttributeError) as e:
        return previous_data, f"Error parsing response: {str(e)}"

    return previous_data, "I couldn't understand your response. Please try again."
