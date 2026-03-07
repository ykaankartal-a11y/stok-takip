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

# Session state başlatıcıları
if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ SİSTEMİ ---
menu = st.sidebar.radio("MENÜ", [
    "🛒 SİPARİŞ AÇ", 
    "📋 AKTİF SİPARİŞLER", 
    "⚙️ REÇETE TANIMLA", 
    "📋 MEVCUT REÇETELER", 
    "📦 DEPO", 
    "📊 ARŞİV"
])

# --- MODÜLLER ---

# 1. SİPARİŞ AÇ
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
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin)})
        verileri_kaydet(st.session_state.data); st.rerun()

# 2. AKTİF SİPARİŞLER
elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    for i, s in enumerate(st.session_state.data.get("SIPARISLER", [])):
        st.write(f"**{s['MÜŞTERİ']}** | {s['ÜRÜN']} | {s['ADET']} Adet | Termin: {s['TERMİN']}")
        if st.button("KAPAT VE ARŞİVLE", key=f"k_{i}"):
            st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
            verileri_kaydet(st.session_state.data); st.rerun()

# 3. REÇETE TANIMLA (DÜZELTİLDİ)
elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    h_ad = col1.text_input("Hammadde Adı")
    h_mik = col2.number_input("Miktar", format="%.4f")
    h_bir = col3.selectbox("Birim", BIRIM_LISTESI)
    
    if col4.button("➕ LİSTEYE EKLE"):
        if h_ad:
            st.session_state.temp_liste.append({"Hammadde": h_ad.upper(), "Miktar": h_mik, "Birim": h_bir})
            st.rerun()
    
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ KAYDET"):
            if urun:
                st.session_state.data["RECETELER"][urun] = {item["Hammadde"]: {"MİKTAR": item["Miktar"], "BİRİM": item["Birim"]} for item in st.session_state.temp_liste}
                verileri_kaydet(st.session_state.data)
                st.session_state.temp_liste = []
                st.success("Reçete kaydedildi!")
                st.rerun()
        if st.button("❌ LİSTEYİ SIFIRLA"):
            st.session_state.temp_liste = []
            st.rerun()

# 4. MEVCUT REÇETELER
elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        data_list = [{"Hammadde": mad, "Miktar": info["MİKTAR"], "Birim": info["BİRİM"]} for mad, info in st.session_state.data["RECETELER"][secilen].items()]
        df = pd.DataFrame(data_list)
        st.table(df)
        mad_sec = st.selectbox("Düzenlenecek Maddeyi Seç", df["Hammadde"].tolist())
        yeni_mik = st.number_input("Yeni Miktar", value=float(df.loc[df["Hammadde"] == mad_sec, "Miktar"].values[0]))
        yeni_bir = st.selectbox("Yeni Birim", BIRIM_LISTESI, index=BIRIM_LISTESI.index(df.loc[df["Hammadde"] == mad_sec, "Birim"].values[0]))
        if st.button("✅ GÜNCELLE"):
            st.session_state.data["RECETELER"][secilen][mad_sec] = {"MİKTAR": yeni_mik, "BİRİM": yeni_bir}
            verileri_kaydet(st.session_state.data); st.rerun()

# 5. DEPO
elif menu == "📦 DEPO":
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

# 6. ARŞİV
elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data.get("ARSIV"): st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
