import streamlit as st
import json
import time
import requests
import pandas as pd
from profile_logic import determine_commuter_profile, COMMUTER_PROFILES
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Configuration ---
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual Gemini API key.
# You can get one from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY = "AIzaSyAzPkgNT0nd4-IP_svJJFSmSWLZ5fZ_idA"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

# --- Load and Analyze Survey Data from CSV ---
csv_data_summary = ""
try:
    df = pd.read_csv("urban.csv")

    # Clean and analyze the data to create a summary for the chatbot
    issues_frustration = df['What issues frustrate you most about Almere Bus line?'].value_counts()
    commute_time = df['What time do you usually leave for work/school?'].str[:2].astype(int).mean()
    age_average = df['What is your age?'].mean()
    primary_transport = df['What is your primary mode of transportation?'].value_counts().idxmax()
    crowd_levels = df['How crowded is your usual bus during peak hours?'].value_counts()

    csv_data_summary = f"""
    Summary of Commuter Survey Data for Almere Bus Network:
    - Average age of respondents: {age_average:.1f}
    - Most common primary transportation: {primary_transport}
    - Average commute start time: {commute_time:.0f}:00 AM
    - Top frustration issues: {issues_frustration.index[0]}, {issues_frustration.index[1]}
    - Reported peak hour crowd levels: Most respondents feel the bus is '{crowd_levels.idxmax()}'
    """
except Exception as e:
    st.error(f"Error loading survey data: {e}")
    st.warning("Please ensure 'urban.csv' is in the same directory as this script.")
    df = pd.DataFrame()

# --- Gemini API Call ---
def generate_bot_response_with_gemini(prompt, profile, csv_summary):
    """
    Generates a bot response using the Gemini API, grounded in user profile
    and CSV data summary.
    """
    try:
        # Define the system instruction to set the bot's persona and context
        system_prompt = f"""
        You are an urban mobility assistant designed to give personalized travel advice.
        Your persona is: helpful, knowledgeable, and empathetic.
        The user's commuter profile is: '{profile}'
        You have access to the following summarized survey data about Almere commuters:
        {csv_summary}
        Use this information to provide tailored and relevant advice.
        If the user asks about schedules or crowding, you can use the data you have, but be clear that the data is based on a survey and not real-time.
        The current date and time is {datetime.now(ZoneInfo('Europe/Amsterdam')).strftime('%Y-%m-%d %H:%M:%S')}.
        """
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "model", "parts": [{"text": "Hello, I'm ready to help you with your commute."}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "tools": [{"google_search": {}}]
        }

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Check if the response contains valid content
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                return candidate['content']['parts'][0]['text']
        return "I'm sorry, I couldn't generate a response. Please try again."

    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}"

# --- Streamlit App UI and Logic ---
st.set_page_config(page_title="Urbanvind Commuter Chatbot", page_icon="🚍")
st.sidebar.title("Urbanvind Commuter Chatbot")
st.sidebar.markdown("A personalized chatbot for Almere residents.")


# Initialize session state variables
if "chat_phase" not in st.session_state:
    st.session_state.chat_phase = "profile_survey"
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Profile Survey Phase ---
if st.session_state.chat_phase == "profile_survey":
    st.title("Commuter Profile Survey")
    st.info("Please answer a few questions to help me understand your travel habits. This will help me give you more personalized advice.")

    # Modified Survey questions to demonstrate how to change the app
    st.session_state.user_answers['Q1'] = st.radio("What is your primary mode of transportation for this trip?", ["Bus", "Train", "Car", "Bicycle"])
    st.session_state.user_answers['Q2'] = st.radio("How important is a punctual arrival to you?", ["Not Important at all", "Somewhat Important", "Very Important", "Absolutely Critical"])
    st.session_state.user_answers['Q3'] = st.radio("How often do you use this specific bus line?", ["Daily", "Several times a week", "A few times a month", "Rarely"])
    st.session_state.user_answers['Q4'] = st.slider("On a scale of 1-5, how willing are you to stand for the entire trip?", 1, 5)

    if st.button("Determine my profile"):
        determined_profile = determine_commuter_profile(st.session_state.user_answers)
        st.session_state.selected_profile = determined_profile

        profile_message = f"Based on your answers, your profile is: **{determined_profile}**."
        st.session_state.messages.append({"role": "bot", "content": profile_message})
        
        st.session_state.chat_phase = "chatting"
        st.session_state.messages.append({"role": "bot", "content": "Now you can ask me for personalized travel advice!"})
        st.rerun()
        
# --- Chatting Phase ---
elif st.session_state.chat_phase == "chatting":
    if st.session_state.selected_profile:
        st.info(f"Your current profile: **{st.session_state.selected_profile}**")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("bot"):
            with st.spinner("Thinking..."):
                bot_response = generate_bot_response_with_gemini(prompt, st.session_state.selected_profile, csv_data_summary)
                st.markdown(bot_response)
        
        st.session_state.messages.append({"role": "bot", "content": bot_response})
