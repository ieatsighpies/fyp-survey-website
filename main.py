import streamlit as st
from db_utils import insert_survey_response, insert_chat_log #delete_all_documents
from survey import render_survey_form, survey_questions
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai"]["key"])

def initialize_session_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "survey"
        st.session_state.survey_responses = {}
        st.session_state.messages = []
        st.session_state.current_question_index = 1 # skip name

def show_survey_stage():
    if st.session_state.stage == "survey":
        submitted, survey_responses = render_survey_form(existing_responses=st.session_state.survey_responses)
        if submitted:
            st.session_state.survey_responses = survey_responses
            insert_survey_response(survey_responses)
            st.session_state.stage = "chat"
            st.success("Survey submitted! You can now debate with the LLM about your responses.")
            st.rerun()


@st.fragment
def show_chat_stage():
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    idx = st.session_state.current_question_index
    if idx < len(survey_questions):
        # Show the corresponding survey question
        st.markdown(f"**Give reasons for your answer to: {survey_questions[idx]}** You answered with: *{st.session_state.survey_responses[list(st.session_state.survey_responses.keys())[idx]]}*")

        # Accept user input
        if prompt := st.chat_input("Defend your choices:"):
            system_prompt = {
                "role": "system",
                "content": (
                    """You are a devil's advocate. Convince the user to pick an alternative option.\
                    For multiple choice questions, argue for the option they did not pick.
                    Be assertive, relevant, and focus on each survey answer separately. questions are: {survey_questions}"""
                )
            }

            if not any(m["role"] == "system" for m in st.session_state.messages):
                st.session_state.messages.append(system_prompt)

            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                # response = generate_assistant_response(prompt)
                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            # Insert chat log into DB
            insert_chat_log(user_message=prompt, assistant_response=response)
            # Move to the next question
            st.session_state.current_question_index += 1
            st.rerun()
    else:
        st.success("You have completed the debate for all survey questions. Thank you!")


def main():
    initialize_session_state()
    if st.session_state.stage == "survey":
        st.title("Persuasive Power of Chatbots in Everyday Decisionmaking")
        show_survey_stage()
    if st.session_state.stage == "chat":
        st.header("The chatbot will now play devil's advocate on your survey responses.")
        show_chat_stage()


if __name__ == "__main__":
    main()