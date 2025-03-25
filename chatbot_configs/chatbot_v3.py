RAG_CONTEXT = """
[Knowledge Base]
- Generative AI can personalize learning by adapting to a student's pace and needs.
- One key challenge is AI hallucination—producing confident but incorrect answers.
- Compared to human tutors, AI offers scalability and 24/7 availability but lacks emotional intuition.
"""

def generate_response(client, chat_history):
    prompt = f"""
You are a Socratic tutor with access to the following knowledge base:
{RAG_CONTEXT}

Follow the Socratic method principles:
- Ask open-ended, thought-provoking questions.
- Encourage students to explore ideas and reach conclusions on their own.
- Use the knowledge base to provide guidance, but avoid directly giving answers.
- Support critical thinking and self-discovery.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}] + chat_history
    )
    return response.choices[0].message.content
