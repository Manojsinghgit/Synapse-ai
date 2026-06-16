import qdrant_client
from qdrant_client.http import models

client = qdrant_client.QdrantClient(':memory:')
client.recreate_collection(collection_name="test", vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
client.upsert(collection_name="test", points=[models.PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"text": "hi"})])
results = client.query_points(collection_name="test", query=[0.1, 0.2, 0.3, 0.4], limit=1)
print(type(results))
print(dir(results))
print(results.points[0].payload)
