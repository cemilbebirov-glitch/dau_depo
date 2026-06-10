"""
RAG System Module - Document Processing & Query
Raw SQLite pattern: import database as db
"""

import database as db
import json
import os
from datetime import datetime


class RAGSystem:
    """RAG - Retrieval Augmented Generation System"""

    def __init__(self, socketio=None):
        self.socketio = socketio

    def process_document(self, filepath, filename):
        """Sənədi emal et və chunk-lara böl"""
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            file_type = file_ext.lstrip('.')

            content = self._read_file(filepath, file_type)
            if not content:
                return {'error': 'Sənəd oxuna bilmədi', 'filename': filename}

            # Sənədi DB-ya yaz
            doc_id = db.rag_doc_add(
                filename=filename,
                filepath=filepath,
                file_type=file_type,
                chunk_count=0,
                metadata={'file_size': os.path.getsize(filepath)}
            )

            # Chunk-lara böl
            chunks = self._split_text(content, chunk_size=500, overlap=50)

            # Chunk-ları DB-ya yaz
            for i, chunk in enumerate(chunks):
                db.rag_chunk_add(
                    document_id=doc_id,
                    content=chunk,
                    chunk_index=i
                )

            # Sənəd chunk sayını yenilə
            db.rag_doc_update_chunks(doc_id, len(chunks), status='ready')

            if self.socketio:
                self.socketio.emit('rag_document_processed', {
                    'doc_id': doc_id,
                    'filename': filename,
                    'chunks': len(chunks)
                })

            return {
                'doc_id': doc_id,
                'filename': filename,
                'chunks': len(chunks),
                'status': 'ready'
            }
        except Exception as e:
            print(f"process_document xətası: {e}")
            return {'error': str(e), 'filename': filename}

    def query(self, query_text, top_k=5):
        """Sual ver və ən uyğun cavabları tap"""
        try:
            # DB-dan axtar
            results = db.rag_chunk_search(query_text, limit=top_k)

            if not results:
                return []

            # Relevance score hesabla (sadə text matching)
            query_words = set(query_text.lower().split())
            for r in results:
                content_words = set(r.get('content', '').lower().split())
                overlap = len(query_words & content_words)
                r['score'] = min(overlap / max(len(query_words), 1), 1.0)

            # Score-a görə sırala
            results.sort(key=lambda x: x.get('score', 0), reverse=True)

            return results[:top_k]
        except Exception as e:
            print(f"query xətası: {e}")
            return []

    def _read_file(self, filepath, file_type):
        """Fayl oxu"""
        try:
            if file_type in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv']:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            elif file_type == 'pdf':
                return self._read_pdf(filepath)
            elif file_type in ['doc', 'docx']:
                return self._read_docx(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
        except Exception as e:
            print(f"_read_file xətası: {e}")
            return None

    def _read_pdf(self, filepath):
        """PDF oxu"""
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "[PDF oxuyucu quraşdırılmayıb - pip install PyPDF2]"
        except Exception as e:
            return None

    def _read_docx(self, filepath):
        """DOCX oxu"""
        try:
            import docx
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            return "[DOCX oxuyucu quraşdırılmayıb - pip install python-docx]"
        except Exception as e:
            return None

    def _split_text(self, text, chunk_size=500, overlap=50):
        """Mətni chunk-lara böl"""
        if not text:
            return []

        chunks = []
        words = text.split()
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - overlap

        return chunks

    def get_stats(self):
        """RAG statistikası"""
        try:
            docs = db.rag_doc_list()
            total_chunks = sum(d.get('chunk_count', 0) for d in docs)
            return {
                'total_documents': len(docs),
                'total_chunks': total_chunks,
                'status': 'active'
            }
        except Exception as e:
            print(f"get_stats xətası: {e}")
            return {'total_documents': 0, 'total_chunks': 0, 'status': 'error'}