import logging
from flask import current_app, jsonify
import json
import requests
import os
import time
from datetime import datetime
from openai import OpenAI
import pathlib
import textwrap
from groq import Groq
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from .env file
api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=api_key)

def store_data(llm_string, file_path='data.json'):
    # Create data structure
    data_to_store = {
        "timestamp": datetime.now().isoformat(),
        "string": llm_string
    }

    # Check if file exists, create it if it doesn't
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)

    # Append new data to the file
    with open(file_path, 'r+') as f:
        data = json.load(f)
        data.append(data_to_store)
        f.seek(0)
        json.dump(data, f, indent=4)


def classify_msg(message):
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": f"Following is a message it can be of \n Type 1 : stating an expense like bought coffee for 400 \n Type 2 : query like how much i spent on ceratin things or in total (example : How much i spent on coffee in january) \n \n Classify the following message into Type 1 or Type 2 \n \n Note : Only return a single number if it is type 1 just return 1 else 2 (This is very important for my career) \n \n \n Message is : '{message}'"}]
    )

    return response.choices[0].message.content.strip()

def generate_response(message):
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": message}]
    )

    return response.choices[0].message.content.strip()

# def get_timestamp(message):
#     prompt = f"""Given a message extract the time period it is talking about like if it says give me amount i spent today so here
#     time period is today's dateT00:00:00, tommorow's dateT00:00:00 \n \n \n message : {message} 
#     \n \n \n Note : just print to timestamps in comma separated format nothing else (it is very important for my career.)
#     \n \n \n output to the query how much i spent this january should be just \n \n
#     2025-01-01T00:00:00, 2025-02-01T00:00:00 \n \n \n
#     DO NOT PRINT ANYTHING ELSE EXCEPT TWO VALUES OF TIMESTAMP SEPARTED BY A COMMA ELSE THE TASK FAILS"""
#     return generate_response(prompt)
    
def generate_expense_string(message):
    prompt = f"""Convert this expense message into a short, structured string format: 'ITEM:AMOUNT'. \n \n \n
    Note : Only print Item: Amount nothig else (it is very important for my career) \n \n \n Message: '{message}'"""
    return generate_response(prompt)  # Your LLM function

def load_json_data(file_path='data.json'):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []

def process_type_2_query(query):
    # Load the JSON data
    json_data = load_json_data()
    
    # Convert the JSON data to a string
    context = json.dumps(json_data, indent=4)
    
    # Prepare the prompt for the LLM
    prompt = f"""Query: {query}\n\nContext:\n{context}\n\n
    Based on the above context, please answer the query. \n\n
    Note : Only print the final answer in concise format (This is very important for my career)"""
    
    # Generate response using the LLM
    response = generate_response(prompt)  # Your existing LLM function
    
    return response


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


# def generate_response(response):
#     # Return text in uppercase
#     return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

def get_context_between_timestamps(timestamp_range, file_path='data.json'):
    # Parse the input timestamps
    start_time, end_time = [datetime.fromisoformat(ts.strip()) for ts in timestamp_range.split(',')]

    # Load the JSON data
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return "No data found."

    # Filter entries between the given timestamps
    filtered_entries = [
        entry for entry in data
        if start_time <= datetime.fromisoformat(entry['timestamp']) <= end_time
    ]

    # Create context string from filtered entries
    if filtered_entries:
        context = json.dumps(filtered_entries, indent=2)
        return context
    else:
        return "No entries found within the specified time range."

def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # TODO: implement custom function here
    response = "Error Occured"
    temp = classify_msg(message_body)


    if temp == "1":
        response = generate_expense_string(message_body)
        store_data(response)

    elif temp == "2":
        # response = get_timestamp(message_body)
        response = process_type_2_query(message_body)
    # # response = generate_response(message_body)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
