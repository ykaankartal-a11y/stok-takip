import streamlit as st
import json
import os
import pandas as pd
import math

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]
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

# --- 1. SİPARİŞ AÇ ---
if menu == "🛒 SİPARİŞ AÇ":
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    adet = st.number_input("ADET", min_value=1)
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "ÜRETİLEN": 0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.success("Sipariş açıldı!"); st.rerun()

# --- 2. AKTİF SİPARİŞLER (Üretim Girişli) ---
elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')} | Üretilen: {s.get('ÜRETİLEN')}"):
            miktar = st.number_input("Üretim Miktarı", 0, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                verileri_kaydet(st.session_state.data); st.rerun()
            not_val = st.text_input("Kapatma Notu", key=f"n_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

# --- 3. REÇETE (Maliyetli) ---
elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3, c4 = st.columns(4)
    h_ad = c1.text_input("Hammadde Adı").upper()
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    h_fiy = c4.number_input("Birim Maliyet (₺)", format="%.2f")
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir, "MALİYET": h_fiy}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- 4. MEVCUT REÇETELER ---
elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        for mat, info in list(st.session_state.data["RECETELER"][secilen].items()):
            cols = st.columns([2, 1, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            m = cols[1].number_input("Mik", value=float(info['MİKTAR']), key=f"m_{mat}", format="%.4f")
            f = cols[2].number_input("Mal", value=float(info.get('MALİYET', 0)), key=f"f_{mat}", format="%.2f")
            b = cols[3].selectbox("Bir", BIRIM_LISTESI, index=BIRIM_LISTESI.index(info['BİRİM']), key=f"b_{mat}")
            if cols[4].button("💾 Kaydet", key=f"u_{mat}"):
                st.session_state.data["RECETELER"][secilen][mat] = {"MİKTAR": m, "MALİYET": f, "BİRİM": b}
                verileri_kaydet(st.session_state.data); st.rerun()

# --- 5. DEPO (Hata Korumalı + Sayfalamalı) ---
elif menu == "📦 DEPO":
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("MİKTAR", 0)), format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("BİRİM", "ADET")) if st.session_state.edit_malzeme else 0)
    if st.button("💾 KAYDET"): st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": bir}; verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme=None; st.rerun()
    
    arama = st.text_input("🔍 ARA").upper()
    filt = {k:v for k,v in st.session_state.data["DEPO"].items() if arama in k}
    for k, v in list(filt.items())[st.session_state.page_depo*SAYFA_BASI : (st.session_state.page_depo+1)*SAYFA_BASI]:
        col1, col2 = st.columns([4, 1])
        # .get kullanımı ile hata koruması
        col1.write(f"**{k}**: {v.get('MİKTAR', 0)} {v.get('BİRİM', '-')}")
        if col2.button("✏️ Düzenle", key=f"e_{k}"): st.session_state.edit_malzeme = k; st.rerun()

# --- 6. ARŞİV (Aramalı + Sayfalamalı) ---
elif menu == "📊 ARŞİV":
    arama = st.text_input("🔍 Sipariş Ara").upper()
    arsiv = [s for s in st.session_state.data.get("ARSIV", []) if arama in str(s.get('MÜŞTERİ', '')).upper()]
    for s in arsiv[st.session_state.page_arsiv*SAYFA_BASI : (st.session_state.page_arsiv+1)*SAYFA_BASI]:
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')}"):
            st.write(f"Not: {s.get('KAPATMA_NOTU', '-')}")
