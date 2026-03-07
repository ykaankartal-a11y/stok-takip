import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

# ... (verileri_yukle ve verileri_kaydet aynı kalıyor) ...
def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "💰 MALİYET ANALİZİ", "📊 ARŞİV"])

# --- MODÜLLER ---

# 1. DEPO (Birim Fiyat Eklendi)
if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME").upper()
    miktar = c2.number_input("STOK MİKTARI", format="%.3f")
    birim = c3.selectbox("BİRİM", BIRIM_LISTESI)
    fiyat = c4.number_input("BİRİM FİYAT (₺)", format="%.2f")
    
    if st.button("KAYDET"): 
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

# 2. MALİYET ANALİZİ (Yeni Menü)
elif menu == "💰 MALİYET ANALİZİ":
    st.header("💰 MALİYET ANALİZİ")
    st.info("Bu alana sadece yetkili kullanıcılar erişebilecek.")
    if st.session_state.data["RECETELER"]:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"]).T)

# 3. AKTİF SİPARİŞLER (Maliyet Hesaplama Entegreli)
elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        # ... (Önceki kod ile aynı, sadece buton içine şunu ekle) ...
        if st.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
            recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
            # Maliyet hesapla: (Miktar * BirimFiyat)
            anlik_maliyet = 0
            for mad, info in recete.items():
                birim_fiyat = st.session_state.data["DEPO"].get(mad, {}).get("FİYAT", 0)
                anlik_maliyet += (info["MİKTAR"] * miktar) * birim_fiyat
            
            # ... geri kalan stok düşme işlemleri ...
            s["MALIYET"] = s.get("MALIYET", 0) + anlik_maliyet
            verileri_kaydet(st.session_state.data); st.rerun()
