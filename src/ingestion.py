import os
import sys
import pypdf
import docx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from sentence_transformers import SentenceTransformer
from src import database

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

_embedding_model = None

def get_embedding_model():
    """SentenceTransformer modelini çevrimdışı yerel dosyalarla yükler."""
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _embedding_model

def set_embedding_model(model_obj):
    """Streamlit veya dışarıdan önbelleklenmiş modeli ayarlar."""
    global _embedding_model
    _embedding_model = model_obj

def encode_texts(texts):
    """Metinleri güvenli bir şekilde embedding vektörlerine dönüştürür."""
    global _embedding_model
    model = get_embedding_model()
    try:
        return model.encode(texts, convert_to_numpy=True)
    except Exception as e:
        print(f"[UYARI] Embedding modeli yeniden başlatılıyor: {e}")
        try:
            _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        return _embedding_model.encode(texts, convert_to_numpy=True)

def read_file_content(file_path):
    """Farklı uzantılardaki (TXT, PDF, DOCX) dosyaların metin içeriğini okur."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    elif ext == ".pdf":
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    elif ext == ".docx":
        doc = docx.Document(file_path)
        for p in doc.paragraphs:
            if p.text:
                text += p.text + "\n"
    else:
        raise ValueError(f"Desteklenmeyen dosya türü: {ext}")
        
    return text.strip()

def chunk_text(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """
    Metni belirlenen karakter boyutunda parçalara böler.
    Parçalar arasında sürekliliği sağlamak için overlap (örtüşme) uygulanır.
    """
    chunks = []
    if not text:
        return chunks
        
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += (chunk_size - overlap)
        
    return chunks

def get_embeddings(texts):
    """Metin listesinin embedding vektörlerini hesaplar."""
    embeddings = encode_texts(texts)
    return embeddings.tolist()

def ingest_text_data(filename, raw_text):
    """
    Ham metni alır, parçalar, vektörleştirir ve SQLite veritabanına kaydeder.
    """
    chunks = chunk_text(raw_text)
    if not chunks:
        return 0
        
    embeddings = get_embeddings(chunks)
    
    chunks_data = []
    for idx, (c, emb) in enumerate(zip(chunks, embeddings)):
        chunks_data.append({
            'chunk_index': idx,
            'content': c,
            'embedding': emb
        })
        
    doc_id = database.save_document_chunks(filename, chunks_data)
    print(f"[OK] '{filename}' belgesi {len(chunks)} parçaya bölünerek SQLite'a kaydedildi. (Doc ID: {doc_id})")
    return len(chunks)

def ingest_file(file_path):
    """Dosyayı okur ve veritabanına aktarır."""
    filename = os.path.basename(file_path)
    text = read_file_content(file_path)
    return ingest_text_data(filename, text)

if __name__ == "__main__":
    database.init_db()
    sample_text = "Microsoft Online Yaz Stajı kapsamındaki RAG uygulaması, verileri yerel cihazda işler. SQLite veritabanı kullanılır."
    ingest_text_data("ornek_not.txt", sample_text)
