from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise ValueError("Missing DISCORD_WEBHOOK_URL! Set it in Render environment variables.")

logging.basicConfig(filename="webhook.log", level=logging.INFO, format="%(asctime)s - %(message)s")

EVENT_COLORS = {
    "push": 0x57F287,
    "pull_request": 0xFAA61A,
    "issues": 0xED4245,
    "star": 0xFEE75C,
    "default": 0x5865F2,
}

def send_to_discord(title, description, color="default"):
    embed = {
        "title": title,
        "description": description,
        "color": EVENT_COLORS.get(color, EVENT_COLORS["default"]),
        "footer": {"text": "GitHub → Discord Webhook"},
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, headers={"Content-Type": "application/json"})
    
    if response.status_code != 204:
        logging.error(f"Failed to send to Discord: {response.text}")

@app.route("/webhook", methods=["POST"])
def github_webhook():
    payload = request.json
    event = request.headers.get("X-GitHub-Event", "ping")

    logging.info(f"Received GitHub Event: {event}")

    repo = payload.get("repository", {}).get("full_name", "Unknown Repository")

    if event == "push":
        pusher = payload.get("pusher", {}).get("name", "Unknown User")
        commits = payload.get("commits", [])
        commit_count = len(commits)
        commit_messages = "\n".join([f"• `{c['message']}`" for c in commits]) or "No commit messages."
        send_to_discord(f"📌 Push Event - {repo}", f"**{pusher}** pushed {commit_count} commits:\n{commit_messages}", "push")

    elif event == "pull_request":
        pr = payload.get("pull_request", {})
        user = pr.get("user", {}).get("login", "Unknown User")
        title = pr.get("title", "Untitled PR")
        url = pr.get("html_url", "#")
        action = payload.get("action", "updated")
        send_to_discord(f"🔄 Pull Request {action.capitalize()} - {repo}", f"**[{title}]({url})** by **{user}**", "pull_request")

    elif event == "issues":
        issue = payload.get("issue", {})
        user = issue.get("user", {}).get("login", "Unknown User")
        title = issue.get("title", "Untitled Issue")
        url = issue.get("html_url", "#")
        action = payload.get("action", "updated")
        send_to_discord(f"🐛 Issue {action.capitalize()} - {repo}", f"**[{title}]({url})** reported by **{user}**", "issues")

    elif event == "star":
        user = payload.get("sender", {}).get("login", "Unknown User")
        send_to_discord(f"⭐ Star Event - {repo}", f"**{user}** starred `{repo}`", "star")

    else:
        send_to_discord(f"📡 GitHub Event: {event.capitalize()}", "This event type is currently not customized.", "default")

    return jsonify({"message": "Webhook received!", "event": event}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
