"""DSA Study Buddy - Multi-agent tutor built with Strands Agents SDK.
Orchestrator routes to Tutor, Quiz and Progress specialist agents (agents-as-tools pattern).
"""
import os, json, time, random
import boto3
from strands import Agent, tool
from strands.models import BedrockModel

MODEL_ID = os.getenv("MODEL_ID", "us.amazon.nova-lite-v1:0")
REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE = os.getenv("TABLE_NAME", "dsa-study-progress")

model = BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.3)
ddb = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)

TOPICS = ["arrays", "strings", "linked lists", "stacks", "queues", "trees",
          "graphs", "dynamic programming", "greedy", "binary search", "heaps", "recursion"]

PROBLEMS = {
    "arrays": ["Two Sum (LC 1)", "Best Time to Buy and Sell Stock (LC 121)", "Product of Array Except Self (LC 238)"],
    "strings": ["Valid Anagram (LC 242)", "Longest Substring Without Repeating Characters (LC 3)"],
    "trees": ["Maximum Depth of Binary Tree (LC 104)", "Lowest Common Ancestor of BST (LC 235)"],
    "graphs": ["Number of Islands (LC 200)", "Course Schedule (LC 207)", "Clone Graph (LC 133)"],
    "dynamic programming": ["Climbing Stairs (LC 70)", "Coin Change (LC 322)", "Longest Increasing Subsequence (LC 300)"],
    "binary search": ["Binary Search (LC 704)", "Search in Rotated Sorted Array (LC 33)"],
}

# ---------------- Tools ----------------
@tool
def record_quiz_result(user_id: str, topic: str, correct: bool) -> str:
    """Save a quiz answer result for a user and topic to track progress."""
    key = {"user_id": user_id, "topic": topic.lower()}
    ddb.update_item(
        Key=key,
        UpdateExpression="ADD attempts :one, correct :c SET updated_at = :t",
        ExpressionAttributeValues={":one": 1, ":c": 1 if correct else 0, ":t": int(time.time())},
    )
    return f"Recorded {'correct' if correct else 'incorrect'} answer for {topic}."

@tool
def get_progress(user_id: str) -> str:
    """Get a user's accuracy per DSA topic. Returns JSON list sorted weakest first."""
    from boto3.dynamodb.conditions import Key
    items = ddb.query(KeyConditionExpression=Key("user_id").eq(user_id)).get("Items", [])
    rows = [{"topic": i["topic"], "attempts": int(i["attempts"]),
             "accuracy": round(int(i.get("correct", 0)) / max(int(i["attempts"]), 1) * 100)} for i in items]
    rows.sort(key=lambda r: r["accuracy"])
    return json.dumps(rows) if rows else "No progress yet."

@tool
def recommend_problems(topic: str) -> str:
    """Recommend practice problems for a DSA topic."""
    probs = PROBLEMS.get(topic.lower())
    return ", ".join(probs) if probs else f"Search LeetCode tag '{topic}', start with Easy problems."

# ---------------- Specialist agents ----------------
tutor = Agent(model=model, callback_handler=None, system_prompt=(
    "You are a friendly DSA tutor for Indian engineering students. Explain concepts simply, "
    "use a real-life analogy, give a short Python example and time/space complexity. "
    "If the student writes in Tamil/Thanglish, reply in Thanglish."))

quizzer = Agent(model=model, tools=[record_quiz_result], callback_handler=None, system_prompt=(
    "You are a DSA quiz master. When asked for a quiz, give ONE multiple-choice question (A-D) "
    "on the topic. When the student answers, say if it is right, explain briefly, and call "
    "record_quiz_result with the user_id and topic."))

coach = Agent(model=model, tools=[get_progress, recommend_problems], callback_handler=None, system_prompt=(
    "You are a study coach. Use get_progress to find weak topics (accuracy < 60%) and "
    "recommend_problems for them. Produce a short 3-day study plan."))

@tool
def tutor_agent(question: str) -> str:
    """Explain a DSA concept or doubt."""
    return str(tutor(question))

@tool
def quiz_agent(request: str) -> str:
    """Generate a quiz question or grade an answer. Include user_id and topic in the request."""
    return str(quizzer(request))

@tool
def coach_agent(request: str) -> str:
    """Analyse progress and build a study plan. Include user_id in the request."""
    return str(coach(request))

def build_orchestrator() -> Agent:
    return Agent(model=model, tools=[tutor_agent, quiz_agent, coach_agent], callback_handler=None,
                 system_prompt=(
        "You are DSA Study Buddy, an orchestrator. Route the student's message: concept doubts -> "
        "tutor_agent; 'quiz me' or answers to quizzes -> quiz_agent; progress / plan / what to study "
        "-> coach_agent. Always pass the user_id along. Return the specialist's answer clearly."))

if __name__ == "__main__":
    bot = build_orchestrator()
    uid = "demo-user"
    print("DSA Study Buddy (type 'exit')")
    while (q := input("> ")) != "exit":
        print(bot(f"[user_id={uid}] {q}"))
