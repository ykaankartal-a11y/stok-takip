import streamlit as st
import json
import os
import pandas as pd

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]

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

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ AÇ")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    c1, c2 = st.columns(2)
    adet = c1.number_input("ADET", min_value=1)
    fiyat = c2.number_input("SATIŞ FİYATI", format="%.2f")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "ÜRETİLEN": 0, "MALIYET": 0.0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Malzeme Adı").upper()
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir}
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        recete = st.session_state.data["RECETELER"][secilen]
        for mat, info in list(recete.items()):
            cols = st.columns([3, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            yeni_mik = cols[1].number_input("Miktar", value=float(info['MİKTAR']), key=f"mik_{mat}", format="%.4f")
            if cols[2].button("💾 Güncelle", key=f"upd_{mat}"):
                recete[mat]['MİKTAR'] = yeni_mik
                verileri_kaydet(st.session_state.data); st.rerun()
            if cols[3].button("❌ Sil", key=f"del_{mat}"):
                del recete[mat]; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    st.header("📦 DEPO")
    arama = st.text_input("🔍 MALZEME ARA").upper()
    for k, v in {k:v for k,v in st.session_state.data["DEPO"].items() if arama in k}.items():
        st.write(f"**{k}**: {v.get('MİKTAR')} {v.get('BİRİM')}")

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    for s in st.session_state.data.get("ARSIV", []):
        with st.expander(f"No: {s.get('NO', '---')} | {s.get('ÜRÜN', 'Tanımsız')}"):
            st.write(f"Maliyet: {s.get('MALIYET', 0):.2f} ₺")
