from typing import List, Dict, Tuple, Optional
from openai import AzureOpenAI
import re

class MedicalDiagnosis:
    def __init__(self, openai_client: AzureOpenAI):
        self.openai_client = openai_client
        self.symptoms: List[str] = []
        self.patient_info: Dict[str, str] = {}
        self.diagnosis_history: List[Dict] = []
        self.current_question: Optional[str] = None
        self.required_info: Dict[str, bool] = {
            'age': False,
            'gender': False,
            'chief_complaint': False,
            'duration': False,
            'severity': False,
            'associated_symptoms': False,
            'medical_history': False,
            'medications': False,
            'allergies': False
        }
        self.personal_details_complete = False

    def add_symptom(self, symptom: str) -> None:
        """Add a symptom to the list of symptoms

        Args:
            symptom (str): The symptom to add
        """
        self.symptoms.append(symptom)

    def add_patient_info(self, key: str, value: str) -> None:
        """Add patient information

        Args:
            key (str): The type of information (e.g., age, gender)
            value (str): The value of the information
        """
        self.patient_info[key] = value

    def get_next_question(self) -> str:
        """Generate the next question based on missing information"""
        if not self.required_info['age'] or not self.required_info['gender']:
            return "Please provide your age and gender (e.g., 'I am 25 years old male')"
        
        if not self.personal_details_complete:
            return "Now, let's discuss your medical concerns. What is your main concern or chief complaint?"
        
        if not self.required_info['chief_complaint']:
            return "What is your main concern or chief complaint?"
        
        if not self.required_info['duration']:
            return "How long have you been experiencing these symptoms?"
        
        if not self.required_info['severity']:
            return "On a scale of 1-10, how severe are your symptoms?"
        
        if not self.required_info['associated_symptoms']:
            return "Are you experiencing any other symptoms along with your main complaint?"
        
        if not self.required_info['medical_history']:
            return "Do you have any pre-existing medical conditions?"
        
        if not self.required_info['medications']:
            return "Are you currently taking any medications?"
        
        if not self.required_info['allergies']:
            return "Do you have any known allergies?"
        
        return None

    def process_answer(self, answer: str) -> Tuple[str, bool]:
        """Process the patient's answer and determine next steps
        
        Returns:
            Tuple[str, bool]: (Next question or response, Whether diagnosis is ready)
        """
        # Process age and gender if not yet collected
        if not self.required_info['age'] or not self.required_info['gender']:
            age_match = re.search(r'(\d+)\s*(?:years?|yrs?|yo)', answer.lower())
            gender_match = re.search(r'(male|female|m|f)', answer.lower())
            
            if age_match and gender_match:
                self.add_patient_info('age', age_match.group(1))
                self.add_patient_info('gender', gender_match.group(1))
                self.required_info['age'] = True
                self.required_info['gender'] = True
                self.personal_details_complete = True
                return self.get_next_question(), False
            else:
                return "Please provide both age and gender in the format: 'I am 25 years old male'", False

        # Process other information based on current question
        elif not self.required_info['chief_complaint']:
            self.add_symptom(f"Chief complaint: {answer}")
            self.required_info['chief_complaint'] = True
        
        elif not self.required_info['duration']:
            self.add_symptom(f"Duration: {answer}")
            self.required_info['duration'] = True
        
        elif not self.required_info['severity']:
            self.add_symptom(f"Severity: {answer}")
            self.required_info['severity'] = True
        
        elif not self.required_info['associated_symptoms']:
            self.add_symptom(f"Associated symptoms: {answer}")
            self.required_info['associated_symptoms'] = True
        
        elif not self.required_info['medical_history']:
            self.add_patient_info('medical_history', answer)
            self.required_info['medical_history'] = True
        
        elif not self.required_info['medications']:
            self.add_patient_info('medications', answer)
            self.required_info['medications'] = True
        
        elif not self.required_info['allergies']:
            self.add_patient_info('allergies', answer)
            self.required_info['allergies'] = True

        # Check if all information is collected
        if all(self.required_info.values()):
            return "Thank you for providing all the information. The doctor will review your case shortly.", True
        
        return self.get_next_question(), False

    def generate_differential_diagnosis(self) -> Tuple[List[str], str]:
        """Generate a differential diagnosis based on symptoms

        Returns:
            Tuple[List[str], str]: List of possible diagnoses and a summary
        """
        prompt = f"""
        Based on the following patient information and symptoms, provide a detailed medical analysis:

        Patient Information:
        {self.patient_info}

        Symptoms and History:
        {', '.join(self.symptoms)}

        Please provide a professional medical analysis including:
        1. Differential diagnosis in order of likelihood
        2. Supporting evidence for each potential diagnosis
        3. Recommended diagnostic tests
        4. Initial treatment recommendations
        5. Red flags or concerning features
        6. Follow-up recommendations
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",  # or your specific deployment name
            messages=[
                {"role": "system", "content": "You are a medical expert providing detailed differential diagnoses for doctors."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        diagnosis_text = response.choices[0].message.content
        diagnoses = diagnosis_text.split('\n\n')

        # Store the diagnosis in history
        self.diagnosis_history.append({
            "symptoms": self.symptoms.copy(),
            "patient_info": self.patient_info.copy(),
            "diagnosis": diagnosis_text
        })

        return diagnoses, diagnosis_text

    def clear_session(self) -> None:
        """Clear the current session data"""
        self.symptoms = []
        self.patient_info = {}
        self.diagnosis_history = []
        self.current_question = None
        self.personal_details_complete = False
        self.required_info = {
            'age': False,
            'gender': False,
            'chief_complaint': False,
            'duration': False,
            'severity': False,
            'associated_symptoms': False,
            'medical_history': False,
            'medications': False,
            'allergies': False
        } 