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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

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

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    urun_adi = st.text_input("ÜRÜN ADI").upper()
    
    c1, c2, c3 = st.columns(3)
    m_ad = c1.text_input("MALZEME ADI").upper()
    m_mik = c2.number_input("MİKTAR", format="%.4f")
    if c3.button("➕ LİSTEYE EKLE"):
        st.session_state.temp_liste.append({"MALZEME": m_ad, "MİKTAR": m_mik})
        st.rerun()
    
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ KAYDET"):
            # Listeyi sözlüğe çevirip kaydet
            recete_dict = {item["MALZEME"]: item["MİKTAR"] for item in st.session_state.temp_liste}
            st.session_state.data["RECETELER"][urun_adi] = recete_dict
            st.session_state.temp_liste = []
            verileri_kaydet(st.session_state.data); st.rerun()
        if st.button("❌ LİSTEYİ SIFIRLA"):
            st.session_state.temp_liste = []; st.rerun()

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
    for i, s in enumerate(st.session_state.data.get("SIPARISLER", [])):
        st.write(f"**{s['MÜŞTERİ']}** | {s['ÜRÜN']} | {s['FİYAT']} ₺")
        if st.button(f"KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
            kapali = st.session_state.data["SIPARISLER"].pop(i)
            st.session_state.data["ARSIV"].append(kapali)
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arsiv = st.session_state.data.get("ARSIV", [])
    if arsiv: st.table(pd.DataFrame(arsiv))
    else: st.info("Arşiv henüz boş.")
