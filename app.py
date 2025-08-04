import streamlit as st
import json
import time
import requests
import pandas as pd
from profile_logic import determine_commuter_profile, COMMUTER_PROFILES
import datetime

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
    Summary of Urban Mobility Survey responses from Almere:
    - The most common frustrations with the bus line are: {issues_frustration.head(3).to_dict()}
    - The average commuter leaves for work/school around {commute_time:.0f}:00.
    - The most common primary mode of transportation is: {primary_transport}.
    - Commuters perceive peak hour crowding as follows: {crowd_levels.to_dict()}.
    - A significant number of people {df[df['Would you be open to using an app that gives personal travel advice based on real-time crowd levels?'] == 'Yes'].shape[0]} are open to using a travel advice app.
    """
except FileNotFoundError:
    st.error("Survey data file not found. The bot will use general knowledge instead.")
    csv_data_summary = "No survey data available for analysis."

# --- Simulated Crowding Data ---
# This dictionary simulates real-time crowding data based on the provided heatmap image.
SIMULATED_CROWDING_DATA = {
    'M1': {
        '7 AM': {'status': 'moderately crowded', 'percentage': 70},
        '8 AM': {'status': 'very crowded', 'percentage': 95},
        '1 PM': {'status': 'not crowded', 'percentage': 30},
        '5 PM': {'status': 'moderately crowded', 'percentage': 75},
        '6 PM': {'status': 'very crowded', 'percentage': 90},
        '2 AM': {'status': 'not crowded', 'percentage': 5}
    },
    'M2': {
        '7 AM': {'status': 'moderately crowded', 'percentage': 65},
        '8 AM': {'status': 'very crowded', 'percentage': 85},
        '1 PM': {'status': 'not crowded', 'percentage': 25},
        '5 PM': {'status': 'very crowded', 'percentage': 80},
        '6 PM': {'status': 'moderately crowded', 'percentage': 60},
        '2 AM': {'status': 'not crowded', 'percentage': 10}
    },
    'M7': {
        '7 AM': {'status': 'very crowded', 'percentage': 85},
        '8 AM': {'status': 'overcrowded', 'percentage': 100},
        '1 PM': {'status': 'moderately crowded', 'percentage': 50},
        '5 PM': {'status': 'overcrowded', 'percentage': 100},
        '6 PM': {'status': 'very crowded', 'percentage': 95},
        '2 AM': {'status': 'not crowded', 'percentage': 15}
    },
    'Bus 24': {
        '7 AM': {'status': 'not crowded', 'percentage': 40},
        '8 AM': {'status': 'moderately crowded', 'percentage': 60},
        '1 PM': {'status': 'not crowded', 'percentage': 35},
        '5 PM': {'status': 'moderately crowded', 'percentage': 55},
        '6 PM': {'status': 'moderately crowded', 'percentage': 70},
        '2 AM': {'status': 'not crowded', 'percentage': 5}
    }
}

# --- Conversational Questions for Profile Determination ---
# These are simplified versions of the survey questions with controlled options.
CONVERSATIONAL_QUESTIONS = [
    {
        "text": "Hello! I'm your Urbanvind Commuter Chatbot. To get started, I need to understand your travel habits. What time do you usually leave for work/school?",
        "key": "What time do you usually leave for work/school?",
        "options": ["Before 9:00 AM", "9:00 AM or later"]
    },
    {
        "text": "How many days per week do you typically commute?",
        "key": "How many days per week do you commute?",
        "options": ["1-2 days", "3-4 days", "5+ days", "I work remotely"]
    },
    {
        "text": "How crowded is your usual bus or train during peak hours?",
        "key": "How crowded is your usual bus during peak hours?",
        "options": ["Not crowded", "Slightly crowded", "Very crowded", "Overcrowded"]
    },
    {
        "text": "If you knew your usual bus was full, would you change your departure time? (1='Definitely not', 5='Definitely')",
        "key": "I would change my departure time if I knew my usual bus was full.",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "text": "If your usual bus arrived 90% full, what would you most likely do?",
        "key": "If your usual bus is 90% full when it arrives, what would you most likely do?",
        "options": ["Wait for the next one", "Change my travel time", "Switch to a different line", "Board anyway", "Cancel or delay the trip"]
    }
]


def call_gemini_api(prompt_text):
    """
    Calls the Gemini API with the given prompt and handles exponential backoff.
    """
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt_text}]}
        ]
    }

    retries = 0
    max_retries = 5
    base_delay = 1  # seconds

    while retries < max_retries:
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and \
               result['candidates'][0]['content'].get('parts') and \
               result['candidates'][0]['content']['parts'][0].get('text'):
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                st.error(f"Unexpected API response structure: {result}")
                return "I'm sorry, I couldn't generate a response due to an unexpected API format."

        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < max_retries:
                delay = base_delay * (2 ** (retries - 1)) # Exponential backoff
                time.sleep(delay)
                # print(f"API call failed: {e}. Retrying in {delay} seconds...") # For debugging
            else:
                st.error(f"Failed to connect to Gemini API after {max_retries} retries: {e}")
                return "I'm currently unable to connect to my knowledge base. Please try again later."
        except json.JSONDecodeError:
            st.error("Failed to decode JSON response from API.")
            return "I'm sorry, I received an unreadable response from my knowledge base."
    return "I'm currently unable to process your request. Please try again later."


def generate_bot_response_with_gemini(user_message, selected_profile, csv_summary):
    """
    Generates a tailored bot response using the Gemini API, incorporating
    the user's profile, simulated crowding data, and CSV survey summary.
    """
    profile_info = COMMUTER_PROFILES.get(selected_profile, {"description": "unknown", "logic_keywords": "unknown"})
    current_hour = datetime.datetime.now().hour
    current_time_key = '7 AM' if 7 <= current_hour < 9 else '1 PM' if 12 <= current_hour < 14 else '5 PM' if 16 <= current_hour < 18 else '2 AM'

    # Construct the prompt for Gemini, including the CSV summary
    prompt = f"""
    You are Urbanvind Commuter Chatbot, a decision support system for Almere residents.
    Your goal is to provide tailored travel suggestions and information based on the user's commuter profile, real-time (simulated) crowding data, and insights from a survey of Almere commuters.

    Insights from the Almere Commuter Survey:
    {csv_summary}

    The user's profile is: "{selected_profile}".
    This means: {profile_info['description']}
    Key characteristics of this profile include: {profile_info['logic_keywords']}

    Current simulated crowding data for key routes at {current_time_key}:
    {json.dumps(SIMULATED_CROWDING_DATA, indent=2)}

    Based on the user's profile, the survey insights, and the crowding data, provide a tailored travel suggestion or answer their question.
    Keep your response concise, helpful, and align it with their profile's characteristics.
    If the user asks about crowding, use the provided simulated data.
    If the user asks for general travel advice for Almere, use the current simulated crowding data and the survey insights to give a general recommendation.
    If the user asks for general advice, use their profile to suggest appropriate actions (e.g., for 'Flexible Avoider', suggest proactive changes; for 'Peak Routine Commuter', acknowledge their routine but gently suggest minor adjustments if needed).

    User's message: "{user_message}"
    """

    response_text = call_gemini_api(prompt)
    return response_text

# --- Streamlit UI ---
st.set_page_config(page_title="Urbanvind Commuter Chatbot", layout="centered")

st.title("🏙️ Urbanvind Commuter Chatbot")
st.markdown("Your personalized travel assistant for Almere.")

# --- Sidebar for Live Crowding Data ---
st.sidebar.title("📊 Live Crowding Data")
st.sidebar.markdown("*(Simulated data for demonstration)*")

# Get current time to determine peak/off-peak
current_hour = datetime.datetime.now().hour
current_time_key = '7 AM' if 7 <= current_hour < 9 else '1 PM' if 12 <= current_hour < 14 else '5 PM' if 16 <= current_hour < 18 else '2 AM'

st.sidebar.subheader("Bus Lines")
for line, times in SIMULATED_CROWDING_DATA.items():
    if "Bus" in line or line.startswith('M'):
        data = times.get(current_time_key, {'status': 'not crowded', 'percentage': 0})
        status = data['status']
        percentage = data['percentage']
        color = "green" if percentage < 50 else "orange" if percentage < 80 else "red"
        st.sidebar.markdown(f"**{line}** at {current_time_key}:")
        st.sidebar.progress(percentage, text=f"{percentage}% ({status})")

st.sidebar.subheader("Train Lines")
# The image only shows bus lines, so we'll leave this section as a placeholder.
st.sidebar.markdown("*(No simulated data for train lines available)*")

# Initialize session state for conversation
if "chat_phase" not in st.session_state:
    st.session_state.chat_phase = "questions"
    st.session_state.questions_asked = 0
    st.session_state.user_answers = {}
    st.session_state.selected_profile = None
    st.session_state.messages = []


# --- Conversation Flow Logic ---
if st.session_state.chat_phase == "questions":
    # Check if all questions have been asked
    if st.session_state.questions_asked >= len(CONVERSATIONAL_QUESTIONS):
        st.session_state.chat_phase = "determining_profile"
        st.rerun()

    # If not all questions have been asked, display the next one
    else:
        current_question_index = st.session_state.questions_asked
        current_question = CONVERSATIONAL_QUESTIONS[current_question_index]

        # Use a single chat message container for the bot's question
        with st.chat_message("bot"):
            st.markdown(current_question['text'])

        # Use radio buttons for all questions with predefined options
        user_answer = st.radio(
            "Please select an option:",
            current_question['options'],
            key=f"q_radio_{current_question_index}"
        )
        if st.button("Next Question", key=f"next_{current_question_index}"):
            st.session_state.user_answers[current_question['key']] = user_answer
            st.session_state.questions_asked += 1
            st.rerun()

elif st.session_state.chat_phase == "determining_profile":
    with st.spinner("Analyzing your answers and determining your commuter profile..."):
        determined_profile = determine_commuter_profile(st.session_state.user_answers)
        st.session_state.selected_profile = determined_profile

        profile_message = f"Based on your answers, your profile is: **{determined_profile}**."
        st.session_state.messages.append({"role": "bot", "content": profile_message})
        
        st.session_state.chat_phase = "chatting"
        st.session_state.messages.append({"role": "bot", "content": "Now you can ask me for personalized travel advice!"})
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

    st.markdown("---")
    st.caption("Note: Crowding data is simulated for this prototype.")
