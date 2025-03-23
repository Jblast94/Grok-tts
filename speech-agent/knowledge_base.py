import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


from flask import Flask


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class KnowledgeBase:
    """Knowledge base for storing and retrieving information"""
    
    def __init__(self, app: Flask = None, storage_dir: str = "./knowledge"):
        """Initialize the knowledge base"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.docs_dir = self.storage_dir / "documents"
        self.docs_dir.mkdir(exist_ok=True)
        
        self.memory_dir = self.storage_dir / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        self.index_file = self.storage_dir / "index.json"
        
        # Initialize index
        if not self.index_file.exists():
            self._save_index({
                "documents": {},
                "interactions": [],
                "last_updated": datetime.now().isoformat()
            })
        
        # Register with Flask app if provided
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Register routes with Flask app"""
        
        @app.route('/knowledge/add', methods=['POST'])
        def add_knowledge():
            from flask import request, jsonify
            
            try:
                data = request.json
                if not data or not isinstance(data, dict):
                    return jsonify({"error": "Invalid data format"}), 400
                
                # Add the knowledge
                result = self.add_knowledge(data)
                return jsonify({"success": True, "id": result}), 200
            except Exception as e:
                logging.error(f"Error adding knowledge: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/knowledge/query', methods=['POST'])
        def query_knowledge():
            from flask import request, jsonify
            
            try:
                query = request.json.get('query', '')
                if not query:
                    return jsonify({"error": "Query is required"}), 400
                
                # Query the knowledge base
                results = self.query(query)
                return jsonify({"results": results}), 200
            except Exception as e:
                logging.error(f"Error querying knowledge: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/knowledge/document/upload', methods=['POST'])
        def upload_document():
            from flask import request, jsonify
            
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No file part"}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({"error": "No selected file"}), 400
                
                # Process and store the document
                doc_id = self.add_document(
                    file.filename,
                    file.read(),
                    file.content_type
                )
                
                return jsonify({
                    "success": True,
                    "document_id": doc_id,
                    "filename": file.filename
                }), 200
            except Exception as e:
                logging.error(f"Error uploading document: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/knowledge/document/<doc_id>', methods=['GET'])
        def get_document(doc_id):
            from flask import send_file, jsonify
            
            try:
                doc_path, metadata = self.get_document(doc_id)
                if not doc_path:
                    return jsonify({"error": "Document not found"}), 404
                
                return send_file(
                    doc_path,
                    mimetype=metadata.get('content_type', 'application/octet-stream'),
                    as_attachment=True,
                    download_name=metadata.get('filename', f"document-{doc_id}")
                )
            except Exception as e:
                logging.error(f"Error retrieving document: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/knowledge/stats', methods=['GET'])
        def get_stats():
            from flask import jsonify
            
            try:
                stats = self.get_stats()
                return jsonify(stats), 200
            except Exception as e:
                logging.error(f"Error getting stats: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _load_index(self) -> Dict:
        """Load the index file"""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading index: {e}")
            return {"documents": {}, "interactions": [], "last_updated": datetime.now().isoformat()}
    
    def _save_index(self, index: Dict):
        """Save the index file"""
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def add_knowledge(self, data: Dict[str, Any]) -> str:
        """Add knowledge to the knowledge base"""
        # Generate a unique ID for this knowledge
        knowledge_id = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        data['id'] = knowledge_id
        
        # Save to file
        knowledge_file = self.memory_dir / f"{knowledge_id}.json"
        with open(knowledge_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update index
        index = self._load_index()
        index['interactions'].append({
            'id': knowledge_id,
            'timestamp': data['timestamp'],
            'type': data.get('type', 'general'),
            'summary': data.get('summary', '')
        })
        index['last_updated'] = datetime.now().isoformat()
        self._save_index(index)
        
        logging.info(f"Added knowledge with ID: {knowledge_id}")
        return knowledge_id
    
    def add_document(self, filename: str, content: bytes, content_type: str) -> str:
        """Add a document to the knowledge base"""
        # Generate a unique ID for this document
        doc_id = hashlib.md5(content).hexdigest()
        
        # Save document
        doc_path = self.docs_dir / doc_id
        with open(doc_path, 'wb') as f:
            f.write(content)
        
        # Extract text if possible (simplified version)
        text_content = ""
        if content_type.startswith('text/'):
            text_content = content.decode('utf-8', errors='ignore')
        
        # Update index
        index = self._load_index()
        index['documents'][doc_id] = {
            'filename': filename,
            'content_type': content_type,
            'size': len(content),
            'added': datetime.now().isoformat(),
            'has_text': bool(text_content)
        }
        index['last_updated'] = datetime.now().isoformat()
        self._save_index(index)
        
        # If we have text content, store it separately for searching
        if text_content:
            text_path = self.docs_dir / f"{doc_id}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        logging.info(f"Added document: {filename} (ID: {doc_id})")
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[tuple]:
        """Get a document from the knowledge base"""
        index = self._load_index()
        
        if doc_id not in index['documents']:
            return None, None
        
        doc_path = self.docs_dir / doc_id
        if not doc_path.exists():
            return None, None
        
        return str(doc_path), index['documents'][doc_id]
    
    def record_interaction(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record an interaction with the system"""
        interaction = {
            'type': 'interaction',
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            interaction.update(metadata)
        
        return self.add_knowledge(interaction)
    
    def query(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query the knowledge base (simple implementation)"""
        results = []
        
        # Load all knowledge files
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Simple text matching (in a real system, use vector search)
                score = 0
                if 'query' in data and query_text.lower() in data['query'].lower():
                    score += 3
                if 'response' in data and query_text.lower() in data['response'].lower():
                    score += 2
                if 'summary' in data and query_text.lower() in data['summary'].lower():
                    score += 4
                
                if score > 0:
                    results.append({
                        'id': data.get('id'),
                        'data': data,
                        'score': score
                    })
            except Exception as e:
                logging.error(f"Error processing knowledge file {file_path}: {e}")
        
        # Search in document text files
        index = self._load_index()
        for doc_id, metadata in index['documents'].items():
            text_path = self.docs_dir / f"{doc_id}.txt"
            if text_path.exists() and metadata.get('has_text'):
                try:
                    with open(text_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    
                    if query_text.lower() in text_content.lower():
                        results.append({
                            'id': doc_id,
                            'type': 'document',
                            'filename': metadata.get('filename'),
                            'score': 1,
                            'snippet': text_content[:200] + '...' if len(text_content) > 200 else text_content
                        })
                except Exception as e:
                    logging.error(f"Error searching document {doc_id}: {e}")
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        index = self._load_index()
        
        return {
            'document_count': len(index['documents']),
            'interaction_count': len(index['interactions']),
            'last_updated': index['last_updated'],
            'storage_size_kb': sum(f.stat().st_size for f in self.storage_dir.glob('**/*') if f.is_file()) // 1024
        }


        # Singleton instance
        kb = KnowledgeBase()


        def get_knowledge_base():
            """Get the knowledge base instance"""
            return kb
