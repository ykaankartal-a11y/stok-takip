import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YAPISI VE GÜVENLİ YÜKLEME ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Her zaman eksik anahtarları tamamla
                keys = ["DEPO", "RECETELER", "SIPARISLER", "ARSIV"]
                for k in keys:
                    if k not in data: data[k] = {} if k != "SIPARISLER" and k != "ARSIV" else []
                return data
        except: pass
    return {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": []}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ SİSTEMİ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

# 1. DEPO
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

# 2. REÇETE
elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    urun = st.text_input("ÜRÜN ADI").upper()
    malz = st.text_input("MALZEME ADI").upper()
    mik = st.number_input("MİKTAR", format="%.4f")
    if st.button("EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][malz] = mik
        verileri_kaydet(st.session_state.data); st.rerun()
    st.write(st.session_state.data["RECETELER"])

# 3. SİPARİŞ OLUŞTUR
elif menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    receteler = list(st.session_state.data["RECETELER"].keys())
    uru = st.selectbox("ÜRÜN", receteler if receteler else ["ÖNCE REÇETE TANIMLA"])
    satis = st.number_input("SATIŞ FİYATI (₺)")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "FİYAT": satis, "TARİH": str(datetime.now().date())})
        verileri_kaydet(st.session_state.data); st.rerun()

# 4. AKTİF SİPARİŞLER (KAPATMA VE ANALİZ)
elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        st.write(f"**{s['MÜŞTERİ']}** - {s['ÜRÜN']} - {s['FİYAT']}₺")
        if st.button(f"KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
            kapali = st.session_state.data["SIPARISLER"].pop(i)
            st.session_state.data["ARSIV"].append(kapali)
            verileri_kaydet(st.session_state.data); st.rerun()

# 5. ARŞİV
elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data["ARSIV"]:
        st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
