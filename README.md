# NexusMind AI: Local Knowledge Assistant & RAG Framework
- Pikey's AI
- Install Python
- Install "requirements.txt"
- Install Ollama and Gemma4-e2b
- Run "rungem.bat"
- Enjoy

# Model AI Base
Gemma4-e2b

# Key Features

- Local RAG Architecture: Vectorized knowledge base enabling semantic context retrieval from local unstructured documents without third-party LLM privacy leaks.

- Asynchronous API Server: Asynchronous non-blocking streaming execution pipeline built on FastAPI and asyncio for scalable multi-request handling.

- Dynamic Web Intelligence: Integrated Tavily Search API to dynamically extend model capabilities with live web search when internal context is insufficient.

- High-Performance Vector Storage: Utilizes ChromaDB for efficient document chunking, dense vector indexing, and low-latency similarity queries.

- Stateful Memory Management: Dual-tiered context retention mechanism for managing short-term chat windows and long-term conversation states.

# Technical Architecture
                                    +--------------------+
                                    |    User Interface   |
                                    +---------+----------+
                                              |
                                              v
                                  +-----------------------+
                                  | FastAPI Backend Server |
                                  | (Async / SSE Stream)  |
                                  +-----------+-----------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
        +-------------------------+                       +--------------------------+
        | Dynamic Web Intelligence|                       | Local Context Retrieval  |
        |   (Tavily Search API)   |                       |    (ChromaDB Vector)     |
        +------------+------------+                       +------------+-------------+
                     |                                                 |
                     +------------------------+------------------------+
                                              |
                                              v
                                  +-----------------------+
                                  | Local Ollama Execution|
                                  |   (Llama 3 / Qwen)    |
                                  +-----------------------+
# IMG
<img width="2555" height="1298" alt="image" src="https://github.com/user-attachments/assets/31e137dd-c1a9-4d72-829d-9956a0b11559" />
<img width="2543" height="1302" alt="image" src="https://github.com/user-attachments/assets/a7e1b156-b53a-49fc-a48b-2215a58f9ee8" />
