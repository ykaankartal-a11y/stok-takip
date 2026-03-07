import streamlit as st
import json
import os
import pandas as pd

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
    return {"DEPO": {}, "RECETELER": {}, "SIPARISLER": []}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETELER", "🛒 SİPARİŞLER"])

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    col1, col2, col3 = st.columns(3)
    isim = col1.text_input("MALZEME ADI").upper()
    miktar = col2.number_input("MİKTAR", format="%.3f")
    fiyat = col3.number_input("BİRİM FİYAT (₺)")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    
    if st.session_state.data["DEPO"]:
        st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "⚙️ REÇETELER":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    urun = st.text_input("ÜRÜN ADI").upper()
    malz = st.text_input("MALZEME ADI").upper()
    mik = st.number_input("MİKTAR", format="%.4f")
    if st.button("EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][malz] = mik
        verileri_kaydet(st.session_state.data); st.rerun()
    st.write(st.session_state.data["RECETELER"])

elif menu == "🛒 SİPARİŞLER":
    st.header("🛒 SİPARİŞ TAKİBİ")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", list(st.session_state.data["RECETELER"].keys()) or ["REÇETE TANIMLA"])
    if st.button("SİPARİŞİ OLUŞTUR"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru})
        verileri_kaydet(st.session_state.data); st.rerun()
    st.table(pd.DataFrame(st.session_state.data["SIPARISLER"]))
