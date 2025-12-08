# Vector Dimension Mismatch Fix - mxbai-embed-large Model

## Issue Description

When attempting to load sample transaction data into the Qdrant vector store, the application encountered a dimension mismatch error:

```
Error loading data: Unexpected Response: 400 (Bad Request)
Raw response content: b'{"status":{"error":"Wrong input: Vector dimension error: expected dim: 768, got 1024"},"time":0.02486576}'
```

### Root Cause

The Qdrant collection was created with a hardcoded vector dimension of **768**, but the embedding model `mxbai-embed-large:latest` produces vectors with **1024 dimensions**. This mismatch caused Qdrant to reject all vector insertions.

### Technical Details

- **Embedding Model**: `mxbai-embed-large:latest` (via Ollama)
- **Expected Dimension**: 768 (hardcoded in original code)
- **Actual Dimension**: 1024 (produced by the model)
- **Vector Store**: Qdrant

## Solution

Implemented a dynamic dimension detection system that:

1. **Automatically detects embedding dimension** by generating a test embedding from the model
2. **Creates collections with correct dimension** based on the actual model output
3. **Automatically fixes existing collections** that have incorrect dimensions by deleting and recreating them

### Changes Made

#### 1. Dynamic Dimension Detection

Added `_get_embedding_dimension()` method that queries the embedding model to determine the actual vector dimension:

```python
def _get_embedding_dimension(self) -> int:
    """Get the embedding dimension by generating a test embedding"""
    test_embedding = self._generate_embedding("test")
    return len(test_embedding)
```

#### 2. Updated Collection Creation

Modified `_create_collection_if_not_exists()` to:
- Use the dynamically detected dimension instead of hardcoded 768
- Check existing collections for dimension mismatches
- Automatically recreate collections with incorrect dimensions

```python
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
        existing_dim = collection_info.config.params.vectors.size
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
```

#### 3. Updated Model Name

Changed default embedding model from `mxbai-embed-large` to `mxbai-embed-large:latest` to match the actual model being used:

```python
def __init__(
    self, collection_name="transactions", embedding_model="mxbai-embed-large:latest"
):
```

## Benefits

1. **Future-proof**: Automatically adapts to any embedding model dimension
2. **Self-healing**: Automatically fixes dimension mismatches in existing collections
3. **Explicit model versioning**: Uses `:latest` tag for clarity
4. **No manual intervention**: Users don't need to manually delete/recreate collections

## Testing

After the fix, the application successfully:
- Detected the dimension mismatch (768 → 1024)
- Automatically recreated the collection with correct dimension
- Loaded 150 sample transactions without errors

### Terminal Output

```
Warning: Collection exists with dimension 768, but model produces 1024
Deleting and recreating collection with correct dimension...
Recreated collection: transactions with dimension 1024
Added 150 transactions to vector store
```

## Files Modified

- `vector_store.py`: Added dynamic dimension detection and automatic collection repair

## Date Fixed

December 8, 2025

## Status

✅ **Resolved** - The application now automatically handles vector dimension mismatches and successfully loads transaction data.
