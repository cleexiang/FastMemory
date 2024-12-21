from datetime import datetime
from typing import List
from pinecone import Pinecone
from litellm import embedding
import pytz

from app.models import MemoryItem

class PineconeClient:
    def __init__(self, api_key: str, index_name: str):
        """
        Initialize PineconeClient
        
        Args:
            api_key: Pinecone API key
            index_name: Pinecone index name
        """
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get vector embedding for text using LiteLLM
        
        Args:
            text: Input text to embed
            
        Returns:
            List[float]: Vector embedding of the input text
        """
        response = embedding(model='text-embedding-ada-002', input=[text])
        return response.data[0]['embedding']

    def add(self, memory_item: MemoryItem, user_id: str) -> bool:
        """
        Add a memory item to Pinecone
        
        Args:
            memory_item: Memory item to add
            user_id: User ID
            
        Returns:
            bool: True if addition was successful, False otherwise
        """
        try:
            vector = self._get_embedding(memory_item.memory)
            metadata = {}
            metadata["user_id"] = user_id
            metadata["content"] = memory_item.memory
            metadata["created_at"] = datetime.now(pytz.UTC).isoformat()

            upsert_data = {
                "id": memory_item.id,
                "values": vector,
                "metadata": metadata
            }
            
            if memory_item.metadata:
                upsert_data["metadata"].update(memory_item.metadata)
                
            self.index.upsert(vectors=[upsert_data])
            return True
            
        except Exception as e:
            print(f"Error adding memory: {e}")
            return False

    def search(self, query: str, threshold: float = 0.75, top_k: int = 3, user_id: str = None) -> List[MemoryItem]:
        """
        Search for memories in Pinecone
        
        Args:
            query: Search query text
            threshold: Score threshold, only return results above this score
            top_k: Maximum number of results to return
            user_id: Optional user ID to filter results by user
            
        Returns:
            List[MemoryItem]: List of matching memory items
        """
        try:
            query_vector = self._get_embedding(query)
            
            filter = None
            if user_id:
                filter = {
                    "user_id": {"$eq": user_id}
                }
            
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter  
            )
            
            memories = []
            for match in results.matches:
                if match.score >= threshold:
                    metadata = match.metadata
                    memory_item = MemoryItem(
                        id=match.id,
                        memory=metadata.pop("content"),
                        hash=metadata.pop("hash", None),
                        score=match.score,
                        created_at=metadata.pop("created_at", None),
                        updated_at=metadata.pop("updated_at", None),
                        metadata=metadata
                    )
                    memories.append(memory_item)
                    
            return memories
            
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    def get_all_by_user(self, user_id: str) -> List[MemoryItem]:
        """
        Get all memories for a specific user
        
        Args:
            user_id: User ID to fetch memories for
            
        Returns:
            List[MemoryItem]: List of all memory items for the user
        """
        try:
            filter = None
            if user_id:
                filter = {
                    "user_id": {"$eq": user_id}
                }
            results = self.index.query(
                vector=None,
                include_metadata=True,
                top_k=100,
                filter=filter  
            )
            memories = []
            for match in results.matches:
                metadata = match.metadata
                memory_item = MemoryItem(
                    id=match.id,
                    memory=metadata.pop("content"),
                    hash=metadata.pop("hash", None),
                    score=match.score,
                    created_at=metadata.pop("created_at", None),
                    updated_at=metadata.pop("updated_at", None),
                    metadata=metadata
                )
                memories.append(memory_item)
            return memories
        
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []


    def update(self, id: str, memory: str) -> bool:
        """
        Update a memory item by ID
        
        Args:
            id: ID of the memory to update
            memory: New memory content
            user_id: User ID
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            vector = self._get_embedding(memory)

            self.index.update(
                id=id, 
                values=vector, 
                set_metadata={"content": memory}
            )
            return True
            
        except Exception as e:
            print(f"Error updating memory: {e}")
            return False

    def delete_by_id(self, id: str) -> bool:
        """
        Delete a memory item by ID
        
        Args:
            id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.index.delete(ids=[id])
            return True
            
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False

    def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete all memories for a specific user
        
        Args:
            user_id: User ID whose memories should be deleted
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            filter = {
                "user_id": {"$eq": user_id}
            }
            
            self.index.delete(filter=filter)
            return True
            
        except Exception as e:
            print(f"Error deleting memories for user: {e}")
            return False

