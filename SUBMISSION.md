# Submission text (copy-paste)

**Project name:** DSA Study Buddy
**Track:** Education
**Tagline:** A multi-agent AI mentor that teaches, quizzes and coaches students on DSA, in their own language.

**Description:**
Students in Tier-2/3 colleges in India often prepare for placements without a mentor. DSA Study Buddy is a multi-agent system built with the Strands Agents SDK. An Orchestrator agent sends each message to one of three specialist agents. The Tutor explains concepts with analogies, Python code and complexity, and also replies in Thanglish. The Quiz Master asks MCQs, grades the answers and saves the results to DynamoDB. The Coach finds the student's weak topics, recommends LeetCode problems and writes a 3-day study plan.

**How Strands is used:** agents-as-tools multi-agent pattern, custom @tool functions (DynamoDB progress tracking, problem recommender), BedrockModel (Amazon Nova Lite).

**Architecture:** S3 static site → API Gateway HTTP API → Lambda (Strands orchestrator) → Amazon Bedrock + DynamoDB.

**Links:** GitHub: <your repo> | Live: <S3 URL> | Demo: <video link>

---
# 2-minute demo video script
1. (0:00–0:15) "Hi, I'm Sankar. Students without mentors struggle with DSA, so I built DSA Study Buddy with Strands."
2. (0:15–0:45) Click **Explain DP** → Tutor agent answers with an analogy and code.
3. (0:45–1:15) Click **Quiz me: Graphs** → answer it → it gets graded and saved.
4. (1:15–1:40) Click **My plan** → Coach shows weak topics and a 3-day plan.
5. (1:40–2:00) Show the README architecture → "Orchestrator + 3 agents, on Lambda, Bedrock and DynamoDB. Thank you!"
