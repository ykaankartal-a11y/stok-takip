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
                return json.load(f)
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

menu = st.sidebar.radio("MENÜ", ["⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER"])

# --- MODÜLLER ---

if menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    h_ad = col1.text_input("Hammadde")
    h_mik = col2.number_input("Miktar", format="%.4f")
    h_bir = col3.selectbox("Birim", BIRIM_LISTESI)
    
    if col4.button("➕ EKLE"):
        if urun and h_ad:
            if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
            st.session_state.data["RECETELER"][urun][h_ad.upper()] = {"MİKTAR": h_mik, "BİRİM": h_bir}
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    urunler = list(st.session_state.data["RECETELER"].keys())
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + urunler)
    
    if secilen:
        # Reçeteyi tablo olarak göster
        st.subheader(f"{secilen} Reçetesi")
        data_list = []
        for mad, info in st.session_state.data["RECETELER"][secilen].items():
            data_list.append({"Hammadde": mad, "Miktar": info["MİKTAR"], "Birim": info["BİRİM"]})
        
        df = pd.DataFrame(data_list)
        st.table(df)

        # Düzenleme Bölümü
        st.write("---")
        st.subheader("✏️ Madde Düzenle")
        mad_sec = st.selectbox("Düzenlenecek Maddeyi Seç", df["Hammadde"].tolist())
        
        yeni_mik = st.number_input("Yeni Miktar", value=float(df.loc[df["Hammadde"] == mad_sec, "Miktar"].values[0]))
        yeni_bir = st.selectbox("Yeni Birim", BIRIM_LISTESI, index=BIRIM_LISTESI.index(df.loc[df["Hammadde"] == mad_sec, "Birim"].values[0]))
        
        if st.button("✅ GÜNCELLE"):
            st.session_state.data["RECETELER"][secilen][mad_sec] = {"MİKTAR": yeni_mik, "BİRİM": yeni_bir}
            verileri_kaydet(st.session_state.data)
            st.success("Güncellendi!")
            st.rerun()
