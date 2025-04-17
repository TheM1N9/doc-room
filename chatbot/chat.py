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

    print("update personal response: {response}")

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
                reply = "Thank you for providing all your details! How can I help you today? Provide me all the current problems and issues your are facing."

            return updated_data, reply
    except (json.JSONDecodeError, AttributeError) as e:
        return previous_data, f"Error parsing response: {str(e)}"

    return previous_data, "I couldn't understand your response. Please try again."


def check_diagnosis(
    client,
    user_message: str,
    chat_history: List[Tuple[str, str]],
    user_data: Dict[str, str],
) -> Tuple[Dict[str, str], str]:
    """Check and diagnose medical symptoms based on user's input.

    Args:
        client: OpenAI client
        user_message: User's message about their symptoms
        chat_history: List of previous conversation messages
        user_data: User's personal information

    Returns:
        Tuple containing diagnosis data and response message
    """
    context = "\n".join([f"{role}: {msg}" for role, msg in chat_history])

    response = (
        client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a helpful Medical assistant. Your task is to analyze the user's answers and diagnose what disease or issue the user is facing.
                    Patient Information: {json.dumps(user_data)}
                    Chat history: {context}
                    
                    Return a JSON response with fields:
                    1. diagnose_complete (yes/no)
                    2. symptoms (list of identified symptoms)
                    3. diagnosed_with (diagnosis if complete, empty if not)
                    4. next_question (question to ask if diagnosis is not complete)
                    """,
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
        match = re.search(r"```json(.*?)```", response, re.DOTALL)
        if match:
            medical_data = json.loads(match.group(1))

            if medical_data.get("diagnose_complete", "").lower() == "no":
                return medical_data, medical_data.get(
                    "next_question",
                    "Could you please describe your symptoms in more detail?",
                )
            else:
                return (
                    medical_data,
                    f"Based on your symptoms, you may be experiencing: {medical_data.get('diagnosed_with', '')}. Would you like to know more about this condition?",
                )
    except (json.JSONDecodeError, AttributeError) as e:
        return {}, f"Error parsing response: {str(e)}"

    return (
        {},
        "I couldn't understand your symptoms. Could you please describe them again?",
    )


# def generate_differential_diagnosis() -> Tuple[List[str], str]:
#     """Generate a differential diagnosis based on symptoms

#     Returns:
#         Tuple[List[str], str]: List of possible diagnoses and a summary
#     """
#     prompt = f"""
#     Based on the following patient information and symptoms, provide a detailed medical analysis:

#     Patient Information:
#     {patient_info}

#     Symptoms and History:
#     {', '.join(symptoms)}

#     Please provide a professional medical analysis including:
#     1. Differential diagnosis in order of likelihood
#     2. Supporting evidence for each potential diagnosis
#     3. Recommended diagnostic tests
#     4. Initial treatment recommendations
#     5. Red flags or concerning features
#     6. Follow-up recommendations
#     """

#     response = openai_client.chat.completions.create(
#         model="gpt-4o",  # or your specific deployment name
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a medical expert providing detailed differential diagnoses for doctors.",
#             },
#             {"role": "user", "content": prompt},
#         ],
#         temperature=0.7,
#         max_tokens=2000,
#     )

#     diagnosis_text = response.choices[0].message.content
#     if not diagnosis_text:
#         raise Exception(
#             "OpenAI has an issue, check by your self, I'm writing this on high!!"
#         )
#     diagnoses = diagnosis_text.split("\n\n")

#     # Store the diagnosis in history
#     diagnosis_history.append(
#         {
#             "symptoms": symptoms.copy(),
#             "patient_info": patient_info.copy(),
#             "diagnosis": diagnosis_text,
#         }
#     )

#     return diagnoses, diagnosis_text
