import streamlit as st
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

from sentence_transformers import SentenceTransformer
from src import database, ingestion, rag_engine

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Microsoft Online Yaz Stajı - Yerel RAG Asistanı",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Model önbellekleme (Çevrimdışı yerel yükleme ile)
@st.cache_resource
def load_streamlit_cached_model():
    try:
        return SentenceTransformer(config.EMBEDDING_MODEL_NAME, local_files_only=True)
    except Exception:
        return SentenceTransformer(config.EMBEDDING_MODEL_NAME)

# Model önbelleğini yükle ve bağla
cached_model = load_streamlit_cached_model()
ingestion.set_embedding_model(cached_model)

# Custom CSS Stilleri (Glassmorphism & Modern Microsoft Teması)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #0078D4, #50E6FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #A0AEC0;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Veritabanını Başlat
database.init_db()

# Örnek Belge Yükle (İlk çalıştırma kontrolü)
if database.get_total_chunks_count() == 0:
    sample_doc = """Microsoft Foundry Local ve SQLite Tabanlı Yerel RAG Uygulaması

Proje Özeti:
Bu proje Microsoft Online Yaz Stajı kapsamında geliştirilmiş bir çevrimdışı bilgi asistanıdır.
Sistem internete bağlanmadan kullanıcı sorularını yerel veritabanında saklanan doküman parçalarıyla yanıtlar.

Kullanılan Teknolojiler:
1. Foundry Local: Cihaz üzerinde çalışan hafif dil modeli (LLM) çıkarım motoru.
2. SQLite: Doküman metinlerini ve vektör gömmelerini (embeddings) saklayan yerel veritabanı.
3. Sentence-Transformers: Türkçe ve çok dilli metinleri vektör uzayına dönüştüren embedding modeli.
4. RAG Mimarisi: Bilgiyi geri getiren (Retrieve), bağlamı zenginleştiren (Augment) ve yanıt üreten (Generate) yapay zeka deseni.

Sorumlu Yapay Zeka İlkeleri:
Asistan halüsinasyon görmez; bilgiyi sadece sağlanan belgelerden alır ve cevabın kaynağını açıkça belirtir.
"""
    ingestion.ingest_text_data("microsoft_staj_rehberi.txt", sample_doc)

# Session State Başlatma
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Merhaba! Ben Microsoft Online Yaz Stajı **Yerel RAG Asistanı**'yım. Yüklediğiniz belgeler hakkında Türkçe sorular sorabilirsiniz."}
    ]

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg", width=150)
    st.title("📁 Doküman Yönetimi")
    st.markdown("---")
    
    # 1. Doküman Yükleme
    uploaded_files = st.file_uploader(
        "Yeni Belgeler Yükleyin (PDF, TXT, DOCX):",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.spinner(f"'{uploaded_file.name}' işleniyor ve SQLite'a aktarılıyor..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    num_chunks = ingestion.ingest_file(tmp_path)
                    st.success(f"✅ '{uploaded_file.name}' ({num_chunks} parça) kaydedildi.")
                except Exception as e:
                    st.error(f" Hata ({uploaded_file.name}): {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        
    st.markdown("---")
    # 2. Veritabanı İstatistikleri
    st.subheader("📊 Veritabanı Durumu")
    total_chunks = database.get_total_chunks_count()
    docs = database.get_all_documents()
    
    st.metric("Toplam Vektör Parçası", f"{total_chunks} chunk")
    st.metric("Kayıtlı Doküman Sayısı", f"{len(docs)} dosya")
    
    with st.expander("📄 Yüklü Dosya Listesi"):
        for d in docs:
            st.text(f"• {d['filename']}")
            
    st.markdown("---")
    if st.button("🗑️ Veritabanını Temizle", type="secondary"):
        database.clear_db()
        st.session_state.messages = []
        st.rerun()

# --- ANA EKRAN (MAIN PANEL) ---
st.markdown('<div class="main-title">🤖 Microsoft Yerel RAG Sohbet Asistanı</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Microsoft Foundry Local & SQLite Çevrimdışı (Offline) Türkçe Soru-Cevap Sistemi</div>', unsafe_allow_html=True)

# Sohbet Geçmişini Göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "chunks" in message and message["chunks"]:
            with st.expander("🔍 Geri Getirilen Doküman Parçaları ve Benzerlik Skorları"):
                for idx, c in enumerate(message["chunks"], 1):
                    st.markdown(f"**[{idx}] {c['filename']}** (Parça #{c['chunk_index']+1} - **Benzerlik: {c['score']:.2f}**)")
                    st.caption(c["content"])

# Kullanıcı Girdisi
if user_query := st.chat_input("Sorunuzu yazın (örn: RAG projesinin amacı nedir?)..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
        
    with st.chat_message("assistant"):
        with st.spinner("SQLite veritabanından bilgi çekiliyor ve yanıt üretiliyor..."):
            res = rag_engine.answer_query(user_query, k=3)
            answer_text = res["answer"]
            chunks = res["chunks"]
            
            st.markdown(answer_text)
            
            if chunks:
                with st.expander("🔍 Geri Getirilen Doküman Parçaları ve Benzerlik Skorları"):
                    for idx, c in enumerate(chunks, 1):
                        st.markdown(f"**[{idx}] {c['filename']}** (Parça #{c['chunk_index']+1} - **Benzerlik: {c['score']:.2f}**)")
                        st.caption(c["content"])
                        
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "chunks": chunks
    })
