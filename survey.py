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
        responses["simple_qn_1"] = st.radio(
            survey_questions[1],
            ["Pizza", "Sushi"],
            index=0 if existing_responses.get("simple_qn_1", "") == "Pizza" else 1
        )
        responses["simple_qn_2"] = st.radio(
            survey_questions[2],
            ["Arts", "Science"],
            index=0 if existing_responses.get("simple_qn_2", "") == "Arts" else 1
        )
        responses["medium_qn_1"] = st.selectbox(
            survey_questions[3],
            ["Taxi", "Bus", "MRT", "Car"],
            index=["Taxi", "Bus", "MRT", "Car"].index(existing_responses.get("medium_qn_1", "Taxi"))
        )
        responses["medium_qn_2"] = st.selectbox(
            survey_questions[4],
            ["Keto", "Vegetarian", "Vegan", "Pescatarian"],
            index=["Keto", "Vegetarian", "Vegan", "Pescatarian"].index(existing_responses.get("medium_qn_2", "Keto"))
        )
        responses["complex_qn_1"] = st.text_area(survey_questions[5], value=existing_responses.get("complex_qn_1", ""))
        responses["complex_qn_2"] = st.text_area(survey_questions[6], value=existing_responses.get("complex_qn_2", ""))

        submitted = st.form_submit_button("Submit Survey")
        return submitted, responses