import streamlit as st
import json
import os
import pandas as pd

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]
SAYFA_BASI = 10

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []
if 'edit_malzeme' not in st.session_state: st.session_state.edit_malzeme = None

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    arama = st.text_input("🔍 MALZEME ARA").upper()
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    
    # Düzenleme modu: Seçili malzemeyi kutulara yükle
    mevcut_val = st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}) if st.session_state.edit_malzeme else {}
    
    kutu_isim = c1.text_input("MALZEME ADI", value=st.session_state.edit_malzeme or "")
    kutu_mik = c2.number_input("MİKTAR", value=float(mevcut_val.get("MİKTAR", 0.0)), format="%.3f")
    kutu_bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(mevcut_val.get("BİRİM", "ADET")) if mevcut_val.get("BİRİM") in BIRIM_LISTESI else 0)
    kutu_fiy = c4.number_input("FİYAT", value=float(mevcut_val.get("FİYAT", 0.0)), format="%.2f")
    
    if st.button("💾 KAYDET / GÜNCELLE"):
        st.session_state.data["DEPO"][kutu_isim] = {"MİKTAR": kutu_mik, "BİRİM": kutu_bir, "FİYAT": kutu_fiy}
        verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme = None; st.success("Kaydedildi."); st.rerun()

    st.write("---")
    # Sayfalamalı ve Aramalı Liste
    filtreli = {k: v for k, v in st.session_state.data["DEPO"].items() if arama in k.upper()}
    for k, v in filtreli.items():
        col1, col2 = st.columns([4, 1])
        # .get kullanımı ile KeyError hatasını kökten kestik
        mik = v.get("MİKTAR", 0)
        bir = v.get("BİRİM", "-")
        fiy = v.get("FİYAT", 0)
        col1.write(f"**{k}**: {mik} {bir} | {fiy} TL")
        if col2.button("✏️ Düzenle", key=f"edit_{k}"): 
            st.session_state.edit_malzeme = k; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)
        if st.button("✏️ DÜZENLE"): 
            st.session_state.temp_liste = [{"H": k, "M": v["MİKTAR"], "B": v["BİRİM"]} for k, v in st.session_state.data["RECETELER"][secilen].items()]
            st.warning("Düzenleme moduna geçildi, reçete tanımlama ekranına gidiniz."); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arsiv = st.session_state.data.get("ARSIV", [])
    for s in arsiv:
        # .get() ile KeyError'i önledik
        no = s.get('NO', '---')
        urun = s.get('ÜRÜN', 'Tanımsız')
        maliyet = s.get('MALIYET', 0.0)
        with st.expander(f"No: {no} | {urun} | Maliyet: {maliyet:.2f} ₺"):
            st.write(f"Not: {s.get('KAPATMA_NOTU', 'Yok')}")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))
