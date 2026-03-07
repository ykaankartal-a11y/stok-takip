import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", [
    "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", 
    "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"
])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    c1, c2 = st.columns(2)
    mus = c1.text_input("MÜŞTERİ ADI").upper()
    uru = c2.selectbox("ÜRÜN", list(st.session_state.data.get("RECETELER", {}).keys()))
    c3, c4, c5 = st.columns(3)
    adet = c3.number_input("ADET", min_value=1, step=1)
    fiyat = c4.number_input("TOPLAM FİYAT (₺)", min_value=0.0)
    termin = c5.date_input("TERMİN TARİHİ")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        siparis_no = st.session_state.data["SIPARIS_SAYAC"]
        st.session_state.data["SIPARISLER"].append({
            "NO": siparis_no,
            "ID": datetime.now().strftime("%Y%m%d%H%M%S%f"), 
            "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, 
            "FİYAT": fiyat, "TERMİN": str(termin)
        })
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    siparisler = st.session_state.data.get("SIPARISLER", [])
    
    if not siparisler:
        st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(siparisler):
            with st.expander(f"No: {s.get('NO', '---')} | {s.get('MÜŞTERİ', 'Belirtilmedi')} - {s.get('ÜRÜN', 'Belirtilmedi')}"):
                not_key = f"not_{i}"
                kapatma_notu = st.text_input(f"Kapatma Notu", key=not_key)
                
                # Onay kutusu olmadan işlem yapma
                onay = st.checkbox("Bu siparişi kapatmak istediğimi onaylıyorum", key=f"check_{i}")
                
                if onay:
                    if st.button("✅ KAPAT VE ARŞİVLE", key=f"btn_{i}"):
                        s["KAPATMA_NOTU"] = kapatma_notu
                        s["KAPATILMA_TARİHİ"] = str(datetime.now())
                        # Arşive at ve listeden çıkar
                        kapali = st.session_state.data["SIPARISLER"].pop(i)
                        st.session_state.data["ARSIV"].append(kapali)
                        verileri_kaydet(st.session_state.data)
                        st.success("Sipariş arşive taşındı!")
                        st.rerun() # Sayfayı zorla yenile

# (Diğer modüller aynıdır...)
elif menu == "⚙️ REÇETE TANIMLA":
    # ... önceki kod yapısı ile aynı ...
    pass
# (Depo, Mevcut Reçeteler, Arşiv modüllerini buraya eklemeye devam edebilirsin)
