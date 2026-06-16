import json
from pathlib import Path
import logging

import qdrant_client
from qdrant_client.http import models as qmodels

# Mem0 client placeholder – you can replace with actual Mem0 SDK
class Mem0Client:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        # In a real implementation you would set up authentication, etc.

    def get_user_profile(self, user_id: str) -> dict:
        # Placeholder – fetch from a JSON file for demo purposes
        path = Path.home() / ".superai" / "mem0" / f"{user_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def update_user_profile(self, user_id: str, data: dict):
        path = Path.home() / ".superai" / "mem0"
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{user_id}.json").write_text(json.dumps(data, indent=2))

# Qdrant wrapper for vector storage
class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "super_ai"):
        db_path = Path.home() / ".superai" / "qdrant"
        db_path.mkdir(parents=True, exist_ok=True)
        self.client = qdrant_client.QdrantClient(path=str(db_path))
        self.collection_name = collection_name
        # Ensure collection exists
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE),
            )

    def upsert(self, ids: list[int], vectors: list[list[float]], payloads: list[dict]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[qmodels.PointStruct(id=id_, vector=vec, payload=payload) for id_, vec, payload in zip(ids, vectors, payloads)],
        )

    def search(self, query_vector: list[float], limit: int = 5) -> list[dict]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
        )
        return [r.payload for r in results.points]

# High‑level memory manager combining Mem0 and Qdrant
class MemoryManager:
    def __init__(self, cfg):
        self.mem0 = Mem0Client(base_url=getattr(cfg, "mem0_api", "http://localhost:5000"))
        self.vdb = VectorDB(
            host=getattr(cfg, "qdrant_host", "localhost"),
            port=getattr(cfg, "qdrant_port", 6333),
        )
        self.user_id = "default_user"

    def store_turn(self, text: str, embedding: list[float]):
        # Persist raw turn in Mem0 (as part of the profile)
        profile = self.mem0.get_user_profile(self.user_id)
        history = profile.get("history", [])
        history.append(text)
        profile["history"] = history
        self.mem0.update_user_profile(self.user_id, profile)
        # Store embedding in Qdrant for semantic search
        new_id = len(history)  # simple incremental ID
        self.vdb.upsert(ids=[new_id], vectors=[embedding], payloads=[{"text": text}])

    def retrieve_similar(self, query_embedding: list[float], top_k: int = 5) -> list[str]:
        results = self.vdb.search(query_embedding, limit=top_k)
        return [r.get("text", "") for r in results]
