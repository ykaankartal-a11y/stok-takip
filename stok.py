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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

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
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    col_m, col_k = st.columns([3, 1])
    m_ad = col_m.text_input("Hammadde Adı")
    m_mik = col_k.number_input("Miktar", format="%.4f")
    
    if st.button("EKLE"):
        if urun and m_ad:
            if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
            st.session_state.data["RECETELER"][urun][m_ad.upper()] = m_mik
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    urunler = list(st.session_state.data.get("RECETELER", {}).keys())
    secilen = st.selectbox("ÜRÜN SEÇİN", urunler)
    
    if secilen:
        st.subheader(f"{secilen} Detayları")
        malzemeler = st.session_state.data["RECETELER"][secilen]
        for mad, mik in malzemeler.items():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{mad}**: {mik}")
            if c3.button("✏️", key=f"edit_{mad}"):
                st.session_state.duzenlenen = (secilen, mad, mik)
                st.rerun()

        # Düzenleme paneli (Aktifse görünür)
        if 'duzenlenen' in st.session_state:
            u, m, eskimik = st.session_state.duzenlenen
            st.warning(f"{u} içindeki {m} maddesini düzenliyorsunuz:")
            yeni_mik = st.number_input("Yeni Miktar", value=eskimik)
            if st.button("GÜNCELLE"):
                st.session_state.data["RECETELER"][u][m] = yeni_mik
                verileri_kaydet(st.session_state.data)
                del st.session_state.duzenlenen
                st.rerun()

elif menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", list(st.session_state.data.get("RECETELER", {}).keys()))
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "TARİH": str(datetime.now().date())})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    for i, s in enumerate(st.session_state.data.get("SIPARISLER", [])):
        st.write(f"**{s['MÜŞTERİ']}** | {s['ÜRÜN']}")
        if st.button("KAPAT VE ARŞİVLE", key=f"k_{i}"):
            st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data.get("ARSIV"): st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
