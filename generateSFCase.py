
# Corrected Python script: generateSFCase.py
# Key changes:
# 1. Modified Salesforce import to use `simple_salesforce` directly.
#    (Ensure `simple-salesforce` is installed: `pip install simple-salesforce`)
# 2. Moved `import json` to the global scope for proper access.

import os
import random
from dotenv import load_dotenv
from simple_salesforce import Salesforce # MODIFIED: Changed from salesforce_api
import json # MODIFIED: Moved to global scope
from openai import OpenAI
import time

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SALESFORCE_SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
SALESFORCE_INSTANCE_URL = os.getenv("SALESFORCE_INSTANCE_URL") # Used for direct API calls if not using simple-salesforce for everything
SALESFORCE_DOMAIN = None # Set to 'test' for sandboxes if using simple-salesforce login

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-3.5-turbo" # Or your preferred model

# --- HELPER FUNCTIONS ---

def connect_to_salesforce():
    """
    Connects to Salesforce using the simple-salesforce library.
    Uses Username-Password authentication.
    Returns:
        Salesforce: An authenticated Salesforce API client instance or None if connection fails.
    """
    try:
        sf = Salesforce(
            username=SALESFORCE_USERNAME,
            password=SALESFORCE_PASSWORD,
            security_token=SALESFORCE_SECURITY_TOKEN,
            domain=SALESFORCE_DOMAIN, # Use 'test' for sandboxes
            instance_url=SALESFORCE_INSTANCE_URL # Can be useful for specific instances
        )
        print("Successfully connected to Salesforce.")
        return sf
    except Exception as e:
        print(f"Error connecting to Salesforce: {e}")
        return None

def get_salesforce_accounts(sf_client):
    """
    Retrieves accounts from Salesforce.
    Args:
        sf_client (Salesforce): Authenticated Salesforce client.
    Returns:
        list: A list of account dictionaries (e.g., [{'Id': '...', 'Name': '...'}]),
              or an empty list if an error occurs or no accounts are found.
    """
    if not sf_client:
        return []
    try:
        query = "SELECT Id, Name FROM Account LIMIT 200"
        result = sf_client.query_all(query)  # Using query_all for SOQL queries
        accounts = result.get('records', [])
        print(f"Retrieved {len(accounts)} accounts from Salesforce.")
        return accounts
    except Exception as e:
        print(f"Error retrieving Salesforce accounts: {e}")
        return []

def generate_support_email_content(account=None):
    """
    Generates email subject and description using OpenAI API.
    Args:
        account (dict, optional): A dictionary representing the Salesforce account
                                  (e.g., {'Name': 'Account Name'}). Defaults to None.
    Returns:
        dict: A dictionary like {'subject': '...', 'description': '...'} or None on error.
    """
    if not OPENAI_API_KEY:
        print("OpenAI API Key not found in environment variables.")
        return None

    try:
        client = OpenAI()
        
        prompt_content = """
        You are simulating an end user of a healthcare software application who needs to submit a support ticket.
        The user is experiencing an issue and needs help.
        Generate a concise email subject and a detailed email description for this support request.

        The tone should be slightly frustrated but polite.  Every now and then the customers will ask about kangaroos.
        The issue should be plausible for a healthcare software application (e.g., problem with patient records, billing module error, appointment scheduling glitch, report generation failure, login issues, slow performance).
        """

        if account and account.get('Name'):
            prompt_content += f"\nThe user is associated with the account: \"{account['Name']}\". You can subtly mention this if it feels natural, but it's not strictly necessary."
        else:
            prompt_content += "\nThe user is not necessarily tied to a specific pre-identified account."

        prompt_content += """
        Please provide the output in JSON format with two keys: "subject" and "description".
        Example JSON:
        {
          "subject": "Urgent: Unable to access patient charts",
          "description": "Dear Support Team,\\n\\nI've been trying to access patient charts for the past hour and keep getting an error message 'Access Denied - Code 503'. This is critically impacting my workflow as I need to review patient data for upcoming appointments. I have tried clearing my cache and restarting the application, but the issue persists. My user ID is janedoe. Please help resolve this urgently.\\n\\nThanks,\\nJane Doe"
        }
        """

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an AI assistant that generates support ticket content in JSON format."},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.7,
            response_format={"type": "json_object"} # For compatible models
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            content_str = response.choices[0].message.content
            email_data = json.loads(content_str) # 'json' is now globally available
            if 'subject' in email_data and 'description' in email_data:
                print(f"Generated Email Subject: {email_data['subject']}")
                print(f"Generated Email Description: {email_data['description']}")
                return email_data
            else:
                print(f"OpenAI response JSON does not contain subject or description. Raw content: {content_str}")
                return None
        else:
            print(f"OpenAI response does not have the expected structure. Full response: {response}")
            return None

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def create_salesforce_case(sf_client, subject, description, account_id=None):
    """
    Creates a new Case in Salesforce.
    Args:
        sf_client (Salesforce): Authenticated Salesforce client.
        subject (str): The subject of the case.
        description (str): The description of the case.
        account_id (str, optional): The ID of the account to associate with the case. Defaults to None.
    Returns:
        str: The ID of the newly created Case, or None if an error occurs.
    """
    if not sf_client:
        return None

    case_data = {
        'Subject': subject,
        'Description': description,
        'Status': 'New',  # Default status
        'Origin': 'Web'   # Default origin
    }
    if account_id:
        case_data['AccountId'] = account_id

    try:
        result = sf_client.Case.create(case_data)
        if result.get('success'):
            case_id = result.get('id')
            print(f"Successfully created Case in Salesforce. Case ID: {case_id}")
            return case_id
        else:
            print(f"Failed to create Case in Salesforce. Errors: {result.get('errors')}")
            return None
    except Exception as e:
        print(f"Error creating Salesforce Case: {e}")
        return None

# --- MAIN WORKFLOW ---
def main_workflow():
    """
    Main function to execute the process.
    """
    print("Starting support case creation workflow...")

    sf_client = connect_to_salesforce()
    if not sf_client:
        print("Exiting workflow due to Salesforce connection failure.")
        return

    accounts = get_salesforce_accounts(sf_client)
    selected_account = None
    pick_account_randomly = random.random() < 0.7

    if pick_account_randomly and accounts:
        selected_account = random.choice(accounts)
        print(f"Randomly selected account: {selected_account.get('Name')} (ID: {selected_account.get('Id')})")
    elif pick_account_randomly and not accounts:
        print("Wanted to pick an account, but no accounts were available.")
    else:
        print("Randomly decided not to select an account for this case.")

    email_content = generate_support_email_content(selected_account)
    if not email_content:
        print("Failed to generate email content from OpenAI. Exiting workflow.")
        return

    case_id = create_salesforce_case(
        sf_client,
        email_content['subject'],
        email_content['description'],
        selected_account['Id'] if selected_account else None
    )

    if case_id:
        print(f"Workflow completed. Case created with ID: {case_id}")
    else:
        print("Workflow completed, but failed to create the Case in Salesforce.")

if __name__ == "__main__":
    for i in range(10):
        time.sleep(2)
        main_workflow()