from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from ..core.config import settings
from .vector_db import vector_db
from typing import List, Dict, Any, Generator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        logger.info(f"Initializing LLM Service. Provider: {settings.LLM_PROVIDER}, Model: {settings.LLM_MODEL}")
        
        api_key = settings.LLM_API_KEY
        if not api_key:
            raise ValueError(f"API key for {settings.LLM_PROVIDER} is missing in .env")
            
        if settings.LLM_PROVIDER == "groq":
            self.llm = ChatGroq(
                groq_api_key=api_key,
                model_name=settings.LLM_MODEL,
                temperature=0.2,
                streaming=True
            )
        elif settings.LLM_PROVIDER == "gemini":
            from langchain_community.chat_models.openai import ChatOpenAI
            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                openai_api_base=settings.LLM_BASE_URL,
                model_name=settings.LLM_MODEL,
                temperature=0.2,
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    def stream_response(self, query: str, top_k: int = 5) -> Generator[str, None, None]:
        try:
            # 1. Retrieve context
            matching_chunks = vector_db.search(query, top_k=top_k)
            
            # 2. Build context string
            if not matching_chunks:
                context_text = "No document is currently uploaded. Please answer using your own general knowledge."
            else:
                context_text = "\n\n---\n\n".join([
                    f"Source: {h['filename']} (Page {h['page_number']})\nContent: {h['text']}" 
                    for h in matching_chunks
                ])

            # 3. Message template structure
            messages = [
                SystemMessage(content="""You are a professional Enterprise AI Assistant.
You will be asked questions about the uploaded document context, or general/outside questions.

Follow these strict rules:
1. First, check if the user's question represents a general/outside query (e.g. asking about sports, science, history, coding help, general assistance, math, or translation) not directly referencing the uploaded document facts. If it is an outside question, you MUST ignore the document context entirely. Answer it directly and accurately using your general knowledge.
2. If the user's question is explicitly seeking info from the provided document context, answer it using only the context facts.
3. Under no circumstances should you refuse to answer general knowledge/outside questions by stating that you don't know or that the context does not mention them. Always answer them using your general knowledge."""),
                HumanMessage(content=f"Document Context:\n{context_text}\n\nUser Question: {query}")
            ]

            # 4. Stream using LangChain
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            yield f"Error during generation: {str(e)}"

    def generate_response(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Synchronous version for compatibility."""
        try:
            matching_chunks = vector_db.search(query, top_k=top_k)
            if not matching_chunks:
                context_text = "No document is currently uploaded."
            else:
                context_text = "\n\n".join([f"Page {h['page_number']}: {h['text']}" for h in matching_chunks])
            
            messages = [
                SystemMessage(content="""You are a professional Enterprise AI Assistant.
You will be asked questions about the uploaded document context, or general/outside questions.

Follow these strict rules:
1. First, check if the user's question represents a general/outside query (e.g. asking about sports, science, history, coding help, general assistance, math, or translation) not directly referencing the uploaded document facts. If it is an outside question, you MUST ignore the document context entirely. Answer it directly and accurately using your general knowledge.
2. If the user's question is explicitly seeking info from the provided document context, answer it using only the context facts.
3. Under no circumstances should you refuse to answer general knowledge/outside questions by stating that you don't know or that the context does not mention them. Always answer them using your general knowledge."""),
                HumanMessage(content=f"Document Context:\n{context_text}\n\nUser Question: {query}")
            ]
            
            response = self.llm.invoke(messages)
            return {
                "answer": response.content,
                "sources": matching_chunks,
                "context_used": bool(matching_chunks)
            }
        except Exception as e:
            return {"answer": str(e), "sources": [], "context_used": False}

llm_service = LLMService()
