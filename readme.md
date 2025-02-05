# RAG with Agent Builder Search and Streamlit

This repository contains a Retrieval-Augmented Generation (RAG) application that utilizes Google Cloud's Agent Builder Search as its knowledge base. The application offers a user-friendly interface built with Streamlit and is deployed on Google Cloud Run. It incorporates memory management and collects user feedback, which is stored in Cloud SQL (PostgreSQL) and leveraged with `pgvector` to enhance future query responses.

## Features

- **Retrieval-Augmented Generation (RAG):** Combines a retrieval system with a generative model to provide contextually relevant and accurate answers.
- **Agent Builder Search as Knowledge Base:** Leverages the power of Agent Builder Search to access and retrieve information from a vast database.
- **Streamlit for Frontend and Backend:** Utilizes Streamlit for both the user interface and the application logic, offering a streamlined development experience.
- **Cloud Run Deployment:** Deploys the application on Google Cloud Run for scalability, reliability, and managed infrastructure.
- **Memory Management:** Stores conversation history in Cloud SQL (PostgreSQL) for context awareness
- **Secret Manager Integration:** Securely stores sensitive information like database credentials using Google Cloud Secret Manager.
- **User Feedback Collection:** Captures user feedback (questions, answers, and ratings) to improve the system's accuracy and effectiveness.
- **Cloud SQL (PostgreSQL) for Data Storage:** Stores user interactions and feedback in a robust Cloud SQL PostgreSQL database.
- **`pgvector` for Semantic Search:** Uses the `pgvector` extension in PostgreSQL to perform semantic similarity searches on historical questions and answers, enabling the system to learn from past interactions.

## Architecture

The application follows a microservices-oriented architecture with clear separation of concerns:

1.  **User Interface (Streamlit):** The frontend, built with Streamlit, handles user interaction, input, and output display.
2.  **Application Logic (Streamlit Backend):** Streamlit also serves as the backend, handling the application logic, interacting with other services, and managing the RAG process.
3.  **RAG Component:**
    -   **Retriever:** Interacts with Agent Builder Search to retrieve relevant documents based on the user's query.
    -   **Generator:** Utilizes a Large Language Model (LLM) to generate a response based on the retrieved documents and the user's query.
4.  **Agent Builder Search:** Acts as the knowledge base, providing structured and unstructured data for the retrieval process.
5.  **Memory Management:** This module ensures efficient handling of in-memory data by paraphrasing historical question for optimizing token.
6.  **Feedback Management:**
    -   **Feedback Collection API:** Collects feedback data from the user interface.
    -   **Data Storage:** Stores the feedback in Cloud SQL (PostgreSQL).
    -   **`pgvector` Search:** Implements the `pgvector` extension within PostgreSQL to enable semantic similarity search on historical feedback data.
7.  **Cloud SQL (PostgreSQL):** A managed relational database service that stores user interactions, feedback data.
8.  **Cloud Run:** A fully managed serverless platform that hosts the Streamlit application, providing automatic scaling and handling infrastructure concerns.

## Code Snippets
<img src="https://github.com/AndriDharma/RAG_agent_builder/blob/main/images/1.png" alt="Imports Snippet" width="600">

This section imports all the necessary libraries and modules for the application:

*   **streamlit as st:**  Used for creating the interactive web interface.
*   **vertexai:** The core Google Cloud Vertex AI SDK for interacting with models.
*   **vertexai.generative_models:** Specific classes for working with generative models like Gemini.  This includes `GenerativeModel`, `Part`, `Content`, `FinishReason`, and `SafetySetting`.
*    **vertexai.preview.generative_models as generative_models:** Accessing preview features of generative models from Vertex AI.
*   **os:** Provides a way to interact with the operating system, mainly to retrieve environment variables.
*   **requests:** A library for making HTTP requests, used here potentially for querying external APIs or services.
*   **google.auth.\*:** Libraries from Google Auth to manage authentication and authorization to Google Cloud Services.
*   **streamlit.runtime.scriptrunner:** Utility for managing Streamlit script execution context.
*   **google.cloud.sql.connector & sqlalchemy:** Used for connecting to and interacting with Google Cloud SQL databases, using SQLAlchemy as an ORM.
*   **google.cloud.logging:** Logging is used to debug and monitor the application
*   **google.cloud.secretmanager:**  Used for securely accessing secrets stored in Google Cloud Secret Manager, such as database credentials.
*   **json:**  Handles JSON data for parsing and serialization.
*   **sqlalchemy.dialects.postgresql.UUID & uuid:** These are for working with UUIDs (Universally Unique Identifiers) in PostgreSQL databases.
*   **connectors.postgres.CloudSQLPostgresConnector:** A custom connector for simplifying connections to Cloud SQL PostgreSQL instances.
*   **langchain_postgres.vectorstores.PGVector:**  Used for storing and retrieving vector embeddings from a PostgreSQL database, likely using a vector extension.
*   **langchain_google_vertexai.VertexAIEmbeddings:** Used for embedding text using the Vertex AI embedding models.
*   **logging & traceback:** These are for logging errors and debugging the application.


<img src="https://github.com/AndriDharma/RAG_agent_builder/blob/main/images/2.png" alt="Environment Variables Snippet" width="600">

### This snippet initializes the logging client and retrieves environment variables.  Using environment variables is crucial for security and configuration:

*   **Logging Setup:**  The first two lines initialize the Google Cloud Logging client, allowing the application to send logs to Google Cloud Logging for monitoring and debugging.
*   **Environment Variables:**
    *   `PROJECT_ID`: Your Google Cloud Project ID.
    *   `COLLECTION_NAME`: The name of the collection in your discovery engine.
    *   `ENGINE_NAME`: The name of the search engine in your discovery engine.
    *   `SECRET_ID_DB`: The ID of the secret in Google Cloud Secret Manager that stores your database credentials.
    *   `driver`: Specifies the database driver to use.  It defaults to "pg8000".

<img src="https://github.com/AndriDharma/RAG_agent_builder/blob/main/images/3.png" alt="Gemini Configuration Snippet" width="600">

This section configures and initializes the Gemini model using the `vertexai` library:

*   **`generation_config`:** Defines the parameters for text generation:
    *   `max_output_tokens`:  The maximum number of tokens the model can generate in its response.
    *   `temperature`: Controls the randomness of the output.  Higher values (e.g., 1.0) lead to more random and creative outputs, while lower values (e.g., 0.2) produce more predictable and conservative outputs.
    *   `top_p`:  Nucleus sampling.  The model considers the most probable tokens whose probabilities add up to `top_p`. A lower `top_p` leads to more focused and less diverse output.

*   **`safety_settings`:** Defines the safety settings to filter responses.  The categories include hate speech, dangerous content, sexually explicit content, and harassment.  The `HarmBlockThreshold` is set to `BLOCK_MEDIUM_AND_ABOVE`, meaning that responses that are considered medium or highly harmful in these categories will be blocked.

*   **`gemini_main()` Function:** This function initializes the Gemini model with specific configuration for retail customer service question answering based on RAG and cached the function with streamlit.
    *   `vertexai.init()`: Initializes the Vertex AI SDK with your `PROJECT_ID` and location.
    *   `GenerativeModel()`: Creates an instance of the Gemini model, specifying the model name (`gemini-1.5-pro-002`), the `generation_config`, and a `system_instruction`.
    *    `system_instruction`: Sets the behavior of the model

*   **`gemini_paraphrase()` Function:** Initializes Gemini model for paraphrase function

*   **`@st.cache_resource`:** This decorator from Streamlit caches the output of the function.  This is *critical* for performance because it prevents the model from being re-initialized on every rerun of the Streamlit app.  Model initialization can be slow.

<img src="https://github.com/AndriDharma/RAG_agent_builder/blob/main/images/4.png" alt="Search Function Snippet" width="600">

This function handles the search and retrieval of relevant documents:

*   **`search_with_answer(query, session, agent)`:** Takes the user's `query`, a `session` ID, and an `agent` identifier as input.
*   **API Authentication (Commented Out):** The code commented out are for api authentication.
*   **Session Management:**
    *   If `session` is empty, it constructs a new session identifier.
    *   Otherwise, it reuses the existing session.
*   **`request_data_search`:** This dictionary defines the search request payload:
    *   `query`: The user's search query.
    *   `pageSize`: The maximum number of results to return (set to 10).
    *   `queryExpansionSpec`: Enables automatic query expansion.
    *   `spellCorrectionSpec`: Enables automatic spell correction.
    *   `contentSearchSpec`:
        *   `snippetSpec`:  Requests document snippets to be returned.
        *   `extractiveContentSpec`: Requests the extraction of a single answer from the document.
    *   `session`:  Includes the session identifier.
*    **requests.post:** This performs an HTTP POST request to search the query, with the specified `url`, `json` payload (`request_data_search`)
*   **Returns:** The function returns the JSON response from the search API.

<img src="https://github.com/AndriDharma/RAG_agent_builder/blob/main/images/5.png" alt="Access Secret Snippet" width="600">

This function securely retrieves secrets (like database credentials) from Google Cloud Secret Manager and initializes the Vertex AI embeddings model:

*   **`access_secret()`:** This function retrieves the database secret from Google Cloud Secret Manager.
*   **`secretmanager.SecretManagerServiceClient()`:** Creates a client for interacting with the Secret Manager API.
*   **`name`:** Constructs the resource name of the secret to retrieve. It uses the `PROJECT_ID` and `SECRET_ID_DB` environment variables.
*   **`client.access_secret_version()`:** Retrieves the secret version.
*   **`payload`:** Extracts the secret data from the response and decodes it from bytes to a UTF-8 string.
*   **`json.loads()`:** Parses the JSON string into a Python dictionary (`db_secret`).
*   **Returns:** The function returns the `db_secret` dictionary containing the database credentials.
*   **`@st.cache_resource`:** Caches the output of this function to avoid repeated calls to Secret Manager.
*   **`embeddings_model()`:**  This function initializes the Vertex AI embeddings model.
*   **`vertexai.init()`:** Initializes the Vertex AI SDK with your `PROJECT_ID` and location.
*   **`VertexAIEmbeddings()`:** Creates an instance of the Vertex AI embeddings model, specifying the model name (`text-multilingual-embedding-002`).
*   **Returns:**  The function returns the `embeddings` object.
*   **`@st.cache_resource`:** Caches the embeddings model instance to improve performance.

## Prerequisites

Before you begin, ensure you have the following:

*   **A Google Cloud Platform (GCP) account:**  If you don't have one, you can sign up for a free trial at [https://cloud.google.com/](https://cloud.google.com/).
*   **The Google Cloud SDK (gcloud CLI) installed and configured:**  Follow the instructions at [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).
*   **Python 3.7 or higher installed:** This is required for Streamlit and the Agent Builder SDK.
*   **Git installed:**  Used for cloning the repository.

## GCP Setup

These steps need to be performed in your GCP project.

1.  **Create a GCP Project:**
    *   If you don't already have one, create a new GCP project in the Cloud Console: [https://console.cloud.google.com/projectcreate]
    *   Note your **Project ID**. This will be used in the `deploy.sh` script (see below).
    *   In the Cloud Console dashboard, note down your **Project Number** which we will use to create a service account with permission to access resources in the Google Cloud project.

2.  **Enable Necessary APIs:**

    Enable the following APIs in the Cloud Console:

    *   Vertex AI API
    *   Cloud SQL Admin API
    *   Cloud Run API
    *   Agent Builder API
    *   Secret Manager API
    *   Cloud Storage API
    *   Cloud Build API
    *   Artifact Registry API

    You can enable these APIs by searching for them in the API Library: [https://console.cloud.google.com/apis/library]

3.  **Create a Cloud SQL Instance:**

    *   Go to the Cloud SQL section in the Cloud Console: [https://console.cloud.google.com/sql]
    *   Create a new Cloud SQL instance.  Choose:
        *   **MySQL** as the database engine.  (This is the assumed database type for this project)
        *   **Shared core (flexible)** instance type.
        *   Minimum **600MB** of storage.
    *   Take note of the **Instance Connection Name**.  It will look like `[PROJECT_ID]:[REGION]:[INSTANCE_NAME]`.  You'll need this when creating secret for cloud sql credentials

4.  **Create a Service Account:**

    *   Go to the IAM & Admin > Service Accounts section in the Cloud Console: [https://console.cloud.google.com/iam-admin/serviceaccounts]
    *   Create a new service account.
    *   Grant the following roles to the service account:
        *   **Vertex AI Admin**
        *   **Secret Manager Admin**
        *   **Storage Admin**
        *   **Cloud SQL Client** (Important for Cloud Run to access Cloud SQL)
    *   Download the JSON key file for the service account.  This file will be used by Cloud Run to authenticate. Take note of the service account email. The service account ID is in the following form [NAME@PROJECT_ID.iam.gserviceaccount.com]

5.  **Create Secrets in Secret Manager:**

    *   Go to the Secret Manager section in the Cloud Console: [https://console.cloud.google.com/security/secret-manager]
    *   Create the following secrets:
        *   **`db-secret` (SECRET_ID_DB):** Store the database credentials (username, password, database name) in a secure format (e.g., a JSON string). The application will need to parse these credentials.
        *   Ensure the Service Account you created in step 4 has the Secret Manager Secret Accessor role for these secrets.  You can grant this role to the service account in the IAM section of the Cloud Console.

6.  **Create Artifact Registry:**

    *   Go to the Artifact Registry section in the Cloud Console: [https://console.cloud.google.com/artifacts]
    *   Create the following repository:
        * **Name** Name of your repository for storing images
        * **Format** Choose Docker for your format
        * **Location type** In this case we use asia-southeast2
        * Leaves all other option as default

## Deployment Steps

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/AndriDharma/RAG_agent_builder
    cd streamlit
    ```
2.  **Run the Deployment Script:**

    ```bash
    sh deploy.sh
    ```

    The script will:

    *   Authenticate to GCP using your local credentials
    *   Set the current project and region.
    *   Build the Docker image using cloud build.
    *   Push the Docker image to Artifact Registry.
    *   Deploy the application to Cloud Run.
    *   Set environment variables for the Cloud Run service.
    *   Allow unauthenticated access (optional, remove `--allow-unauthenticated` if you require authentication).

3.  **Access Your Application:**

    Once the deployment is complete, the script will print the URL of your Cloud Run service.  Open this URL in your browser to access your Streamlit application.