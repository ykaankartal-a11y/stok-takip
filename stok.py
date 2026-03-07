import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

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
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3 = st.columns(3)
    isim = c1.text_input("MALZEME ADI").upper()
    miktar = c2.number_input("MİKTAR", format="%.3f")
    fiyat = c3.number_input("BİRİM FİYAT (₺)")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data.get("DEPO"): st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    urun = st.text_input("ÜRÜN ADI").upper()
    
    # Malzeme ekleme alanı
    c1, c2, c3 = st.columns(3)
    m_ad = c1.text_input("MALZEME").upper()
    m_mik = c2.number_input("MİKTAR", format="%.4f")
    if c3.button("➕ EKLE"):
        if m_ad: st.session_state.temp_recete[m_ad] = m_mik
    
    st.write("EKLENEN MALZEMELER:", st.session_state.temp_recete)
    
    if st.button("💾 REÇETEYİ TAMAMLA"):
        if urun and st.session_state.temp_recete:
            st.session_state.data["RECETELER"][urun] = st.session_state.temp_recete
            st.session_state.temp_recete = {}
            verileri_kaydet(st.session_state.data); st.rerun()
    if st.button("❌ TEMİZLE"): st.session_state.temp_recete = {}; st.rerun()

elif menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    receteler = list(st.session_state.data.get("RECETELER", {}).keys())
    uru = st.selectbox("ÜRÜN", receteler if receteler else ["ÖNCE REÇETE TANIMLA"])
    satis = st.number_input("SATIŞ FİYATI (₺)")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "FİYAT": satis, "TARİH": str(datetime.now().date())})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    siparisler = st.session_state.data.get("SIPARISLER", [])
    for i, s in enumerate(siparisler):
        st.write(f"**{s.get('MÜŞTERİ')}** - {s.get('ÜRÜN')} - {s.get('FİYAT')}₺")
        if st.button(f"KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
            kapali = st.session_state.data["SIPARISLER"].pop(i)
            st.session_state.data["ARSIV"].append(kapali)
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arsiv = st.session_state.data.get("ARSIV", [])
    if arsiv: st.table(pd.DataFrame(arsiv))
    else: st.info("Arşiv henüz boş.")
