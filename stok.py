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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- 1. SİPARİŞ AÇ ---
if menu == "🛒 SİPARİŞ AÇ":
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    c1, c2 = st.columns(2)
    adet = c1.number_input("ADET", min_value=1)
    termin = c2.date_input("TERMİN TARİHİ")
    fiyat = st.number_input("SATIŞ FİYATI", format="%.2f")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "TERMİN": str(termin), "FİYAT": fiyat, "ÜRETİLEN": 0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.success("Sipariş açıldı!"); st.rerun()

# --- 2. AKTİF SİPARİŞLER ---
elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            miktar = st.number_input("Üretim Miktarı", 0, key=f"u_{i}")
            not_val = st.text_input("Kapatma Notu", key=f"n_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                # Maliyet Hesabı (Tüm kalemler + İşçilik)
                recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                for mat, info in recete.items():
                    s["DETAY"][mat] = s.get("DETAY", {}).get(mat, 0) + (miktar * info.get("MİKTAR", 0) * info.get("MALİYET", 0))
                verileri_kaydet(st.session_state.data); st.rerun()
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

# --- 3. REÇETE TANIMLA (İşçilikli) ---
elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3, c4 = st.columns(4)
    h_ad = c1.text_input("Malzeme Adı").upper()
    h_mik = c2.number_input("Miktar", 0.0)
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    h_fiy = c4.number_input("Maliyet", 0.0)
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir, "MALİYET": h_fiy}
        verileri_kaydet(st.session_state.data); st.rerun()
    st.write("---")
    isc_fiyat = st.number_input("İŞÇİLİK BEDELİ (TL)", 0.0)
    if st.button("➕ İŞÇİLİK EKLE"):
        st.session_state.data["RECETELER"][urun]["İŞÇİLİK"] = {"MİKTAR": 1, "BİRİM": "İŞÇİLİK(TL)", "MALİYET": isc_fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- 4. MEVCUT REÇETELER ---
elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        for mat, info in list(st.session_state.data["RECETELER"][secilen].items()):
            cols = st.columns([2, 1, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            m = cols[1].number_input("Mik", value=float(info['MİKTAR']), key=f"m_{mat}")
            f = cols[2].number_input("Fiyat", value=float(info.get('MALİYET', 0)), key=f"f_{mat}")
            if cols[4].button("Kaydet", key=f"u_{mat}"):
                st.session_state.data["RECETELER"][secilen][mat] = {"MİKTAR": m, "MALİYET": f, "BİRİM": info['BİRİM']}; verileri_kaydet(st.session_state.data); st.rerun()

# --- 5. DEPO & 6. ARŞİV (Eski Stabil Hal) ---
elif menu == "📦 DEPO":
    for k, v in st.session_state.data["DEPO"].items(): st.write(f"**{k}**: {v.get('MİKTAR')} {v.get('BİRİM')}")
elif menu == "📊 ARŞİV":
    for s in st.session_state.data.get("ARSIV", []):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')}"):
            st.write(f"Not: {s.get('KAPATMA_NOTU')}")
            st.metric("Toplam Maliyet", f"{sum(s.get('DETAY', {}).values()):.2f} ₺")
