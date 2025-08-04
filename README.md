Urbanvind Commuter Chatbot
This project develops a prototype of a commuter decision support system, featuring a personalized chatbot for Almere residents. The chatbot provides tailored travel suggestions based on user profiles and simulated crowding data.

Project Components
app.py: The main Streamlit application.

profile_logic.py: Contains the logic for defining and determining commuter profiles based on survey data.

Commuter Profiles: Five distinct commuter profiles (Peak Routine Commuter, Flexible Avoider, Inflexible Tolerant, Adaptive Midday Ridder, Late Responder) are defined based on behavioral theory and survey insights.

Simulated Crowding Data: A mock dataset simulates real-time crowding on various bus and train routes at different times.

Personalized Chatbot: A Streamlit application with a chatbot interface that uses the Google Gemini API to provide custom advice, taking into account the user's selected commuter profile and the simulated crowding data.

Survey Data Integration: The application loads survey data directly from a CSV file placed in the project directory. It attempts to determine the commuter profile of the first respondent in that file based on predefined logic. Regardless of whether a profile is determined from the CSV, a manual selection option is always provided at the top.

Setup and Installation
Follow these steps to set up and run the Urbanvind Commuter Chatbot locally:

1. Create Project Files
Create a new directory for your project and then create the following files within it:

app.py

profile_logic.py

requirements.txt

README.md

Copy the content provided in the immersive blocks from our conversation into their respective files.

2. Create a Virtual Environment (Recommended)
It's good practice to use a virtual environment to manage project dependencies.

python -m venv venv
# On Windows:
.\venv\Scripts\activate


3. Install Dependencies
Install the required Python libraries using the requirements.txt file:

pip install -r requirements.txt

4. Get Your Google Gemini API Key
The chatbot uses the Google Gemini API for its conversational intelligence.

Go to Google AI Studio.

Log in with your Google account.

Create a new API key.

Open app.py and replace "YOUR_GEMINI_API_KEY" with your newly obtained API key:

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" # <<< REPLACE THIS

Important: Do not commit your API key directly to a public repository. For production applications, consider using environment variables. For this prototype, direct insertion is acceptable for local testing.

5. Prepare Your Survey Data
Export from Google Forms:

Go to your Google Form (the link you provided earlier).

Click on the "Responses" tab.

Click the green Google Sheets icon to view responses in Google Sheets.

In Google Sheets, go to File > Download > Comma Separated Values (.csv). Save this CSV file (e.g., urban.csv) to the same directory as your app.py and profile_logic.py files.

Inspect and Adapt profile_logic.py (CRITICAL STEP):

Open your downloaded CSV file (e.g., urban.csv) in a text editor or spreadsheet program.

Crucially, note the exact column headers for each question (e.g., "What time do you usually leave for work/school?", "How many days per week do you commute?", etc.). Google Forms often uses the full question text as the header.

Open profile_logic.py and go to the determine_commuter_profile function.

Replace the placeholder column names (e.g., 'What time do you usually leave for work/school?') with the exact column headers from your CSV.

Adjust the answer strings in the if conditions (e.g., "Wait for the next one", "Very crowded", "Yes", "No", "Maybe", "5+ days") to precisely match the options provided in your Google Form and how they appear in your CSV. For 1-5 scale questions, ensure the integer comparison logic (<=2, >=4, ==3) correctly reflects "Disagree", "Agree", and "Neutral" based on your survey's scale.

This step is vital for the profile determination logic to work correctly with your specific data.

6. Run the Streamlit Application
Once the dependencies are installed, the API key is set, and your profile_logic.py is adapted to your survey's column names and answer values, you can run the application:

streamlit run app.py

This command will open a new tab in your web browser (usually at http://localhost:8501) where you can interact with the chatbot.

How to Use the Chatbot
Launch the App: The app will first attempt to load the profile from your specified CSV file.

Profile Selection:

A radio button group will always be displayed at the top, allowing you to manually select a commuter profile.

If a profile was successfully determined from the CSV, that option will be pre-selected in the radio buttons.

If no profile could be determined from the CSV (e.g., file not found, empty, or no match), the radio buttons will default to no selection, allowing you to pick one.

Start Chatting: Once a profile is selected (either automatically pre-selected or manually chosen), the chat interface will appear.

Ask about crowding: E.g., "Is Bus 10 crowded at 8 AM?", "How crowded is Train A at 5 PM?"

Ask for advice: E.g., "Suggest a travel time", "Give me advice for my commute."

Experience Tailored Advice: Observe how the chatbot's responses adapt based on the commuter profile and the simulated crowding data.

Simulated Data
Please note that for this prototype, the crowding data is simulated within the app.py file. In a full-fledged system, this data would come from a live traffic simulation model.

