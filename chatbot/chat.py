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
                reply = """Thank you for providing all your personal details! 
                Now, I'll help you with your medical concerns. Let's start with a detailed assessment of your symptoms.
                Please tell me:
                1. What is your main symptom or concern?
                2. When did it first start?
                3. How severe is it on a scale of 1-10?
                4. Is it constant or does it come and go?
                5. Have you noticed any triggers that make it worse?
                Please provide as much detail as possible about your symptoms.
                """
            return data, reply
        except json.JSONDecodeError as e:
            return {}, f"Error: {e}"
    return {}, response


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
                reply = """Thank you for providing all your personal details! 
                Now, I'll help you with your medical concerns. Let's start with a detailed assessment of your symptoms.
                Please tell me:
                1. What is your main symptom or concern?
                2. When did it first start?
                3. How severe is it on a scale of 1-10?
                4. Is it constant or does it come and go?
                5. Have you noticed any triggers that make it worse?
                Please provide as much detail as possible about your symptoms.
                """

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
                    "content": f"""You are a thorough medical assistant conducting a detailed patient interview. 
                    Your task is to systematically gather information and prepare a detailed medical report for the doctor.
                    
                    Patient Information: {json.dumps(user_data)}
                    Chat history: {context}
                    
                    Follow this structured approach:
                    1. First, identify and confirm all reported symptoms
                    2. For each symptom, ask about:
                       - Onset (when it started)
                       - Duration (how long it lasts)
                       - Frequency (how often it occurs)
                       - Severity (on a scale of 1-10)
                       - Triggers (what makes it worse)
                       - Alleviating factors (what makes it better)
                    3. Ask about associated symptoms
                    4. Inquire about medical history, medications, and allergies
                    5. Consider lifestyle factors and recent changes
                    6. Specifically ask about family history related to current symptoms
                    
                    Return a JSON response with fields:
                    1. diagnose_complete (yes/no)
                    2. symptoms (detailed list of identified symptoms with their characteristics)
                    3. possible_diagnoses (list of potential diagnoses in order of likelihood)
                    4. confidence_level (percentage for each diagnosis)
                    5. next_question (specific question to narrow down the diagnosis)
                    6. red_flags (any concerning symptoms that need immediate attention)
                    7. can_diagnose (yes/no - whether enough information is available for a diagnosis)
                    8. doctor_summary (detailed summary for the doctor)
                    9. family_history_related (yes/no - whether there is family history related to current symptoms)
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
