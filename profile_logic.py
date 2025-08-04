import datetime

# --- Commuter Profiles Definition ---
# This dictionary contains the definitions for each commuter profile.
COMMUTER_PROFILES = {
    "Peak Routine Commuter": {
        "description": "A person with a fixed, early commute schedule who is less likely to change their plans, even when faced with crowding.",
        "logic_keywords": "Early departure, fixed schedule (5+ days/week), low flexibility, low digital openness, takes the bus anyway when crowded."
    },
    "Flexible Avoider": {
        "description": "A person who is highly flexible and actively avoids crowded buses by changing their departure time, route, or waiting for the next one.",
        "logic_keywords": "High flexibility, proactive crowd avoidance, digital-open, willing to change plans to avoid discomfort."
    },
    "Inflexible Tolerant": {
        "description": "Someone who reports high crowding but is not affected by it. They have a fixed routine and a high tolerance for discomfort, making them unlikely to change their travel habits.",
        "logic_keywords": "High crowding experience, high tolerance, fixed schedule, unaffected by crowding, low digital openness."
    },
    "Adaptive Midday Rider": {
        "description": "A commuter with some flexibility who rides during midday hours. Their choices are context-driven, and they are open to new tools and ideas but not necessarily proactive planners.",
        "logic_keywords": "Midday/later departure, some flexibility, open to new ideas, context-driven choices."
    },
    "Late Responder": {
        "description": "A commuter who doesn't proactively plan for crowding but will react in the moment to adjust their travel. They are responsive to real-time information.",
        "logic_keywords": "Doesn't proactively plan, reacts in the moment, responsive to real-time info, will wait or switch lines when faced with crowding."
    },
    "Unknown Profile": {
        "description": "A commuter profile could not be determined based on the provided answers.",
        "logic_keywords": "No clear match found."
    }
}

def determine_commuter_profile(user_survey_response):
    """
    Determines a commuter's profile based on their answers to key survey questions.
    This logic has been revised to be more comprehensive and ensure a profile
    is always assigned based on the available answers.

    Args:
        user_survey_response (dict): A dictionary containing the user's answers,
                                     with keys matching the survey question names.

    Returns:
        str: The name of the determined commuter profile.
    """
    # Safely retrieve answers using .get() with default values to prevent errors
    q7_departure_time = user_survey_response.get('What time do you usually leave for work/school?', '')
    q9_commute_frequency = user_survey_response.get('How many days per week do you commute?', '')
    q10_crowding_experience = user_survey_response.get('How crowded is your usual bus during peak hours?', '')
    q16_change_departure_scale = int(user_survey_response.get('I would change my departure time if I knew my usual bus was full.', 0))
    q21_full_bus_response = user_survey_response.get('If your usual bus is 90% full when it arrives, what would you most likely do?', '')

    # --- Profile Determination Logic (Revised to be more comprehensive) ---
    
    # Check for strong indicators first
    
    # 1. Flexible Avoider: Prioritizes changing plans to avoid a full bus
    if q16_change_departure_scale >= 4 and q21_full_bus_response in ["Wait for the next one", "Change my travel time", "Switch to a different line"]:
        return "Flexible Avoider"

    # 2. Inflexible Tolerant: Experiences crowding but won't change plans
    if q10_crowding_experience in ["Very crowded", "Overcrowded"] and q16_change_departure_scale <= 2 and q21_full_bus_response == "Board anyway":
        return "Inflexible Tolerant"

    # 3. Peak Routine Commuter: Early, rigid schedule and low flexibility
    if q7_departure_time == "Before 9:00 AM" and q9_commute_frequency == "5+ days" and q16_change_departure_scale <= 2:
        return "Peak Routine Commuter"

    # 4. Late Responder: Reacts in the moment to a full bus, but doesn't proactively plan
    if q16_change_departure_scale >= 3 and q21_full_bus_response in ["Wait for the next one", "Switch to a different line"]:
        return "Late Responder"

    # 5. Adaptive Midday Rider: A catch-all for other flexible commuters
    # This profile is assigned if a user doesn't fit a more specific, rigid profile.
    if q7_departure_time == "9:00 AM or later" and q16_change_departure_scale >= 3:
        return "Adaptive Midday Rider"

    # If none of the above conditions are met, we'll assign a default profile
    # to avoid the 'Unknown Profile' response. The Adaptive Midday Rider is a good
    # general profile for a non-specific user.
    return "Adaptive Midday Rider"
