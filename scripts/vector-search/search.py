"""Vector search query interface.

Takes natural language queries, generates embeddings, and retrieves
semantically similar documents from Supabase pgvector.

Supports filtering by file source and customizable similarity thresholds.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass

import aiohttp
import tiktoken
from supabase import create_client

from config import get_config


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    
    file_path: str
    file_source: str
    chunk_text: str
    similarity_score: float
    chunk_index: int = 0
    
    def __str__(self) -> str:
        """Format result for display."""
        preview = self.chunk_text[:200] + "..." if len(self.chunk_text) > 200 else self.chunk_text
        return (
            f"[{self.similarity_score:.3f}] {self.file_source}: {self.file_path}\n"
            f"    {preview}\n"
        )


class VectorSearchClient:
    """Client for vector similarity search."""
    
    def __init__(self):
        """Initialize search client."""
        self.config = get_config()
        self.supabase_client = create_client(
            self.config.supabase.url,
            self.config.supabase.api_key
        )
        self.encoding = tiktoken.encoding_for_model(self.config.azure_openai.embedding_model)
        logger.info("Vector search client initialized")
    
    async def generate_query_embedding(
        self,
        query: str,
        session: aiohttp.ClientSession,
        max_retries: int = 3
    ) -> Optional[list[float]]:
        """Generate embedding for search query.
        
        Args:
            query: Natural language search query
            session: aiohttp session
            max_retries: Maximum retry attempts
            
        Returns:
            Embedding vector or None if generation fails
        """
        headers = {
            "api-key": self.config.azure_openai.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": query,
            "model": self.config.azure_openai.embedding_model
        }
        
        for attempt in range(max_retries):
            try:
                async with session.post(
                    f"{self.config.azure_openai.endpoint}/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedding = data["data"][0]["embedding"]
                        token_count = len(self.encoding.encode(query))
                        logger.debug(f"Generated query embedding ({token_count} tokens)")
                        return embedding
                    
                    elif resp.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    
                    else:
                        error_text = await resp.text()
                        logger.error(f"API error {resp.status}: {error_text}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
            
            except asyncio.TimeoutError:
                logger.error(f"Timeout generating embedding (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        file_source: Optional[str] = None
    ) -> list[SearchResult]:
        """Search for semantically similar documents.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            file_source: Optional filter for source (onedrive, google_drive, local)
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Generate query embedding
                embedding = await self.generate_query_embedding(query, session)
                
                if embedding is None:
                    logger.error("Failed to generate query embedding")
                    return []
                
                # Query Supabase using match_documents function
                try:
                    response = self.supabase_client.rpc(
                        "match_documents",
                        {
                            "query_embedding": embedding,
                            "match_threshold": similarity_threshold,
                            "match_count": top_k
                        }
                    ).execute()
                    
                    results = []
                    for row in response.data:
                        # Apply source filter if specified
                        if file_source and row["file_source"] != file_source:
                            continue
                        
                        result = SearchResult(
                            file_path=row["file_path"],
                            file_source=row["file_source"],
                            chunk_text=row["chunk_text"],
                            similarity_score=row["similarity"]
                        )
                        results.append(result)
                    
                    logger.info(f"Found {len(results)} results")
                    return results
                
                except Exception as e:
                    logger.error(f"Database query error: {e}")
                    
                    # Fallback: query documents table directly
                    logger.info("Falling back to direct table query")
                    query_obj = self.supabase_client.table("documents").select("*")
                    
                    if file_source:
                        query_obj = query_obj.eq("file_source", file_source)
                    
                    response = query_obj.execute()
                    results = []
                    
                    for row in response.data:
                        # Calculate similarity manually if embedding not available
                        if "embedding" in row:
                            similarity = self._cosine_similarity(embedding, row["embedding"])
                            
                            if similarity >= similarity_threshold:
                                result = SearchResult(
                                    file_path=row["file_path"],
                                    file_source=row["file_source"],
                                    chunk_text=row["chunk_text"],
                                    similarity_score=similarity,
                                    chunk_index=row.get("chunk_index", 0)
                                )
                                results.append(result)
                    
                    # Sort by similarity and limit
                    results.sort(key=lambda x: x.similarity_score, reverse=True)
                    results = results[:top_k]
                    
                    logger.info(f"Found {len(results)} results (fallback)")
                    return results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec_a: First vector
            vec_b: Second vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if len(vec_a) != len(vec_b):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = sum(a * a for a in vec_a) ** 0.5
        mag_b = sum(b * b for b in vec_b) ** 0.5
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot_product / (mag_a * mag_b)


async def interactive_search():
    """Run interactive search session."""
    client = VectorSearchClient()
    
    print("\n=== Vector Search ===")
    print("Commands:")
    print("  search <query>           - Search for documents")
    print("  search <query> --top 20  - Return top 20 results")
    print("  search <query> --threshold 0.8  - Use custom similarity threshold")
    print("  search <query> --source onedrive - Filter by source")
    print("  exit                     - Exit search\n")
    
    while True:
        try:
            user_input = input("Search> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            # Parse command
            parts = user_input.split()
            if parts[0].lower() != "search":
                print("Unknown command. Use 'search' or 'exit'")
                continue
            
            query = " ".join(parts[1:])
            top_k = 10
            threshold = 0.7
            source = None
            
            # Parse optional flags
            if "--top" in query:
                idx = query.index("--top")
                query = query[:idx].strip()
                try:
                    top_k = int(query.split("--top")[1].split()[0])
                except (IndexError, ValueError):
                    top_k = 10
            
            if "--threshold" in query:
                idx = query.index("--threshold")
                query = query[:idx].strip()
                try:
                    threshold = float(query.split("--threshold")[1].split()[0])
                except (IndexError, ValueError):
                    threshold = 0.7
            
            if "--source" in query:
                idx = query.index("--source")
                query = query[:idx].strip()
                try:
                    source = query.split("--source")[1].split()[0]
                except (IndexError, ValueError):
                    source = None
            
            # Run search
            results = await client.search(
                query,
                top_k=top_k,
                similarity_threshold=threshold,
                file_source=source
            )
            
            if results:
                print(f"\n=== Results ({len(results)} matches) ===\n")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result}")
            else:
                print("No results found.")
            
            print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            logger.exception("Search error")


async def main():
    """Main entry point."""
    await interactive_search()


if __name__ == "__main__":
    asyncio.run(main())
