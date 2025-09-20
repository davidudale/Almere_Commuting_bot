import streamlit as st
import json
import time
import requests
import pandas as pd
from profile_logic import determine_commuter_profile, COMMUTER_PROFILES
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Configuration ---
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual Gemini API key.
# You can get one from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY = "AIzaSyAzPkgNT0nd4-IP_svJJFSmSWLZ5fZ_idA"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

# --- Load and Analyze Survey Data from CSV ---
try:
    df = pd.read_csv("urban.csv")

    # Clean and analyze the data to create a summary for the chatbot
    issues_frustration = df['What issues frustrate you most about Almere Bus line?'].value_counts()
    commute_time = df['What time do you usually leave for work/school?'].str[:2].astype(int).mean()
    age_average = df['What is your age?'].mean()
    primary_transport = df['What is your primary mode of transportation?'].value_counts().idxmax()
    crowd_levels = df['How crowded is your usual bus during peak hours?'].value_counts()

    csv_data_summary = f"""
    Summary of Almere Commuter Survey Data:
    - Top frustrations: {issues_frustration.to_dict()}
    - Average commute start time: {commute_time:.0f}:00
    - Average age: {age_average:.0f}
    - Primary mode of transport: {primary_transport}
    - Reported crowd levels during peak hours: {crowd_levels.to_dict()}
    """
except Exception as e:
    st.error(f"Error loading or analyzing urban.csv: {e}")
    csv_data_summary = "No survey data available."

# --- Helper Functions ---
def get_current_time_for_almere():
    """Gets the current time in the Europe/Amsterdam timezone (Almere, Netherlands)."""
    almere_tz = ZoneInfo("Europe/Amsterdam")
    now = datetime.now(almere_tz)
    return now.strftime("%A, %B %d, %Y at %H:%M")

def display_current_time():
    """Displays the current time and updates it automatically."""
    current_time_str = get_current_time_for_almere()
    st.markdown(f"<div style='text-align: right; font-size: 0.8em; color: gray;'>Current time in Almere: {current_time_str}</div>", unsafe_allow_html=True)
    time.sleep(1) # Rerun the script every second to update the time
    st.rerun()
    

def generate_bot_response_with_gemini(prompt, commuter_profile, data_summary):
    """
    Generates a response from the Gemini API using search grounding.
    The prompt includes the user's question, their profile, and a summary of the survey data.
    It now also includes the current time and day of the week for context.
    """
    current_almere_time = get_current_time_for_almere()
    
    system_instruction = f"""
    You are a friendly and helpful commuter chatbot for the city of Almere, Netherlands.
    Your goal is to provide personalized and useful advice to commuters based on their profile, general survey data, and live time context.

    Commuter's profile: {COMMUTER_PROFILES.get(commuter_profile, 'unknown')}
    Time and Day context: It is currently {current_almere_time} in Almere.

    Crowding and scheduling data to consider:
    - Simulated Metro bus line operational times (M1-M8): 04:30 AM to 02:00 AM, 7 days a week.
    - Simulated weekday-only lines (22, 24): 06:00 AM to 08:00 PM, Weekdays.
    - Simulated night lines (N22, N23): 10:00 PM to 04:00 AM.
    - Simulated peak hours for crowding are from 07:00 AM to 09:00 AM and 04:00 PM to 06:00 PM.
    - Based on the user's profile, they have a certain tolerance for crowding and willingness to change their plans.
    - {data_summary}

    Based on the above information, respond to the user's prompt.
    - Be concise and direct.
    - Ground your response in the provided profile and simulated data.
    - If the user asks for advice on a time or day outside of a bus line's operation, clearly state that the line is not running.
    - Do not make up information. If you don't have an answer, say so politely.
    - Your responses should be conversational, as if you're a helpful travel assistant.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        bot_response = response.json()['candidates'][0]['content']['parts'][0]['text']
        return bot_response
    except requests.exceptions.RequestException as e:
        return f"An error occurred while connecting to the Gemini API: {e}"


# --- Streamlit UI ---
st.title("Urbanvind Commuter Chatbot Prototype")
st.markdown("Your personalized travel assistant for Almere.")

# Display the current time at the top right
display_current_time()

if "chat_phase" not in st.session_state:
    st.session_state.chat_phase = "profile_selection"
    st.session_state.messages = []
    st.session_state.user_answers = {}
    st.session_state.selected_profile = None

if st.session_state.chat_phase == "profile_selection":
    # Manually select a profile or determine it from CSV
    st.markdown("### Profile Selection")
    st.markdown("First, let's determine your commuter profile. You can either select one below or let the app determine it from the CSV data.")

    # Manual selection
    selected_option = st.radio(
        "**Manual Profile Selection:**",
        options=list(COMMUTER_PROFILES.keys()),
        index=None
    )

    if selected_option:
        st.session_state.selected_profile = selected_option
        st.session_state.chat_phase = "chatting"
        st.session_state.messages.append({"role": "bot", "content": f"You have selected the **{selected_option}** profile. Feel free to ask me for personalized travel advice!"})
        st.rerun()

elif st.session_state.chat_phase == "chatting":
    st.info(f"Your current profile: **{st.session_state.selected_profile}**")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("bot"):
            with st.spinner("Thinking..."):
                bot_response = generate_bot_response_with_gemini(prompt, st.session_state.selected_profile, csv_data_summary)
                st.markdown(bot_response)
        
        st.session_state.messages.append({"role": "bot", "content": bot_response})
