import os
import sys
import json
import asyncio
import argparse
import aiohttp
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions


@dataclass
class SearchResult:
    """Represents a vector search result."""
    id: str
    title: str
    similarity: float
    metadata: Optional[dict] = None


class VectorSearchClient:
    """Client for performing vector similarity searches against Supabase pgvector."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize the vector search client.
        
        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase API key (defaults to SUPABASE_API_KEY env var)
        
        Raises:
            ValueError: If required environment variables are not set
        """
        # Use provided values or fall back to environment variables
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_API_KEY")
        
        # Validate that required credentials are set
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not provided and not found in environment variables")
        if not self.supabase_key:
            raise ValueError("SUPABASE_API_KEY not provided and not found in environment variables")
        
        # Initialize Supabase client
        options = ClientOptions(headers={"X-Client-Info": "vector-search-client"})
        self.client: Client = create_client(self.supabase_url, self.supabase_key, options)
        
        # Azure OpenAI configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_key = os.getenv("AZURE_OPENAI_KEY")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Generate embedding for a query using Azure OpenAI.
        
        Args:
            query: Natural language query string
            
        Returns:
            List of embedding values
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.azure_endpoint}/openai/deployments/{self.deployment_name}/embeddings?api-version=2024-02-15-preview"
            headers = {
                "api-key": self.azure_key,
                "Content-Type": "application/json"
            }
            payload = {
                "input": query,
                "model": self.deployment_name
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to generate embedding: {await response.text()}")
                result = await response.json()
                return result["data"][0]["embedding"]

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity normalized to [0, 1]
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            # Normalize to [0, 1] range
            return max(0.0, min(1.0, similarity))
        except (TypeError, ValueError) as e:
            print(f"Error calculating similarity: {e}", file=sys.stderr)
            return 0.0

    def _has_rpc_function(self, function_name: str) -> bool:
        """Check if an RPC function exists in Supabase.
        
        Args:
            function_name: Name of the RPC function to check
            
        Returns:
            True if the function exists, False otherwise
        """
        try:
            # Query the information_schema to check if the function exists
            result = self.client.table("information_schema.routines").select("routine_name").eq(
                "routine_name", function_name
            ).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Warning: Could not verify RPC function existence: {e}", file=sys.stderr)
            return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        threshold: float = 0.5
    ) -> Tuple[list[SearchResult], int]:
        """Search for similar documents.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            offset: Pagination offset
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            Tuple of (search results list, total count)
        """
        # Generate embedding for the query
        query_embedding = await self.generate_query_embedding(query)
        
        results = []
        total_count = 0
        
        # Try using RPC function if it exists, otherwise fall back to direct table query
        if self._has_rpc_function("match_documents"):
            try:
                response = self.client.rpc(
                    "match_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": threshold,
                        "match_count": limit
                    }
                ).execute()
                
                for row in response.data:
                    similarity = self._cosine_similarity(query_embedding, row.get("embedding", []))
                    if similarity >= threshold:
                        results.append(
                            SearchResult(
                                id=row["id"],
                                title=row.get("title", ""),
                                similarity=similarity,
                                metadata=row.get("metadata")
                            )
                        )
                
                total_count = len(results)
            except Exception as e:
                print(f"RPC call failed, falling back to direct query: {e}", file=sys.stderr)
                # Fall through to direct table query
        
        # Fall back to direct table query if RPC is not available or failed
        if not results:
            try:
                response = self.client.table("documents").select("*").order(
                    "created_at", desc=True
                ).range(offset, offset + limit - 1).execute()
                
                for row in response.data:
                    try:
                        # Handle embedding field (could be JSON string or list)
                        embedding = row.get("embedding", [])
                        if isinstance(embedding, str):
                            embedding = json.loads(embedding)
                        
                        similarity = self._cosine_similarity(query_embedding, embedding)
                        if similarity >= threshold:
                            results.append(
                                SearchResult(
                                    id=row["id"],
                                    title=row.get("title", ""),
                                    similarity=similarity,
                                    metadata=row.get("metadata")
                                )
                            )
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error processing document {row.get('id')}: {e}", file=sys.stderr)
                        continue
                
                # Get total count for pagination
                count_response = self.client.table("documents").select("count", count="exact").execute()
                total_count = count_response.count if hasattr(count_response, 'count') else 0
            except Exception as e:
                print(f"Error querying documents: {e}", file=sys.stderr)
        
        # Sort by similarity descending
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results, total_count


async def interactive_search():
    """Run the vector search client in interactive mode."""
    try:
        client = VectorSearchClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Vector Search Client")
    print("Enter your search queries or 'quit' to exit")
    print("-" * 50)
    
    page = 1
    limit = 10
    
    while True:
        try:
            # Get user input
            query = input("\nSearch query (or 'quit'): ").strip()
            
            if query.lower() == "quit":
                break
            
            if not query:
                print("Please enter a valid query")
                continue
            
            # Perform search
            offset = (page - 1) * limit
            results, total_count = await client.search(query, limit=limit, offset=offset)
            
            if not results:
                print(f"No results found for query: {query}")
                continue
            
            # Display results
            print(f"\nResults for '{query}' (Page {page}, showing {len(results)} of {total_count} total):")
            print("-" * 50)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   ID: {result.id}")
                print(f"   Similarity: {result.similarity:.4f}")
                if result.metadata:
                    print(f"   Metadata: {result.metadata}")
                print()
            
            # Pagination prompt
            if total_count > limit:
                print(f"Total results: {total_count}")
                print("Enter 'n' for next page, 'p' for previous page, or new query to search")
                nav = input("Navigation: ").strip().lower()
                
                if nav == "n" and (page * limit) < total_count:
                    page += 1
                elif nav == "p" and page > 1:
                    page -= 1
                else:
                    page = 1  # Reset to page 1 for new search
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Vector search interface for documents")
    parser.add_argument("query", nargs="?", default=None, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Number of results per page (default: 10)")
    parser.add_argument("--page", type=int, default=1, help="Page number for pagination (default: 1)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold (0-1, default: 0.5)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            sys.exit(1)
        raise
    
    # If interactive mode or no query provided, run interactive search
    if args.interactive or args.query is None:
        try:
            asyncio.run(interactive_search())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Single query mode
        try:
            client = VectorSearchClient()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        
        try:
            offset = (args.page - 1) * args.limit
            results, total_count = asyncio.run(
                client.search(args.query, limit=args.limit, offset=offset, threshold=args.threshold)
            )
            
            if not results:
                print(f"No results found for query: {args.query}")
                sys.exit(0)
            
            print(f"Results for '{args.query}' (Page {args.page}, showing {len(results)} of {total_count} total):")
            print("-" * 50)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   ID: {result.id}")
                print(f"   Similarity: {result.similarity:.4f}")
                if result.metadata:
                    print(f"   Metadata: {result.metadata}")
            
            if total_count > args.limit:
                print(f"\nTotal results: {total_count}")
                print(f"Use --page flag to view other pages (e.g., --page 2)")
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
