import os
import re
from typing import Dict, List, Any
import PyPDF2
from docx import Document
import chromadb
from sentence_transformers import SentenceTransformer
import uuid

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection("hr_policies")
    
    async def process_document(self, file_path: str, category: str, title: str, description: str = "") -> Dict[str, Any]:
        """Process a document and create searchable chunks"""
        try:
            # Extract text based on file type
            if file_path.endswith('.pdf'):
                text = self._extract_pdf_text(file_path)
            elif file_path.endswith('.docx'):
                text = self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Split into chunks
            chunks = self._split_into_chunks(text, title)
            
            # Create embeddings and store in vector database
            chunk_ids = []
            embeddings = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                
                # Create embedding
                embedding = self.embedding_model.encode(chunk['content']).tolist()
                embeddings.append(embedding)
                
                # Create metadata
                metadata = {
                    "title": title,
                    "category": category,
                    "description": description,
                    "chunk_index": i,
                    "file_path": file_path,
                    "section": chunk.get('section', ''),
                    "subsection": chunk.get('subsection', '')
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=[chunk['content'] for chunk in chunks]
            )
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "title": title,
                "category": category,
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks_created": 0
            }
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _split_into_chunks(self, text: str, title: str) -> List[Dict[str, Any]]:
        """Split text into meaningful chunks with section detection"""
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split by common section patterns
        section_patterns = [
            r'\n\s*\d+\.\s+[A-Z][^.\n]*',  # 1. Section Title
            r'\n\s*[A-Z][A-Z\s]+\n',       # ALL CAPS SECTION
            r'\n\s*[A-Z][a-z\s]+:\s*\n',   # Section Title:
        ]
        
        sections = [text]
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                parts = re.split(pattern, section)
                new_sections.extend(parts)
            sections = new_sections
        
        # Create chunks from sections
        chunks = []
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:  # Skip very short sections
                continue
                
            # Try to extract section title
            section_title = ""
            subsection = ""
            
            # Look for section markers
            lines = section.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if re.match(r'^\d+\.', first_line) or len(first_line) < 100:
                    section_title = first_line
                    content = '\n'.join(lines[1:]).strip()
                else:
                    content = section.strip()
            
            # Split large sections into smaller chunks
            if len(content) > 1000:
                sub_chunks = self._split_large_text(content, 800)
                for j, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        "content": sub_chunk,
                        "section": section_title,
                        "subsection": f"Part {j+1}" if len(sub_chunks) > 1 else ""
                    })
            else:
                chunks.append({
                    "content": content,
                    "section": section_title,
                    "subsection": subsection
                })
        
        return chunks
    
    def _split_large_text(self, text: str, max_length: int) -> List[str]:
        """Split large text into smaller chunks"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk + sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def search_similar_chunks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            similar_chunks = []
            for i in range(len(results['ids'][0])):
                similar_chunks.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })
            
            return similar_chunks
            
        except Exception as e:
            print(f"Error searching chunks: {e}")
            return []
