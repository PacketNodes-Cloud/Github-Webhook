from flask import Flask, request, jsonify
import json
import logging
import requests
import os

app = Flask(__name__)

# Fetch Discord Webhook URL from environment variable
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("Missing DISCORD_WEBHOOK_URL! Set it in Render environment variables.")

# Configure logging
logging.basicConfig(filename="webhook.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def send_to_discord(embed):
    """Send formatted GitHub event as an embed to Discord."""
    data = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers)
    
    if response.status_code == 204:
        logging.info("Sent to Discord successfully!")
    else:
        logging.error(f"Failed to send to Discord: {response.text}")

@app.route("/webhook", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook events and send to Discord."""
    payload = request.json  # Get GitHub event data
    event = request.headers.get("X-GitHub-Event", "ping")  # Event type

    logging.info(f"Received event: {event}")
    logging.info(json.dumps(payload, indent=4))  # Log full event

    embed = {
        "title": f"GitHub Event: {event}",
        "color": 0x00ff00,  # Green color
        "fields": [],
        "footer": {"text": "GitHub → Discord Webhook"}
    }

    # Handle different GitHub events
    if event == "push":
        repo = payload["repository"]["full_name"]
        pusher = payload["pusher"]["name"]
        commit_count = len(payload["commits"])
        commit_messages = "\n".join([f"- {c['message']}" for c in payload["commits"]])

        embed["title"] = f"Push Event - {repo}"
        embed["description"] = f"**{pusher}** pushed {commit_count} commits."
        embed["fields"].append({"name": "Commits", "value": commit_messages[:1024], "inline": False})

    elif event == "pull_request":
        action = payload["action"]
        pr = payload["pull_request"]
        repo = payload["repository"]["full_name"]
        user = pr["user"]["login"]
        title = pr["title"]
        url = pr["html_url"]

        embed["title"] = f"Pull Request {action.capitalize()} - {repo}"
        embed["description"] = f"**{user}** {action} a pull request: [{title}]({url})"

    elif event == "issues":
        action = payload["action"]
        issue = payload["issue"]
        repo = payload["repository"]["full_name"]
        user = issue["user"]["login"]
        title = issue["title"]
        url = issue["html_url"]

        embed["title"] = f"Issue {action.capitalize()} - {repo}"
        embed["description"] = f"**{user}** {action} an issue: [{title}]({url})"

    else:
        embed["description"] = f"Received `{event}` event from GitHub."

    send_to_discord(embed)
    return jsonify({"message": "Webhook received!", "event": event}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
