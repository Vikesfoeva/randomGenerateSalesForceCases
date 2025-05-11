import os
from flask import Flask, request, jsonify, render_template_string
from generateSFCase import main_workflow, connect_to_salesforce, get_salesforce_accounts, generate_support_email_content, create_salesforce_case

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RandomGenSFCase</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        #result { margin-top: 20px; }
        button { padding: 10px 20px; font-size: 16px; }
    </style>
</head>
<body>
    <h1>RandomGenSFCase</h1>
    <p>Click the button below to generate a Salesforce support case using OpenAI.</p>
    <button onclick="generateCase()">Generate Case</button>
    <div id="result"></div>
    <script>
        function generateCase() {
            document.getElementById('result').innerHTML = 'Generating cases, please wait...';
            fetch('/generate-case', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        document.getElementById('result').innerHTML =
                            `<b>All done!</b> ${data.success_count} out of 10 cases created successfully.`;
                    } else if (data.status === 'error') {
                        document.getElementById('result').innerHTML = '<b>Error:</b> ' + (data.message || 'Unknown error');
                    } else {
                        document.getElementById('result').innerHTML = '<b>Unexpected response from server.</b>';
                    }
                })
                .catch(err => {
                    document.getElementById('result').innerHTML =
                        '<b>There was a problem generating cases. Please try again later.</b>';
                });
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-case', methods=['POST'])
def generate_case():
    results = []
    success_count = 0
    for i in range(10):
        try:
            print(f"--- Run {i+1} ---")
            main_workflow()
            results.append({"run": i+1, "status": "success"})
            success_count += 1
        except Exception as e:
            results.append({"run": i+1, "status": "error", "message": str(e)})
    return jsonify({
        "status": "completed",
        "success_count": success_count,
        "results": results
    }), 200

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