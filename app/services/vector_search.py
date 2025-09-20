import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np

class VectorSearchService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection("hr_policies")
    
    async def search_similar_content(self, query: str, n_results: int = 5, category: str = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Prepare where clause for category filtering
            where_clause = None
            if category:
                where_clause = {"category": category}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            similar_content = []
            for i in range(len(results['ids'][0])):
                similar_content.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "title": results['metadatas'][0][i].get('title', ''),
                    "category": results['metadatas'][0][i].get('category', ''),
                    "section": results['metadatas'][0][i].get('section', ''),
                    "subsection": results['metadatas'][0][i].get('subsection', '')
                })
            
            return similar_content
            
        except Exception as e:
            print(f"Error searching content: {e}")
            return []
    
    async def get_related_policies(self, policy_id: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Get policies related to a specific policy"""
        try:
            # Get the policy content first
            policy_results = self.collection.get(ids=[policy_id])
            if not policy_results['ids']:
                return []
            
            policy_content = policy_results['documents'][0]
            
            # Search for similar content
            return await self.search_similar_content(policy_content, n_results)
            
        except Exception as e:
            print(f"Error getting related policies: {e}")
            return []
    
    async def search_by_category(self, category: str, query: str = "", n_results: int = 10) -> List[Dict[str, Any]]:
        """Search within a specific category"""
        try:
            if query:
                return await self.search_similar_content(query, n_results, category)
            else:
                # Get all content from category
                results = self.collection.get(
                    where={"category": category},
                    limit=n_results
                )
                
                content = []
                for i in range(len(results['ids'])):
                    content.append({
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i],
                        "title": results['metadatas'][i].get('title', ''),
                        "category": results['metadatas'][i].get('category', ''),
                        "section": results['metadatas'][i].get('section', ''),
                        "subsection": results['metadatas'][i].get('subsection', '')
                    })
                
                return content
                
        except Exception as e:
            print(f"Error searching by category: {e}")
            return []
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text"""
        return self.embedding_model.encode(text).tolist()
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        embedding1 = self.embedding_model.encode(text1)
        embedding2 = self.embedding_model.encode(text2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return float(similarity)
