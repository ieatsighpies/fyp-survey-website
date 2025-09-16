# fyp-survey-website

To startup:

1. in terminal, run 'uv sync'
2. start up venv (ie. 'source .venv/bin/activate')
3. Currently using mongoDB community, start up from homebrew: brew services start mongodb-community@8.0
4. run this command: uv run streamlit run main.py
5. To stop, remember to run 'brew services stop mongodb-community@8.0'

mongoexport to see entries in collections: mongoexport --collection=chat_logs --db=survey_db
