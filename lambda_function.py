import json
from agent import build_orchestrator

# Simple in-memory sessions (warm Lambda). Conversation history per user.
SESSIONS = {}
CORS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS"}

def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS, "body": ""}
    try:
        body = json.loads(event.get("body") or "{}")
        uid = body.get("user_id", "anon")
        msg = body.get("message", "").strip()
        if not msg:
            return {"statusCode": 400, "headers": CORS, "body": json.dumps({"error": "message required"})}
        bot = SESSIONS.setdefault(uid, build_orchestrator())
        reply = str(bot(f"[user_id={uid}] {msg}"))
        return {"statusCode": 200, "headers": CORS, "body": json.dumps({"reply": reply})}
    except Exception as e:
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": str(e)})}
