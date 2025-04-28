import streamlit as st
import openai
import time
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from pinecone import Pinecone

# Retrieve secrets
# Load API Key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# Load Pinecone Secrets

PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

# Initialize Pinecone
pc = Pinecone(PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Load Firebase Credentials
firebase_creds = {
    "type": "service_account",
    "project_id": st.secrets["FIREBASE_PROJECT_ID"],
    "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
    "private_key": st.secrets["FIREBASE_PRIVATE_KEY"],
    "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
    "client_id": st.secrets["FIREBASE_CLIENT_ID"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40thesis-chat-4ce35.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)

if not OPENAI_API_KEY:
    st.error("Missing API keys! Check your .env file.")
    st.stop()

SURVEY_LINK = "https://sydney.au1.qualtrics.com/jfe/form/SV_b8i421dY50SCTps"


db = firestore.client()
chat_collection = db.collection("chats")

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# User Authentication
st.title("Chatbot Session")
name = st.text_input("Enter your Full Name:")
password = st.text_input("Enter the password:", type="password")
actual = "usyd-genai"
st.text("The password is 'usyd-genai' this step was purely for bot prevention ")
st.text("You will be presented with randomly chosen question related to the ENGG2112 curriculum, please ask the chatbot that question and continue the conversation with a learning mindset")

if st.button("Start Chat") and name and password==actual:
    st.session_state.chat_started = True
    st.session_state.start_time = time.time()
    st.session_state.chat_history.append({"role": "system", "content": f"Hello {name}, let's begin!"})
    st.rerun()

import random

# Define questions
questions = [
    "What is regression?",
    "How can generative AI help students with their coursework?",
    "What is Machine Learning?",
    "What is Supervised learning and Unsupervised learning?",
    "What is training versus testing in the context of ML?",
    "Why do we do data pre processing",
    "What are Convolutional Neural Networks and how do they work",
    "How is machine learning different from traditional programming?",
    "What are the main types of machine learning?",
    "Can you explain supervised learning with an example?",
    "What’s the difference between classification and regression?",
    "What is a dataset, and why is it important?",
    "How do you prepare data for a machine learning model?",
    "What is a loss function?",
    "How does a model “learn” during training?",
    "What is gradient descent?",
    "What are some common algorithms used in machine learning?",
    "What’s the difference between a model and an algorithm?",
    "How do you evaluate the performance of a machine learning model?",
    "What are precision, recall, and F1-score?",
    "What tools or libraries are commonly used for machine learning?",
    "Can you walk me through building a simple machine learning project?",
    "What are neural networks, and how do they work?",
    "How is deep learning different from regular machine learning?",
    "What’s the future of machine learning, and what should I focus on as a beginner?"
]

# Select a random question when the session starts
if "random_question" not in st.session_state:
    st.session_state.random_question = random.choice(questions)


if "chatbot_version" not in st.session_state:
    st.session_state.chatbot_version = random.choice([3])

if st.session_state.chatbot_version == 1:
    from chatbot_configs import chatbot_v1 as chatbot_module
elif st.session_state.chatbot_version == 2:
    from chatbot_configs import chatbot_v2 as chatbot_module
else:
    from chatbot_configs import chatbot_v3 as chatbot_module

st.sidebar.markdown(f"🔒 Internal: Chatbot Version **{st.session_state.chatbot_version}**\n Please note this down for the survey")

# Sidebar Timer Display with Survey Notice

# Timer Logic
if st.session_state.chat_started:
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = max(0, 360 - int(elapsed_time))  # 10-minute timer
    st.sidebar.markdown(f"""
    ### ⏳ Time Remaining: {remaining_time // 60}:{remaining_time % 60:02d}

    After the time is up, you will be redirected to the survey page.
    **The timer must hit zero to be redirected**
    Please have a learning mindset and probe the chatbot based on your starting question
    """)

    # Suggest a question to the user
    st.info(f"💡 Try asking this: **{st.session_state.random_question}**")


    if remaining_time == 0:
        st.session_state.chat_started = False
        chat_log = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]

        # Store in Firestore
        chat_collection.add({
            "name": name,
            "chat_log": chat_log,
            "chatbot_version": st.session_state.chatbot_version,
            "timestamp": time.time()
        })

        st.success("Chat log saved successfully! Redirecting to the survey...")
        time.sleep(3)
        st.markdown(f'<meta http-equiv="refresh" content="0;URL={SURVEY_LINK}">', unsafe_allow_html=True)

if st.session_state.chat_started:
    st.subheader("Chat with AI")

    # Display Chat Messages
    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.write(msg["content"])

    # **User Input and AI Response**
    user_input = st.chat_input("Type your message...")
    
    if user_input:
        # Display User Message Instantly
        with st.chat_message("user"):
            st.write(user_input)

        st.session_state.chat_history.append({"role": "user", "content": user_input})

        bot_reply = chatbot_module.generate_response(client, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

        # Display AI Response Instantly
        with st.chat_message("assistant"):
            st.write(bot_reply)