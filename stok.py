import streamlit as st
import json
import os
import pandas as pd

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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME ADI").upper()
    miktar = c2.number_input("MİKTAR", format="%.3f")
    birim = c3.selectbox("BİRİM", BIRIM_LISTESI)
    fiyat = c4.number_input("BİRİM FİYAT (₺)")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data.get("DEPO"): st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    h_ad = col1.text_input("Hammadde Adı")
    h_mik = col2.number_input("Miktar", format="%.4f")
    h_bir = col3.selectbox("Birim", BIRIM_LISTESI)
    
    if col4.button("➕ EKLE"):
        if h_ad:
            st.session_state.temp_liste.append({"Hammadde": h_ad.upper(), "Miktar": h_mik, "Birim": h_bir})
            st.rerun()
            
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ TAMAMLA"):
            if urun:
                st.session_state.data["RECETELER"][urun] = {item["Hammadde"]: {"MİKTAR": item["Miktar"], "BİRİM": item["Birim"]} for item in st.session_state.temp_liste}
                verileri_kaydet(st.session_state.data)
                st.session_state.temp_liste = []
                st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN SEÇİN", list(st.session_state.data.get("RECETELER", {}).keys()))
    if secilen:
        df = pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T
        st.table(df)
        st.info("Düzenleme yapmak için yukarıdaki listeden madde ismini girip tanımlama ekranına gidebilirsiniz.")

# Diğer kısımlar... (Siparişler vs.)
