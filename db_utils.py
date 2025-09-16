import streamlit as st
from pymongo import MongoClient, errors
import pprint

# Connection parameters (replace as needed)
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "survey_db"
#collections
SURVEY_COLLECTION = "survey_responses"
CHAT_COLLECTION = "chat_logs"
VALIDATE_ANSWERS_COLLECTION = "validate_answers"
# JSON schema validator for your survey collection
SURVEY_SCHEMA_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "name", "simple_qn_1", "simple_qn_2",
            "medium_qn_1", "medium_qn_2",
            "complex_qn_1", "complex_qn_2"
        ],
        "properties": {
            "name": {"bsonType": "string"},
            "simple_qn_1": {"bsonType": "string"},
            "simple_qn_2": {"bsonType": "string"},
            "medium_qn_1": {"bsonType": "string"},
            "medium_qn_2": {"bsonType": "string"},
            "complex_qn_1": {"bsonType": "string"},
            "complex_qn_2": {"bsonType": "string"}
        }
    }
}

@st.cache_resource
def get_mongo_client():
    env = st.secrets.get("environment", "development").lower()
    mongo_uri = None
    if env == "production":
        mongo_uri = st.secrets["production"]["mongo_uri"]
    else:
        mongo_uri = st.secrets["development"]["mongo_uri"]

    client = MongoClient(mongo_uri)
    return client


def create_collection_if_not_exists(db, collection_name, validator=None):
    if collection_name not in db.list_collection_names():
        if validator:
            db.create_collection(
                collection_name,
                validator=validator,
                validationLevel="strict",
                validationAction="error"
            )
        else:
            db.create_collection(collection_name)
    return db[collection_name]

@st.cache_data(ttl=600)
def get_survey_collection():
    client = get_mongo_client()
    db = client[MONGO_DB]
    return create_collection_if_not_exists(db, SURVEY_COLLECTION, SURVEY_SCHEMA_VALIDATOR)

@st.cache_data(ttl=600)
def get_chat_collection():
    client = get_mongo_client()
    db = client[MONGO_DB]
    # Chat logs can have a simple schema or no validation
    return create_collection_if_not_exists(db, CHAT_COLLECTION)

@st.cache_data(ttl=600)
def get_validated_collection():
    client = get_mongo_client()
    db = client[MONGO_DB]
    # Chat logs can have a simple schema or no validation
    return create_collection_if_not_exists(db, VALIDATE_ANSWERS_COLLECTION)

def insert_survey_response(responses):
    try:
        client = get_mongo_client()
        db = client.get_default_database() #database is specified in the URI
        collection = db[SURVEY_COLLECTION]
        result = collection.insert_one(dict(responses))
        return result.inserted_id
    except errors.WriteError as e:
        print(f"Survey insert failed: {e}")
        return None


def insert_chat_log(user_message, assistant_response):
    try:
        client = get_mongo_client()
        db = client.get_default_database() #database is specified in the URI
        collection = db[CHAT_COLLECTION]
        doc = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "timestamp": None  # optionally add datetime.datetime.utcnow()
        }
        result = collection.insert_one(doc)
        return result.inserted_id
    except errors.WriteError as e:
        print(f"Chat log insert failed: {e}")
        return None

def insert_validated_answers(responses: dict):
    try:
        client = get_mongo_client()
        db = client.get_default_database() #database is specified in the URI
        collection = db[VALIDATE_ANSWERS_COLLECTION]
        result = collection.insert_one(responses)
        return result.inserted_id
    except errors.WriteError as e:
        print(f"Survey insert failed: {e}")
        return None

def show_all_documents():
    client = get_mongo_client()
    db = client.get_default_database()

    collections = db.list_collection_names()
    print(f"Collections in database 'survey_db': {collections}\n")

    for coll_name in collections:
        print(f"Documents in collection '{coll_name}':")
        collection = db[coll_name]
        cursor = collection.find()
        for doc in cursor:
            pprint.pprint(doc)
        print("-" * 40)

def delete_all_documents():
    client = get_mongo_client()
    db = client.get_default_database()

    collections = db.list_collection_names()
    for coll_name in collections:
        collection = db[coll_name]
        result = collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from collection '{coll_name}'")