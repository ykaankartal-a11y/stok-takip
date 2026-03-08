import streamlit as st
import json
import os
import pandas as pd

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": []}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- REÇETE TANIMLA ---
if menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    col1, col2, col3, col4 = st.columns(4)
    h_ad = col1.text_input("Malzeme Adı").upper()
    h_mik = col2.number_input("Miktar", 0.0, format="%.4f")
    h_bir = col3.selectbox("Birim", BIRIM_LISTESI)
    h_fiy = col4.number_input("Birim Maliyet", 0.0, format="%.2f")
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir, "MALİYET": h_fiy}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- MEVCUT REÇETELER (Tam Kontrollü Satır Düzenleme) ---
elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.subheader(f"{secilen} İçeriği")
        # İŞÇİLİK EKLEME BUTONU
        if st.button("➕ İŞÇİLİK EKLE (Sabit)"):
            st.session_state.data["RECETELER"][secilen]["İŞÇİLİK"] = {"MİKTAR": 1, "BİRİM": "İŞÇİLİK(TL)", "MALİYET": 0}
            verileri_kaydet(st.session_state.data); st.rerun()
            
        # SATIR SATIR DÜZENLEME
        for mat, info in list(st.session_state.data["RECETELER"][secilen].items()):
            cols = st.columns([2, 1, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            m = cols[1].number_input("Mik", value=float(info['MİKTAR']), key=f"m_{mat}", format="%.4f")
            f = cols[2].number_input("Fiyat", value=float(info.get('MALİYET', 0)), key=f"f_{mat}", format="%.2f")
            b = cols[3].selectbox("Birim", BIRIM_LISTESI, index=BIRIM_LISTESI.index(info['BİRİM']), key=f"b_{mat}")
            if cols[4].button("💾 Kaydet", key=f"u_{mat}"):
                st.session_state.data["RECETELER"][secilen][mat] = {"MİKTAR": m, "BİRİM": b, "MALİYET": f}
                verileri_kaydet(st.session_state.data); st.rerun()
                
# --- DEPO & ARŞİV (Diğer modüller) ---
elif menu == "📦 DEPO":
    for k, v in st.session_state.data["DEPO"].items(): st.write(f"**{k}**: {v.get('MİKTAR')} {v.get('BİRİM')}")
elif menu == "📊 ARŞİV":
    for s in st.session_state.data.get("ARSIV", []): st.write(f"No: {s.get('NO')} tamamlandı.")
