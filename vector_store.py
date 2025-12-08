from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import ollama
import pandas as pd
from typing import List, Dict, Any
import os


class TransactionVectorStore:
    def __init__(
        self, collection_name="transactions", embedding_model="mxbai-embed-large:latest"
    ):
        # Check for Qdrant API key and URL from environment variables
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")

        # Initialize Qdrant client based on available configuration
        if qdrant_url:
            # Custom URL provided (e.g., behind Traefik or remote instance)
            if qdrant_api_key:
                # Remote Qdrant instance with API key
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            else:
                # Local Qdrant instance behind reverse proxy (no API key needed)
                self.client = QdrantClient(url=qdrant_url)
        elif qdrant_api_key:
            # If only API key is provided, assume cloud Qdrant (you may need to set QDRANT_URL)
            # For Qdrant Cloud, URL format is typically: https://<cluster-id>.qdrant.io
            raise ValueError(
                "QDRANT_URL environment variable is required when using QDRANT_API_KEY"
            )
        else:
            # Local Qdrant instance (default)
            self.client = QdrantClient(host="localhost", port=6333)

        self.collection_name = collection_name
        self.embedding_model = embedding_model
        # Get embedding dimension dynamically
        self.embedding_dim = self._get_embedding_dimension()
        self._create_collection_if_not_exists()

    def _get_embedding_dimension(self) -> int:
        """Get the embedding dimension by generating a test embedding"""
        test_embedding = self._generate_embedding("test")
        return len(test_embedding)

    def _create_collection_if_not_exists(self):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim, distance=Distance.COSINE
                ),
            )
            print(
                f"Created collection: {self.collection_name} with dimension {self.embedding_dim}"
            )
        else:
            # Check if existing collection has correct dimension
            collection_info = self.client.get_collection(self.collection_name)
            existing_dim = collection_info.config.params.vectors.size  # type: ignore[attr-defined]
            if existing_dim != self.embedding_dim:
                print(
                    f"Warning: Collection exists with dimension {existing_dim}, but model produces {self.embedding_dim}"
                )
                print(f"Deleting and recreating collection with correct dimension...")
                self.client.delete_collection(self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim, distance=Distance.COSINE
                    ),
                )
                print(
                    f"Recreated collection: {self.collection_name} with dimension {self.embedding_dim}"
                )

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        response = ollama.embeddings(model=self.embedding_model, prompt=text)
        return response["embedding"]

    def add_transactions(self, transactions: List[Dict]):
        """Add transactions to vector store"""
        points = []

        for i, transaction in enumerate(transactions):
            # Create embedding from description + category
            text = f"{transaction['description']} {transaction['category']} {transaction['merchant']}"
            vector = self._generate_embedding(text)

            point = PointStruct(
                id=transaction["id"],
                vector=vector,
                payload={
                    "date": transaction["date"],
                    "description": transaction["description"],
                    "category": transaction["category"],
                    "amount": transaction["amount"],
                    "merchant": transaction["merchant"],
                },
            )
            points.append(point)

        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"Added {len(points)} transactions to vector store")

    def search_by_description(self, query: str, limit: int = 5) -> List[Dict]:
        """Semantic search on transaction descriptions"""
        query_vector = self._generate_embedding(query)

        results = self.client.search(  # type: ignore[attr-defined]
            collection_name=self.collection_name, query_vector=query_vector, limit=limit
        )

        transactions = []
        for result in results:
            transactions.append({**result.payload, "score": result.score})

        return transactions

    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions (for categorical analysis)"""
        results = self.client.scroll(collection_name=self.collection_name, limit=1000)[
            0
        ]

        return [point.payload for point in results if point.payload is not None]
