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
import re
# import sqlalchemy
# from google.cloud.sql.connector import Connector

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\ASUS\Documents\Job\Datalabs\2025\service_account\dla-gen-ai-specialization-a03e18685e07.json" # Isi dengan Service Account

PROJECT_ID = "844021890758"
COLLECTION_NAME = "default_collection"
ENGINE_NAME = "demo2-test_1736323106527"

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
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
]

@st.cache_resource
def gemini_model_rapihin():
    vertexai.init(project=PROJECT_ID, location="asia-southeast1")
    model = GenerativeModel(
    "gemini-1.5-pro-002",
    generation_config=generation_config,
    system_instruction="you are a customer service for retail product, please answer only based on the RAG result but don't say 'based on RAG result'"
    )
    return model

@st.cache_resource
def gemini_model_form():
    vertexai.init(project=PROJECT_ID, location="asia-southeast1")
    model = GenerativeModel(
    "gemini-1.5-flash-001",
    generation_config=generation_config
    )
    return model

def search_with_answer(query,session,agent):
    url_search = f"https://discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/global/collections/{COLLECTION_NAME}/engines/{agent}/servingConfigs/default_search:search"
    # API credential
    credentials = service_account.Credentials.from_service_account_file(
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
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

# global session for retrieving memory from db
if not "initialized" in st.session_state:
    st.session_state['session'] = session_global

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        model_rapihin = gemini_model_rapihin()
        model_form = gemini_model_form()
        search = search_with_answer(session='',query=prompt,agent=ENGINE_NAME)
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

        summarizer_prompt =f"""
        answer this question below based on RAG result and use citation [number] on the answer and say i dont know if there isnt any answer on the references
        
        question: {prompt}
        
        RAG results:

        {reference}"""

        # rapihin jawaban hasil agent builder
        responses = model_rapihin.generate_content(
            [summarizer_prompt],
            safety_settings=safety_settings,
            stream=False
        )
        hasil_mentah = responses.text
        sources_fix = []
        x = 1
        for i in range(len(sources_link)):
            if re.search(f"[{i}]", sources_link[i]):
                data_temp = f"{sources_link[i].replace(f'{i}',f'{x}')} \n\n"
                hasil_mentah= hasil_mentah.replace(f'[{i}]',f'[{x}]')
                sources_fix.append(data_temp)
                x += 1
            else:
                pass
        sources_link_join = ''.join(sources_link)
        
        sources_link_join_final = f"Here are the references for the AI\n\n{sources_link_join}"
        st.write(f"\n{sources_link_join_final}")
        final_result = f"{hasil_mentah}\n {sources_link_join_final}"

    st.session_state.messages.append({"role": "assistant", "content": final_result})