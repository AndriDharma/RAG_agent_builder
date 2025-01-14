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
# import sqlalchemy
# from google.cloud.sql.connector import Connector

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\ASUS\Documents\Job\Datalabs\2025\service_account\dla-gen-ai-specialization-a03e18685e07.json" # Isi dengan Service Account

# Ganti dengan ID proyek Anda
PROJECT_ID = "712154177458"

# Ganti dengan nama koleksi Anda
COLLECTION_NAME = "default_collection"

INSTANCE_CONNECTION_NAME = "wom-gen-ai:asia-southeast2:postgres-wom"
DB_USER = "postgres"
DB_PASS = "kCg@lK=MB*3Jih,D"
DB_NAME = "postgres"

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
    "gemini-1.5-flash-001",
    generation_config=generation_config
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

# @st.cache_resource
# def gemini_model_context():
#     vertexai.init(project=PROJECT_ID, location="asia-southeast1")
#     model = GenerativeModel(
#     "gemini-1.5-flash-001",
#     generation_config=generation_config
#     )
#     return model

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
    # ini bagian api call untuk summary
    url_answer = f"https://discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/global/collections/{COLLECTION_NAME}/engines/{agent}/servingConfigs/default_search:answer"

    request_data_answer = {
        "query": {
            "text": query,
            "queryId": search['sessionInfo']['queryId']
        },
        "session": search['sessionInfo']['name'],
        "relatedQuestionsSpec": {
            "enable": True
        },
        "answerGenerationSpec": {
            "ignoreAdversarialQuery": True,
            "ignoreNonAnswerSeekingQuery": True,
            "ignoreLowRelevantContent": True,
            "includeCitations": True,
            "promptSpec": {
                "preamble": """Anda adalah agent chatbot internal untuk perusahaan WOM Finance Jawablah dalam bahasa indonesia jangan dengan bahasa inggris,untuk jawaban yang tidak ditemukan harap balas dengan "Jawaban tidak ditemukan, silahkan menghubungi tim OPP pada email OPP@wom.co.id. Terima Kasih" """
            },
            "modelSpec": {
                "modelVersion": "gemini-1.5-flash-001/answer_gen/v2"
            }
        }
    }

    request_answer = requests.post(url_answer, json=request_data_answer,headers=headers)
    answer = request_answer.json()

    return answer

# def getconn():
#     conn = connector.connect(
#         INSTANCE_CONNECTION_NAME,
#         "pg8000",
#         user=DB_USER,
#         password=DB_PASS,
#         db=DB_NAME
#     )
#     return conn

st.title("WOM Finance Chatbot Assitant")
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
        # model_context = gemini_model_context()

        # #connecting to db for memory
        # connector = Connector()
        # pool = sqlalchemy.create_engine(
        # "postgresql+pg8000://",
        # creator=getconn,
        # )
        # with pool.connect() as db_conn:
        #     history = db_conn.execute(sqlalchemy.text(f"SELECT id FROM session WHERE streamlit_session='{session_global}' LIMIT 1")).fetchall()
        #     db_conn.close()
        # engine_name = "wom-test_1721697862665"

        #commenting memory for now because it makes the agent builder worse, it would be better if we add button for activating memory
        # #check session from db for memory
        # if len(history) >= 1:
        #     with pool.connect() as db_conn:
        #         memory = db_conn.execute(sqlalchemy.text(f"SELECT agent_builder_session FROM session WHERE streamlit_session='{session_global}' LIMIT 1")).fetchone()
        #         db_conn.close()
        #     hasil_mentah = search_with_answer(session=str(memory[0]),query=prompt,agent=engine_name)

        # else:
        #     hasil_mentah = search_with_answer(session='',query=prompt,agent=engine_name)
        #     with pool.connect() as db_conn:
        #         db_conn.execute(sqlalchemy.text(f"INSERT INTO session (streamlit_session, agent_builder_session) VALUES ('{session_global}', '{hasil_mentah['session']['name']}')"))
        #         db_conn.commit()
        #         db_conn.close()
        
        # kalau gada jawaban langsung jawab "Jawaban tidak ditemukan, silahkan menghubungi tim OPP pada email OPP@wom.co.id. Terima Kasih"
        try:
            engine_name = "wom-test_1721697862665"
            hasil_mentah = search_with_answer(session='',query=prompt,agent=engine_name)
            # Mapping apakah nanya formulir atau ga
            formulir_genai = model_rapihin.generate_content(
                ["Apakah pertanyaan tersebut bertanya mengenai formulir? jika ya maka berikan output '1' dan jika tidak maka berikan output '0' Berikut pertanyaannya \n", prompt],
                safety_settings=safety_settings,
                stream=False
            )
            # extract data dari hasil search
            answer_list = []
            sources_all = []
            for i in range(len(hasil_mentah['answer']['citations'])):
                sources = []
                for x in range(len(hasil_mentah['answer']['citations'][i]['sources'])):
                    sources.append(int(hasil_mentah['answer']['citations'][i]['sources'][x]['referenceId']))
                    sources_all.append(int(hasil_mentah['answer']['citations'][i]['sources'][x]['referenceId']))
                if i == 0:
                    index = int(hasil_mentah['answer']['citations'][i]['endIndex'])
                    answer_list.append(hasil_mentah['answer']['answerText'][:index] + f'{sources}')
                else:
                    start_index = int(hasil_mentah['answer']['citations'][i]['startIndex'])
                    end_index = int(hasil_mentah['answer']['citations'][i]['endIndex'])
                    answer_list.append(hasil_mentah['answer']['answerText'][start_index:end_index] + f'{sources}')
            
            # mapping sources to gcs link
            myset = set(sources_all)
            mynewlist = list(myset)
            sources_link = []
            for x in mynewlist:
                gcs_uri = hasil_mentah['answer']['references'][x]['chunkInfo']['documentMetadata']['uri']
                doc_page = hasil_mentah['answer']['references'][x]['chunkInfo']['documentMetadata']['pageIdentifier']
                # Extract data source
                source_exact = gcs_uri.replace("gs://","https://storage.cloud.google.com/")
                source_exact = source_exact.replace(" ","%20")
                source_exact = f"{source_exact}#page={doc_page}"
                sources_link.append(f"[{x}]{source_exact} \n\n")
            sources_link_join = ''.join(sources_link)

            # rapihin jawaban hasil agent builder
            answer_join = ''.join(answer_list)
            responses = model_rapihin.generate_content(
                ["rapihkan text berikut tanpa menghilangkan referensi seperti [0] dan gunakan markdown \n", answer_join],
                safety_settings=safety_settings,
                stream=True
            )
            hasil = []
            def streaming():
                for response in responses:
                    hasil.append(response.text)
                    yield response.text
            st.write_stream(streaming)
            # nambahin link sources sama link formulir di hasil akhir
            if '0' in formulir_genai.text:
                sources_link_join_final = f"Harap cross check dari referensi yang diberikan oleh AI dibawah ini\n{sources_link_join}"
                st.write(f"\n{sources_link_join_final}")
                hasil = ''.join(hasil)
                final_result = f"{hasil}\n {sources_link_join_final}"
            else:
                sources_link_join_final = f"Harap cross check dari referensi yang diberikan oleh AI dibawah ini\n{sources_link_join}"
                link_formulir = "\nBerikut Link untuk formulir tersebut https://w2u.wom.co.id/w2u/public/login"
                st.write(link_formulir)
                st.write(f"\n{sources_link_join_final}")
                hasil = ''.join(hasil)
                final_result = f"{hasil}\n {link_formulir}\n \n {sources_link_join_final}"
        except:
            final_result = "Jawaban tidak ditemukan, silahkan menghubungi tim OPP pada email OPP@wom.co.id. Terima Kasih"
            st.write(final_result)
        
        #commenting all memory for now because it's still bad
        # #insert chat history
        # user_chat_history_str =  prompt.replace('\'','')
        # ai_chat_history_str =  final_result.replace('\'','')
        # ai_chat_history_str =  ai_chat_history_str.replace('*','')

        # with pool.connect() as db_conn:
        #     db_conn.execute(sqlalchemy.text(f"INSERT INTO chat_history (session_id, user_chat, ai_response) VALUES ('{hasil_mentah['session']['name']}', '{user_chat_history_str}', '{ai_chat_history_str}')"))
        #     db_conn.commit()
        #     db_conn.close()

        # if st.button('ask me follow up question:'):
        #     st.write("halo")

    st.session_state.messages.append({"role": "assistant", "content": final_result})