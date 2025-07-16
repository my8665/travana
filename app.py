from flask import Flask, render_template, request, redirect, url_for
import joblib
import os
import requests
from groq import Groq

app = Flask(__name__)

# Get password and other configuration from environment variables
CORRECT_PASSWORD = os.environ.get("TRAVANA_PASSWORD")  # Password stored in environment variable
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # Telegram bot token
DOMAIN_URL = os.environ.get("DOMAIN_URL")  # The base domain URL (e.g., Render.com URL)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Groq API key

# Initialize Groq client (ensure Groq SDK uses the API key if required)
client = Groq(api_key=GROQ_API_KEY)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "MY" and password == CORRECT_PASSWORD:
            return redirect(url_for("main"))
        else:
            return render_template("index.html", error="Incorrect username or password.")
    return render_template("index.html")

@app.route("/main", methods=["GET", "POST"])
def main():
    # Ensure 'q' is available only in POST requests
    q = request.form.get("q") if request.method == "POST" else None
    return render_template("main.html", q=q)

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    domain_url = 'https://travana-83xv.onrender.com'
    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={domain_url}/webhook"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running."
    else:
        status = "Failed to start the telegram bot."
    return(render_template("telegram.html", r=status))

@app.route("/stop_telegram",methods=["GET","POST"])
def stop_telegram():
    domain_url = 'https://travana-83xv.onrender.com'
    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    # Set the webhook URL for the Telegram bot
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot has stop."
    else:
        status = "Failed to stop the telegram bot."
    return(render_template("stop_telegram.html", r=status))

@app.route("/webhook",methods=["GET","POST"])
def webhook():
    # This endpoint will be called by Telegram when a new message is received
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        query = update["message"]["text"]

        # Pass the query to the Groq model
        client = Groq()
        completion_ds = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": q
            }
        ]
    )
        response_message = completion_ds.choices[0].message.content

        # Send the response back to the Telegram chat
        send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(send_message_url, json={
            "chat_id": chat_id,
            "text": response_message
        })
    return('ok', 200)

if __name__ == "__main__":
    app.run()