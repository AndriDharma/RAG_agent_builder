import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content, FinishReason, SafetySetting
import vertexai.preview.generative_models as generative_models
import os
import requests
import google.auth.transport.requests
from google.oauth2 import service_account
import google.oauth2.id_token
import vertexai
from streamlit.runtime.scriptrunner import get_script_run_ctx
from google.cloud.sql.connector import Connector
import sqlalchemy
import google.cloud.logging
from google.cloud import secretmanager
import json
from sqlalchemy.dialects.postgresql import UUID
import uuid

from connectors.postgres import CloudSQLPostgresConnector
from langchain_postgres.vectorstores import PGVector
from langchain_google_vertexai import VertexAIEmbeddings

import logging
import traceback


# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\ASUS\Documents\Job\Datalabs\2025\service_account\dla-gen-ai-specialization-a03e18685e07.json" # Isi dengan Service Account

log_client = google.cloud.logging.Client()
log_client.setup_logging()

PROJECT_ID = os.environ.get('PROJECT_ID')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME')
ENGINE_NAME = os.environ.get('ENGINE_NAME')
SECRET_ID_DB = os.environ.get('SECRET_ID_DB')
driver = os.environ.get("DRIVER", "pg8000")
# PROJECT_ID = "844021890758"
# COLLECTION_NAME = "default_collection"
# ENGINE_NAME = "demo2-test_1736323106527"
# SECRET_ID_DB = "db-secret"

ctx = get_script_run_ctx()
session_global = ctx.session_id

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0,
    "top_p": 0.95
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
]

@st.cache_resource
def gemini_main():
    vertexai.init(project=PROJECT_ID, location="asia-southeast1")
    model = GenerativeModel(
    "gemini-1.5-pro-002",
    generation_config=generation_config,
    system_instruction="you are a customer service for retail product, please answer only based on the RAG result but don't say 'based on RAG result'"
    )
    return model

@st.cache_resource
def gemini_paraphrase():
    vertexai.init(project=PROJECT_ID, location="asia-southeast1")
    model = GenerativeModel(
    "gemini-1.5-pro-002",
    generation_config=generation_config
    )
    return model

def search_with_answer(query,session,agent):
    url_search = f"https://discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/global/collections/{COLLECTION_NAME}/engines/{agent}/servingConfigs/default_search:search"
    # API credential
    # credentials = service_account.Credentials.from_service_account_file(
    #     os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
    #     scopes=['https://www.googleapis.com/auth/cloud-platform']
    # )
    credentials, _ = google.auth.default()
    request_token = google.auth.transport.requests.Request()
    credentials.refresh(request_token)
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    # ngelakuin search file dulu baru summary, ini buat data searchnya
    if session == "":
        session = f"projects/{PROJECT_ID}/locations/global/collections/{COLLECTION_NAME}/engines/{agent}/sessions/-"
    else:
        pass
    request_data_search = {
        "query": query,
        "pageSize": 10,
        "queryExpansionSpec": {
            "condition": "AUTO"
        },
        "spellCorrectionSpec": {
            "mode": "AUTO"
        },
        "contentSearchSpec": {
            "snippetSpec": {
                "returnSnippet": True
            },
            "extractiveContentSpec": {
                "maxExtractiveAnswerCount": 1
            }
        },
        "session": session
    }
    request_search = requests.post(url=url_search, json=request_data_search,headers=headers)
    search = request_search.json()
    return search


st.title("Demo 2 Gen AI Specialization")
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
}
@st.cache_resource
def access_secret():
    # secret manager
    client = secretmanager.SecretManagerServiceClient()
    # Build the resource name of the secret version.
    name = f"projects/{PROJECT_ID}/secrets/{SECRET_ID_DB}/versions/latest"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    db_secret = json.loads(payload)
    return db_secret

@st.cache_resource
def embeddings_model():
    vertexai.init(project=PROJECT_ID, location="asia-southeast1")
    embeddings = VertexAIEmbeddings(model="text-multilingual-embedding-002")
    return embeddings


# global session for retrieving memory from db
if not "initialized" in st.session_state:
    st.session_state['session'] = session_global

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize feedback
if "get_feedback" not in st.session_state:
    st.session_state.get_feedback = False

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# feedback function
def save_feedback():
    user_text = str(st.session_state.messages[-2]["content"])
    ai_text = str(st.session_state.messages[-1]["content"])
    if st.session_state.feedback == 1: # 1 means thumbs up
        embed_text = embeddings.embed_query(user_text) # embed the question
        metadata = {
            "user_chat" : user_text,
            "ai_chat" :ai_text
        }
        texts = [user_text]
        embeddings_text = [embed_text]
        metadata = [metadata]
        vector_store.add_embeddings(
            texts=texts,
            embeddings=embeddings_text,
            metadatas=metadata
        )
    elif st.session_state.feedback == 0: # 0 means thumbs down
        feedback_text = st.text_input("Write your feedback here which consist of correct answer", "Feedback")
        embed_text = embeddings.embed_query(feedback_text) # embed the question
        metadata = {
            "user_chat" : user_text,
            "ai_chat" :feedback_text
        }
        texts = [user_text]
        embeddings_text = [embed_text]
        metadata = [metadata]
        vector_store.add_embeddings(
            texts=texts,
            embeddings=embeddings_text,
            metadatas=metadata
        )

    st.session_state.get_feedback = False


# Accept user input
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # db connection
        connector = Connector()
        db_secret = access_secret()


        # prepare vectorstore
        connector = CloudSQLPostgresConnector(
            instance_name=db_secret["INSTANCE_CONNECTION_NAME"],
            user=db_secret['DB_USER'],
            password=db_secret["DB_PASS"],
            database=db_secret["DB_NAME"],
            driver=driver
        )
        company_id = "datalabs"
        engine = connector.get_engine()
        embeddings = embeddings_model()
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=company_id,
            connection=engine,
            use_jsonb=True
        )
        gemini_main_model = gemini_main()
        gemini_paraphrase_model = gemini_paraphrase()

        # retrieve chat history
        history = []
        with engine.connect() as db_conn:
            # returning vacancy information for prompting
            query_history_data = f"""SELECT user_chat, ai_chat FROM demo_2_chat where session_id = '{session_global}' ORDER BY inserttimestamp ASC LIMIT 3"""
            query_history_result = db_conn.execute(sqlalchemy.text(query_history_data)).fetchall()
            for row in query_history_result:
                rows = row._mapping
                row_as_dict = dict(rows)
                history_temp = {
                    "user": row_as_dict['user_chat'],
                    "ai": row_as_dict['ai_chat']
                }
                history.append(history_temp)
        if history == []:
            search_paraphrase = prompt
        else:
            paraphrase_prompt = f""""
            Adjust the following question based on the historical chat. If the question doesn't relate to the historical chat, no adjustment is needed.
            
            here is the question '{prompt}'
            
            here is the historical chat
            {history}"""
            responses = gemini_paraphrase_model.generate_content(
                [paraphrase_prompt],
                safety_settings=safety_settings,
                stream=False
            )
            search_paraphrase = responses.text
        try:
            search = search_with_answer(session='',query=search_paraphrase,agent=ENGINE_NAME)
            reference = ''
            sources_link = []
            for i in range(len(search['results'])):
                reference +=f"[{i}]{search['results'][i]['document']['derivedStructData']['extractive_answers'][0]['content']}\n"
                gcs_uri = search['results'][i]['document']['derivedStructData']['link']
                # Extract data source
                source_exact = gcs_uri.replace("gs://","https://storage.cloud.google.com/")
                source_exact = source_exact.replace(" ","%20")
                sources_link.append(f"[{i}]{source_exact} \n\n")
            sources_link_join = ''.join(sources_link)
        except:
            logging.exception(str(traceback.format_exc()))
            reference = 'there is no data in the db'

        # retrieve user feedback based on questions
        results = vector_store.similarity_search_with_relevance_scores(query=search_paraphrase, k=3)
        threshold_similarity = 0.7
        check_duplicate_feedback = []
        reference_feedback = []
        for result, score in results:
            if score > threshold_similarity:
                if result.metadata['user_chat'] in check_duplicate_feedback:
                    pass
                else:
                    check_duplicate_feedback.append(result.metadata['user_chat'])
                    reference_json = {
                        "user_chat":result.metadata['user_chat'],
                        "ai_chat":result.metadata['ai_chat']
                    }
                    reference_feedback.append(reference_json)
        summarizer_prompt =f"""
        answer this question below based on RAG result and similar question and answer in the past but if the result is irrelevant or no data answer it like a customer support would be
        
        question: {prompt}

        similar question:
        {reference_feedback}

        RAG results:

        {reference}"""

        # rapihin jawaban hasil agent builder
        responses = gemini_main_model.generate_content(
            [summarizer_prompt],
            safety_settings=safety_settings,
            stream=True
        )
        hasil = []
        def streaming():
            for response in responses:
                hasil.append(response.text)
                yield response.text
        st.write_stream(streaming)
        hasil = ''.join(hasil)

        # update data on db
        insert_data = sqlalchemy.text("""INSERT INTO demo_2_chat (session_id, user_chat, ai_chat) values (:session_id, :user_chat, :ai)""")
        with engine.connect() as db_conn:
            # update job information
            bind_params = [
                sqlalchemy.sql.bindparam(key="session_id", value=uuid.UUID(session_global), type_=UUID(as_uuid=True)),
                sqlalchemy.sql.bindparam(key="user_chat", value=prompt),
                sqlalchemy.sql.bindparam(key="ai", value=hasil),
            ]
            db_conn.execute(insert_data.bindparams(*bind_params))
            db_conn.commit()
        # connector.close()
        # if engine:
        #     engine.dispose()

    st.session_state.messages.append({"role": "assistant", "content": hasil})
    st.session_state.get_feedback = True

if st.session_state.get_feedback:
    st.feedback("thumbs", key="feedback", on_change=save_feedback)