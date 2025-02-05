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
    git clone <YOUR_GITHUB_REPOSITORY_URL>
    cd streamlit
    ```
2.  **Run the Deployment Script:**

    ```bash
    sh deploy.sh
    ```

    The script will:

    *   Authenticate to GCP using the service account.
    *   Set the current project and region.
    *   Build the Docker image using cloud build.
    *   Push the Docker image to Artifact Registry.
    *   Deploy the application to Cloud Run.
    *   Set environment variables for the Cloud Run service.
    *   Allow unauthenticated access (optional, remove `--allow-unauthenticated` if you require authentication).

3.  **Access Your Application:**

    Once the deployment is complete, the script will print the URL of your Cloud Run service.  Open this URL in your browser to access your Streamlit application.