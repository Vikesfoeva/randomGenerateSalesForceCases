# RandomGenSFCase

A Python application that generates random support cases in Salesforce using OpenAI's GPT model.

## Features

- Connects to Salesforce using simple-salesforce
- Generates realistic support case content using OpenAI's GPT model
- Creates cases in Salesforce with generated content
- Optionally associates cases with random Salesforce accounts

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   SALESFORCE_USERNAME=your_username
   SALESFORCE_PASSWORD=your_password
   SALESFORCE_SECURITY_TOKEN=your_security_token
   SALESFORCE_INSTANCE_URL=your_instance_url
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

Run the main script:
```bash
python3 generateSFCase.py
```

## Requirements

- Python 3.9+
- simple-salesforce
- openai
- python-dotenv

## License

MIT 