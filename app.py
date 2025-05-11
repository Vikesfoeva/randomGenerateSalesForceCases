import os
from flask import Flask, request, jsonify
from generateSFCase import main_workflow, connect_to_salesforce, get_salesforce_accounts, generate_support_email_content, create_salesforce_case

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-case', methods=['POST'])
def generate_case():
    try:
        # Run the main workflow
        main_workflow()
        return jsonify({"status": "success", "message": "Case generated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/accounts', methods=['GET'])
def list_accounts():
    try:
        sf_client = connect_to_salesforce()
        if not sf_client:
            return jsonify({"status": "error", "message": "Failed to connect to Salesforce"}), 500
        
        accounts = get_salesforce_accounts(sf_client)
        return jsonify({"status": "success", "accounts": accounts}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 