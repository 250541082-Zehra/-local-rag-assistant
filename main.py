import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from src import database, ingestion, rag_engine

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def print_header():
    print("=" * 65)
    print(" Microsoft Online Yaz Stajı - Yerel RAG (Foundry Local) CLI")
    print(" Tamamen Çevrimdışı (Offline) Türkçe Doküman Sohbet Asistanı")
    print("=" * 65)

def main():
    print_header()
    
    # 1. Veritabanını Başlat
    database.init_db()
    
    # 2. Örnek Bilgi Yükle (Eğer veritabanı boşsa)
    chunk_count = database.get_total_chunks_count()
    if chunk_count == 0:
        print("\n[INFO] Veritabanı boş. Microsoft Staj başlangıç belgesi yükleniyor...")
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
        ingested = ingestion.ingest_text_data("microsoft_staj_rehberi.txt", sample_doc)
        print(f"[OK] {ingested} adet metin parçası SQLite veritabanına işlendi.")
        
    print(f"\n[INFO] Veritabanı Durumu: {database.get_total_chunks_count()} adet vektörleştirilmiş metin parçası hazır.")
    print("\n[BİLGİ] Çıkış yapmak için 'q' veya 'cikis' yazabilirsiniz.\n")
    
    # Tek seferlik veya döngülü test çalıştırması
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"[SORU]: {query}")
        result = rag_engine.answer_query(query, k=3)
        print("\n[ASİSTAN YANITI]:")
        print(result["answer"])
        return

    while True:
        try:
            query = input("\n[SORU] Sorunuzu Girin (Türkçe): ").strip()
            if not query:
                continue
            if query.lower() in ['q', 'exit', 'quit', 'cikis', 'çıkış']:
                print("\n[ÇIKIŞ] Görüşmek üzere! Başarılar dileriz.")
                break
                
            print("\n[ARAMA] SQLite veritabanında kosinüs benzerliği ile aranıyor...")
            result = rag_engine.answer_query(query, k=3)
            
            print("\n[ASİSTAN YANITI]:")
            print("-" * 50)
            print(result["answer"])
            print("-" * 50)
            
            if result["chunks"]:
                print("\n[KAYNAKLAR] En Alakalı Doküman Parçaları:")
                for idx, c in enumerate(result["chunks"], 1):
                    print(f"  [{idx}] {c['filename']} (Skor: {c['score']:.2f}) -> {c['content'][:100]}...")
            print("\n" + "=" * 65)
            
        except KeyboardInterrupt:
            print("\n[ÇIKIŞ] Program kapatıldı.")
            break
        except Exception as e:
            print(f"[HATA] Bir hata oluştu: {e}")

if __name__ == "__main__":
    main()
