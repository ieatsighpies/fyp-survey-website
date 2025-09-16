import streamlit as st
import logging
from db_utils import insert_survey_response, insert_chat_log, insert_validated_answers
from survey import render_survey_form, survey_questions
from openai import OpenAI

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

client = OpenAI(api_key=st.secrets["openai"]["key"])

def initialize_session_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "survey"
        st.session_state.survey_responses = {}
        st.session_state.messages = []
        st.session_state.current_question_index = 1
        st.session_state.validated_answers = {}
        logging.info("Session initialized.")

def show_survey_stage():
    if st.session_state.stage == "survey":
        submitted, survey_responses = render_survey_form(existing_responses=st.session_state.survey_responses)
        logging.info("Survey rendered. Submitted? %s", submitted)
        if submitted:
            st.session_state.survey_responses = survey_responses
            insert_survey_response(survey_responses)
            logging.info("Survey responses inserted: %s", survey_responses)
            st.session_state.stage = "chat"
            st.success("Survey submitted! You can now debate with the LLM about your responses.")
            st.rerun()


def show_chat_stage():
    # Custom scrollable message container
    st.markdown("""
    <style>
    .chat-messages {
        max-height: 70vh;
        overflow-y: auto;
        padding-bottom: 60px;  /* to avoid overlapping with fixed input */
    }
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #ddd;
        padding: 10px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

    # Messages inside scrollable div
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        if message["role"] in ["user", "assistant"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Fixed Input container, rendered LAST so it stays bottom fixed
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    prompt = st.chat_input("Type your message here...")
    st.markdown('</div>', unsafe_allow_html=True)

    idx = st.session_state.current_question_index
    if idx < len(survey_questions):
        st.markdown(f"**Give reasons for your answer to: {survey_questions[idx]}** You answered with: *{st.session_state.survey_responses[list(st.session_state.survey_responses.keys())[idx]]}*")

        if not any(m["role"] == "system" for m in st.session_state.messages):
            system_prompt = {
                "role": "system",
                "content": (
                    f"""You are a devil's advocate. Convince the user to pick an alternative option.\
                    For multiple choice questions, argue for options not picked.
                    Be assertive, relevant, and focus on each survey answer separately. Questions: {survey_questions[1:]}, \
                    User answered: {list(st.session_state.survey_responses.values())[1:]}."""
                )
            }
            st.session_state.messages.append(system_prompt)
            logging.info("Added system prompt.")

        if prompt:
            # Append only, do NOT re-render new user input here (this causes input shift)
            st.session_state.messages.append({"role": "user", "content": prompt})
            logging.info("User message added: %s", prompt)

            # Assistant reply
            stream = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            response = st.write_stream(stream)
            logging.info("Assistant response generated: %s", response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            insert_chat_log(user_message=prompt, assistant_response=response)
            st.session_state.current_question_index += 1

            st.rerun()
    else:
        st.success("You have completed the debate for all survey questions. Thank you!")
        logging.info("User finished all survey questions.")
        st.session_state.stage = "validate"
        st.rerun()

def show_validate_stage():
    st.header("Validate Your Responses and Related Chat")

    questions = survey_questions[1:]  # Skip name index or adjust as needed
    responses = st.session_state.survey_responses
    messages = st.session_state.messages

    # Let user pick which question to validate
    question_idx = st.selectbox("Select a survey question to validate", range(len(questions)), format_func=lambda i: questions[i])

    # Show the selected question & user response for validation
    st.markdown(f"### Question:\n{questions[question_idx]}")

    response_key = list(responses.keys())[question_idx + 1]  # +1 if skipping name index

    # Use a unique key for this text_area for session state tracking
    text_area_key = f"validated_answer_{question_idx}"

    validated_answer = st.text_area(
        label="Modify your answer if you were persuaded! Otherwise move onto the next question.",
        value=responses[response_key],
        key=text_area_key,
    )

    # Save button to persist validated answer to DB
    if st.button("Save validated answer"):
        # Retrieve updated answer from session state
        updated_answer = st.session_state[text_area_key]

        # Prepare document to insert/update in MongoDB collection 'validated_survey_responses'
        doc = {
            "question_index": question_idx,
            "question": questions[question_idx],
            "original_answer": responses[response_key],
            "validated_answer": updated_answer,
            "user": st.session_state.survey_responses.get("name", "anonymous"),
        }
        insert_validated_answers(doc)
        st.success("Your validated answer has been saved!")


    # Filter messages related to this question
    # (Assuming your message structure includes question index ref or you can filter by position)
    # Here, a simple heuristic: messages after the system prompt and belonging to that question index in sequence
    chat_start_idx = None
    system_prompts = [i for i, m in enumerate(messages) if m['role']=='system']

    if system_prompts:
        # Starting index of question-related chat (simplified)
        chat_start_idx = system_prompts[0] + 1 + question_idx * 2  # heuristic: 2 messages per Q? Adjust logic accordingly

    st.markdown("### Related chat messages:")
    if chat_start_idx is not None:
        # Show user-assistant chat pair for this question (adjust logic to match your chat structure)
        if chat_start_idx < len(messages):
            user_msg = messages[chat_start_idx]
            if user_msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(user_msg["content"])
            if chat_start_idx + 1 < len(messages) and messages[chat_start_idx + 1]["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(messages[chat_start_idx + 1]["content"])
        else:
            st.info("No chat messages found for this question.")
    else:
        st.info("No system prompt or chat messages found.")

    # Optionally, add navigation buttons Next/Prev or finish validation
    if st.button("Finish Validation"):
        st.success("Thank you for validating your responses!")
        # Update stage if needed
        # st.session_state.stage = "done"
        # Or trigger further logic


def main():
    initialize_session_state()
    if st.session_state.stage == "survey":
        st.title("Persuasive Power of Chatbots in Everyday Decisionmaking")
        show_survey_stage()
    if st.session_state.stage == "chat":
        st.header("The chatbot will now play devil's advocate on your survey responses.")
        show_chat_stage()
    if st.session_state.stage == "validate":
        st.header("Validate Your Survey Responses and Chat History")
        show_validate_stage()

if __name__ == "__main__":
    main()