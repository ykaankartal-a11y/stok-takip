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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []
if 'edit_malzeme' not in st.session_state: st.session_state.edit_malzeme = None
if 'duzenlenen_urun' not in st.session_state: st.session_state.duzenlenen_urun = ""

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- REÇETE TANIMLAMA ---
if menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLAMA")
    urun = st.text_input("ÜRÜN ADI", value=st.session_state.duzenlenen_urun)
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Malzeme Adı")
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    
    if st.button("➕ Listeye Ekle"):
        st.session_state.temp_liste.append({"H": h_ad.upper(), "M": h_mik, "B": h_bir})
        st.rerun()
    
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["H"]: {"MİKTAR": i["M"], "BİRİM": i["B"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data)
            st.session_state.temp_liste = []
            st.session_state.duzenlenen_urun = ""
            st.success("Reçete kaydedildi!"); st.rerun()
        if st.button("❌ Listeyi Temizle"): st.session_state.temp_liste = []; st.rerun()

# --- MEVCUT REÇETELER ---
elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)
        if st.button("✏️ Düzenle"):
            st.session_state.temp_liste = [{"H": k, "M": v["MİKTAR"], "B": v["BİRİM"]} for k, v in st.session_state.data["RECETELER"][secilen].items()]
            st.session_state.duzenlenen_urun = secilen
            st.info("Reçete tanımlama ekranına gidip düzenleyebilirsiniz.")

# --- DEPO ---
elif menu == "📦 DEPO":
    st.header("📦 DEPO")
    arama = st.text_input("🔍 ARA").upper()
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    mev = st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}) if st.session_state.edit_malzeme else {}
    
    isim = c1.text_input("MALZEME", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(mev.get("MİKTAR", 0)), format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(mev.get("BİRİM", "ADET")) if mev.get("BİRİM") in BIRIM_LISTESI else 0)
    fiy = c4.number_input("FİYAT", value=float(mev.get("FİYAT", 0)), format="%.2f")
    
    if st.button("💾 KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": mik, "BİRİM": bir, "FİYAT": fiy}
        verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme = None; st.rerun()
    
    for k, v in {k: v for k, v in st.session_state.data["DEPO"].items() if arama in k}.items():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v.get('MİKTAR',0)} {v.get('BİRİM','-')} | {v.get('FİYAT',0)} ₺")
        if col2.button("✏️ Düzenle", key=f"e_{k}"): st.session_state.edit_malzeme = k; st.rerun()

# (Sipariş ve Arşiv modülleri aynı mantıkla devam eder...)
