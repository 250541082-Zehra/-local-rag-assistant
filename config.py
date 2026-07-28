import os
import sys

# Çevrimdışı (Offline) Modu Zorla - HuggingFace network/httpx hatalarını engellemek için
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Windows konsol çıktılarında utf-8 karakter kodlaması sağla
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Proje Yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "rag_knowledge.db")

# Dizin Oluşturma
os.makedirs(DATA_DIR, exist_ok=True)

# Embedding Konfigürasyonu
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Doküman Parçalama (Chunking) Parametreleri
CHUNK_SIZE = 700       # Karakter cinsinden parça boyutu
CHUNK_OVERLAP = 100    # Karakter cinsinden örtüşme miktarı

# Yerel LLM / Prompt Konfigürasyonu
DEFAULT_SYSTEM_PROMPT = """Sen Türkçe çalışan sorumlu bir yapay zeka asistanısın.
Sadece sana verilen "Bağlam (Context)" içindeki bilgileri kullanarak kullanıcının sorusunu yanıtla.

Kurallar:
1. Yanıtlarını tamamen Türkçe olarak yaz.
2. Bağlamda cevap yoksa kesinlikle bilgi uydurma (halüsinasyon görme) ve kibarca: "Üzgünüm, sağlanan belgelerde bu soruyla ilgili bilgi bulunmamaktadır." de.
3. Bilgi bağlamda varsa, hangi belgeden/kaynaktan alındığını belirt (Kaynak Gösterimi / Source Citation).
4. Açık, öz ve anlaşılır yanıtlar ver.
"""
