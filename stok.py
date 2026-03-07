import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    # Dosya yoksa veya bozuksa en temiz yapıyı kur
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

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3 = st.columns(3)
    isim = c1.text_input("MALZEME ADI").upper()
    miktar = c2.number_input("MİKTAR", format="%.3f")
    fiyat = c3.number_input("BİRİM FİYAT (₺)")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]:
        st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    urun = st.text_input("ÜRÜN ADI").upper()
    malz = st.text_input("MALZEME ADI").upper()
    mik = st.number_input("MİKTAR", format="%.4f")
    if st.button("EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][malz] = mik
        verileri_kaydet(st.session_state.data); st.rerun()
    st.write("MEVCUT REÇETELER:", st.session_state.data["RECETELER"])

elif menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    receteler = list(st.session_state.data["RECETELER"].keys())
    uru = st.selectbox("ÜRÜN", receteler if receteler else ["ÖNCE REÇETE TANIMLA"])
    satis = st.number_input("SATIŞ FİYATI (₺)")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "FİYAT": satis, "TARİH": str(datetime.now().date())})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    if not st.session_state.data["SIPARISLER"]:
        st.info("Aktif sipariş bulunmuyor.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            st.write(f"**{s['MÜŞTERİ']}** - {s['ÜRÜN']} - {s['FİYAT']}₺")
            if st.button(f"KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
                kapali = st.session_state.data["SIPARISLER"].pop(i)
                st.session_state.data["ARSIV"].append(kapali)
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if len(st.session_state.data["ARSIV"]) > 0:
        st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
    else:
        st.info("Arşiv henüz boş.")
