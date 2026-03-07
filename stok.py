import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

VERI_DOSYASI = "stok_verileri.json"

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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    c1, c2 = st.columns(2)
    mus = c1.text_input("MÜŞTERİ ADI").upper()
    uru = c2.selectbox("ÜRÜN", list(st.session_state.data["RECETELER"].keys()))
    adet = st.number_input("SİPARİŞ ADEDİ", min_value=1, step=1)
    
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({
            "NO": st.session_state.data["SIPARIS_SAYAC"],
            "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "ÜRETİLEN": 0
        })
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        kalan = s["ADET"] - s["ÜRETİLEN"]
        with st.container(border=True):
            st.write(f"**Sipariş No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Toplam:** {s['ADET']} | **Üretilen:** {s['ÜRETİLEN']} | **Kalan:** {kalan}")
            
            # Üretim girişi
            uretim_miktari = st.number_input(f"Üretim Adedi ({s['NO']})", min_value=1, max_value=kalan, step=1, key=f"uretim_{i}")
            
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                # Hammadde kontrol
                hata = False
                for mad, info in recete.items():
                    gerekli = info["MİKTAR"] * uretim_miktari
                    if mad not in st.session_state.data["DEPO"] or st.session_state.data["DEPO"][mad]["MİKTAR"] < gerekli:
                        hata = True; st.error(f"Eksik Hammadde: {mad}")
                
                if not hata:
                    for mad, info in recete.items():
                        st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * uretim_miktari)
                    
                    s["ÜRETİLEN"] += uretim_miktari
                    if s["ÜRETİLEN"] >= s["ADET"]:
                        st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                    verileri_kaydet(st.session_state.data); st.rerun()

# [DİĞER MODÜLLER (REÇETE, DEPO, ARŞİV) AYNI KALABİLİR]
elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLA")
    # ... (önceki reçete koduyla aynı) ...
    pass

elif menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    # ... (önceki depo koduyla aynı) ...
    pass
