import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": []}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k in default.keys():
                    if k not in data: data[k] = default[k]
                return data
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
# Geçici reçete tutucu
if 'temp_recete' not in st.session_state: st.session_state.temp_recete = {}

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    # ... (Depo kodu aynı kalabilir) ...

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    
    # Hammadde Ekleme Bölümü
    c_ad, c_mik, c_bir, c_btn = st.columns([2, 1, 1, 1])
    m_ad = c_ad.text_input("Hammadde")
    m_mik = c_mik.number_input("Miktar", format="%.4f")
    m_bir = c_bir.selectbox("Birim", BIRIM_LISTESI)
    
    if c_btn.button("➕ LİSTEYE EKLE"):
        if m_ad:
            st.session_state.temp_recete[m_ad.upper()] = {"MİKTAR": m_mik, "BİRİM": m_bir}
            st.rerun()

    # Geçici listeyi göster
    if st.session_state.temp_recete:
        st.write("EKLENENLER:", st.session_state.temp_recete)
        if st.button("💾 REÇETEYİ KAYDET"):
            if urun:
                st.session_state.data["RECETELER"][urun] = st.session_state.temp_recete
                st.session_state.temp_recete = {}
                verileri_kaydet(st.session_state.data)
                st.success("Reçete başarıyla kaydedildi!")
                st.rerun()
        if st.button("❌ LİSTEYİ SIFIRLA"):
            st.session_state.temp_recete = {}
            st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    # ... (Düzenleme sekmesi aynı) ...
    pass
# ... (Diğer sekmeler aynı) ...
