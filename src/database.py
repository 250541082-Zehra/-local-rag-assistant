import sqlite3
import json
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_connection():
    """SQLite veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Gerekli SQLite tablolarını oluşturur."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Dokümanlar Tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Doküman Parçaları (Chunks) Tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                filename TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def clear_db():
    """Veritabanındaki tüm dokümanları ve parçaları siler."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        cursor.execute("DELETE FROM documents")
        conn.commit()

def save_document_chunks(filename, chunks_data):
    """
    Doküman bilgisini ve parçalarını (content, embedding) SQLite veritabanına kaydeder.
    chunks_data: list of dicts [{'chunk_index': 0, 'content': '...', 'embedding': [...]}]
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO documents (filename) VALUES (?)", (filename,))
        doc_id = cursor.lastrowid
        
        for item in chunks_data:
            embedding_json = json.dumps(item['embedding'])
            cursor.execute("""
                INSERT INTO chunks (document_id, filename, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, filename, item['chunk_index'], item['content'], embedding_json))
            
        conn.commit()
    return doc_id

def cosine_similarity(vec1, vec2):
    """İki vektör arasındaki Kosinüs Benzerliğini hesaplar."""
    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def search_similar_chunks(query_embedding, top_k=3):
    """
    Verilen sorgu embedding vektörüne en yakın top_k doküman parçasını döndürür.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, filename, chunk_index, content, embedding FROM chunks").fetchall()
        
        if not rows:
            return []
        
        results = []
        for row in rows:
            chunk_emb = json.loads(row['embedding'])
            score = cosine_similarity(query_embedding, chunk_emb)
            results.append({
                'id': row['id'],
                'filename': row['filename'],
                'chunk_index': row['chunk_index'],
                'content': row['content'],
                'score': score
            })
            
        # Skorlara göre azalan sırada sırala
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

def get_all_documents():
    """Sistemde kayıtlı tüm dokümanların listesini getirir."""
    with get_connection() as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT id, filename, uploaded_at FROM documents ORDER BY id DESC").fetchall()

def get_total_chunks_count():
    """Veritabanındaki toplam parça sayısını döndürür."""
    with get_connection() as conn:
        cursor = conn.cursor()
        res = cursor.execute("SELECT COUNT(*) as count FROM chunks").fetchone()
        return res['count'] if res else 0

if __name__ == "__main__":
    init_db()
    print("[OK] SQLite veritabanı başarıyla başlatıldı:", config.DB_PATH)
