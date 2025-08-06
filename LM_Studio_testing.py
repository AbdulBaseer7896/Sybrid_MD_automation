import requests

# Set your prompt
prompt = "Is the sky blue?"

# Define the endpoint
url = "http://localhost:1234/v1/chat/completions"

# Define the payload
payload = {
    # "model": "google/gemma-3-12b",
    "model": "google/gemma-3-1b",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7
}

# Send the request
response = requests.post(url, json=payload)

# Handle and print the response
if response.status_code == 200:
    reply = response.json()["choices"][0]["message"]["content"]
    print("AI:", reply)
else:
    print("Error:", response.status_code, response.text)
