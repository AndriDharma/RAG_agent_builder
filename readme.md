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