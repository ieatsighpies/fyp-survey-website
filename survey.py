import streamlit as st

survey_questions = [
    "What's your name?",
    "Do you prefer pizza or sushi?",
    "Do you like arts or science?",
    "How would you commute to Changi airport?",
    "How would you diet?",
    "What is most important when planning a trip with friends?",
    "What do you treasure most in life?"
]

def render_survey_form(existing_responses=None):
    if existing_responses is None:
        existing_responses = {}

    with st.form("survey_form"):
        responses = {}
        responses["name"] = st.text_input(survey_questions[0], value=existing_responses.get("name", ""))
        responses["food_pref"] = st.radio(
            survey_questions[1],
            ["Pizza", "Sushi"],
            index=0 if existing_responses.get("food_pref", "") == "Pizza" else 1
        )
        responses["interest"] = st.radio(
            survey_questions[2],
            ["Arts", "Science"],
            index=0 if existing_responses.get("interest", "") == "Arts" else 1
        )
        responses["commute"] = st.selectbox(
            survey_questions[3],
            ["Taxi", "Bus", "MRT", "Car", "Other"],
            index=["Taxi", "Bus", "MRT", "Car", "Other"].index(existing_responses.get("commute", "Taxi"))
        )
        responses["diet"] = st.text_area(survey_questions[4], value=existing_responses.get("diet", ""))
        responses["trip_plan"] = st.text_area(survey_questions[5], value=existing_responses.get("trip_plan", ""))
        responses["treasure"] = st.text_area(survey_questions[6], value=existing_responses.get("treasure", ""))

        submitted = st.form_submit_button("Submit Survey")
        return submitted, responses