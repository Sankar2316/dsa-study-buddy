# 🧠 DSA Study Buddy: Multi-Agent AI Tutor (Strands Agents SDK)

**Track:** Education | **Hackathon:** Strands SDK: Workshop to Ship

## Problem
Many students in Tier-2/3 colleges in India don't get a personal mentor for Data Structures & Algorithms. Their prep goes unguided and they don't know which topics they're weak in.

## Solution
DSA Study Buddy is a **multi-agent system** built with the **Strands Agents SDK**:

| Agent | Role | Tools |
|---|---|---|
| Orchestrator | Sends each student message to the right specialist | tutor_agent, quiz_agent, coach_agent |
| Tutor | Explains concepts with analogies, Python code and complexity. Supports Thanglish | — |
| Quiz Master | Asks MCQs, grades answers, saves results | record_quiz_result |
| Coach | Finds weak topics, recommends problems, writes a 3-day plan | get_progress, recommend_problems |

## Architecture
```
Browser (S3 static site) → API Gateway (HTTP API) → Lambda (Strands orchestrator)
                                                      ├─ Amazon Bedrock (Nova Lite)
                                                      └─ DynamoDB (progress)
```

## Run locally
```bash
pip install -r requirements.txt
aws configure            # needs Bedrock access to Nova Lite
python agent.py
```

## Deploy
1. DynamoDB table `dsa-study-progress` (PK `user_id`, SK `topic`, both String)
2. Package: `pip install -r requirements.txt -t package/ --platform manylinux2014_x86_64 --only-binary=:all: && cp *.py package/ && cd package && zip -r ../function.zip .`
3. Lambda: Python 3.12, handler `lambda_function.lambda_handler`, 1024 MB, 60s timeout, permissions for `bedrock:InvokeModel*` + DynamoDB
4. API Gateway HTTP API → `POST /chat` → Lambda, CORS enabled
5. Put the API URL in `index.html`, then upload it to an S3 static website bucket

## Social impact
Free, always-available, personalized DSA mentoring in the student's own language.

## Built with
Strands Agents SDK · Amazon Bedrock · AWS Lambda · API Gateway · DynamoDB · S3 . IAM . EC2
