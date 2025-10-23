import os 
from dotenv import load_dotenv
from google.adk.agents import BaseAgent, LlmAgent
from typing_extensions import override
from typing import Callable
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator

from google import genai
from ..config import DEFAULT_TOP_K, DEFAULT_CANDIDATES, DEFAULT_VECTOR_SEARCH_INDEX, DEFAULT_ATLAS_SEARCH_INDEX
from config.config import get_settings
from ..tools.reranking import rerank_documents
from ..tools.search_from_database import find_similar_information_by_hybrid_search
from ..tools.embedding import get_embedding
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAG_Agent(BaseAgent):
    answer_generator : LlmAgent
    top_k : int = DEFAULT_TOP_K
    candidates : int = DEFAULT_CANDIDATES
    vector_search_index : str = DEFAULT_VECTOR_SEARCH_INDEX
    atlas_search_index : str = DEFAULT_ATLAS_SEARCH_INDEX
    disallow_transfer_to_parent : bool = True
    model : str = get_settings().rag_model
    get_embedding : Callable = get_embedding
    search_from_database : Callable = find_similar_information_by_hybrid_search
    rerank_documents : Callable = rerank_documents
    
    def __init__(self, 
        name: str, 
        answer_generator: LlmAgent,
        top_k: int = DEFAULT_TOP_K,
        candidates: int = DEFAULT_CANDIDATES,
        vector_search_index: str = DEFAULT_VECTOR_SEARCH_INDEX,
        atlas_search_index: str = DEFAULT_ATLAS_SEARCH_INDEX,
        model: str = get_settings().rag_model,
        get_embedding: Callable = get_embedding,
        search_from_database: Callable = search_from_database,
        rerank_documents: Callable = rerank_documents
        ):
        super().__init__(
            name = name,
            answer_generator = answer_generator,
            top_k = top_k,
            candidates = candidates,
            vector_search_index = vector_search_index,
            atlas_search_index = atlas_search_index,
            model = model,
            get_embedding = get_embedding,
            search_from_database = search_from_database,
            rerank_documents = rerank_documents,
        )
        
        
    @override
    async def _run_async_impl(self, ctx : InvocationContext) -> AsyncGenerator[Event, None]:
        # Get user input from session state
        query = ctx.session.state.get("user_input", "")
        
        # query transform 
        logger.info(f"🔍 Query: {query}")
        # embed
        embedded_query = self.get_embedding(text = query)
        logger.info(f"Embedded query: {embedded_query}")
        ctx.session.state['embedded_query'] = embedded_query
        
        # retrieve
        retrieved_docs = self.search_from_database(query = query, limit = self.top_k, candidates = self.candidates, vector_search_index = self.vector_search_index, atlas_search_index = self.atlas_search_index)
        logger.info(f"Retrieved documents: {retrieved_docs}")
        ctx.session.state['retrieved_docs'] = retrieved_docs
        
        # rerank
        reranked_docs = self.rerank_documents(query, retrieved_docs['data'])
        logger.info(f"Reranked documents: {reranked_docs}")
        ctx.session.state['reranked_docs'] = reranked_docs
        
        async for event in self.answer_generator.run_async(ctx):
            if (event.is_final_response() and event.content and event.content.parts):
                # Process final response if needed
                logger.info(f"Final response from answer generator: {event.content.parts[0].text}")
            yield event
        
        






        
    
        
    
    