from flask import Flask, render_template, request, jsonify
import requests
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# The path where wordlist files will be saved temporarily
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check subdomain URLs
def check_subdomain(subdomain, domain):
    subdomain_urls = [
        f"http://{subdomain}.{domain}",
        f"https://{subdomain}.{domain}"
    ]
    
    for subdomain_url in subdomain_urls:
        try:
            response = requests.get(subdomain_url, timeout=3)
            if response.status_code == 200:
                return subdomain_url
        except requests.RequestException:
            continue
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enumerate', methods=['POST'])
def enumerate_subdomains():
    domain = request.form['domain']
    wordlist_file = request.files['wordlist']

    # Save the wordlist temporarily
    wordlist_path = os.path.join(app.config['UPLOAD_FOLDER'], wordlist_file.filename)
    wordlist_file.save(wordlist_path)

    subdomains = []
    
    # Open the wordlist and create a thread pool to handle requests concurrently
    with open(wordlist_path, 'r') as f:
        subdomain_list = [line.strip() for line in f]
    
    # Use ThreadPoolExecutor for concurrency
    with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust max_workers as needed
        results = executor.map(lambda subdomain: check_subdomain(subdomain, domain), subdomain_list)
        
        # Collect the valid subdomains
        for result in results:
            if result:
                subdomains.append(result)

    # Clean up the uploaded file
    os.remove(wordlist_path)

    return render_template('result.html', subdomains=subdomains, domain=domain)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
