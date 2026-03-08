import streamlit as st
import json
import os
import pandas as pd
import math

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]
SAYFA_BASI = 10

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
if 'edit_malzeme' not in st.session_state: st.session_state.edit_malzeme = None
if 'page_depo' not in st.session_state: st.session_state.page_depo = 0
if 'page_arsiv' not in st.session_state: st.session_state.page_arsiv = 0

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- DEPO MODÜLÜ (DÜZENLEME VE LİSTELEME) ---
if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    # Düzenleme Formu
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("MİKTAR", 0)), format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("BİRİM", "ADET")) if st.session_state.edit_malzeme else 0)
    if c4.button("💾 KAYDET"): 
        st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": bir}
        verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme=None; st.rerun()
    
    st.write("---")
    arama = st.text_input("🔍 ARA").upper()
    filt = {k:v for k,v in st.session_state.data["DEPO"].items() if arama in k}
    
    for k, v in list(filt.items())[st.session_state.page_depo*SAYFA_BASI : (st.session_state.page_depo+1)*SAYFA_BASI]:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v.get('MİKTAR')} {v.get('BİRİM')}")
        if col2.button("✏️ Düzenle", key=f"e_{k}"): st.session_state.edit_malzeme = k; st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️ Önceki") and st.session_state.page_depo > 0: st.session_state.page_depo -= 1; st.rerun()
    if c3.button("Sonraki ➡️"): st.session_state.page_depo += 1; st.rerun()

# --- DİĞER MODÜLLER (Önceki kararlı yapılar korunarak...) ---
elif menu == "🛒 SİPARİŞ AÇ":
    # ... (Sipariş açma kodları)
    pass
elif menu == "📋 AKTİF SİPARİŞLER":
    # ... (Üretim ve not alma kodları)
    pass
elif menu == "⚙️ REÇETE TANIMLA":
    # ... (İşçilikli reçete tanımlama)
    pass
elif menu == "📋 MEVCUT REÇETELER":
    # ... (Satır bazlı düzenleme)
    pass
elif menu == "📊 ARŞİV":
    # ... (Arama ve sayfalamalı arşiv)
    pass
