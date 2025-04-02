import streamlit as st
from openai import OpenAI
from pinecone import Pinecone

# Load API keys from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

# Initialize OpenAI and Pinecone clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Create embedding from user query using OpenAI (new API format)
def get_embedding(text: str, model="text-embedding-ada-002"):
    response = client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

# Search Pinecone for relevant context
def retrieve_context(query: str, top_k=5):
    query_embedding = get_embedding(query)
    result = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

    # Extract context chunks from metadata
    contexts = [match["metadata"]["text"] for match in result.matches if "metadata" in match and "text" in match["metadata"]]
    return "\n\n".join(contexts)

# Generate Socratic tutor response using RAG-enhanced prompt
def generate_response(ignore, chat_history):
    # Get the latest user message
    user_message = [msg["content"] for msg in chat_history if msg["role"] == "user"][-1]

    # Retrieve context from Pinecone
    rag_context = retrieve_context(user_message)

    # Build the system prompt
    prompt = f"""
You are a Socratic tutor with access to a knowledge base.

[Knowledge Base]
{rag_context}

Follow these principles:
- Ask thought-provoking, open-ended questions that challenge students' preconceptions and encourage them to engage in deeper reflection and critical thinking.
- Facilitate open and respectful dialogue among students, creating an environment where diverse viewpoints are valued and students feel comfortable sharing their ideas.
- Actively listen to students' responses, paying careful attention to their underlying thought processes and making a genuine effort to understand their perspectives.
- Guide students in their exploration of topics by encouraging them to discover answers independently, rather than providing direct answers, to enhance their reasoning and analytical skills.
- Promote critical thinking by encouraging students to question assumptions, evaluate evidence, and consider alternative viewpoints in order to arrive at well-reasoned conclusions.
- Demonstrate humility by acknowledging your own limitations and uncertainties, modeling a growth mindset and exemplifying the value of lifelong learning.
     """

    # Make chat completion request with GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}] + chat_history
    )

    return response.choices[0].message.content
