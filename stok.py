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
if 'duzenlenen_urun' not in st.session_state: st.session_state.duzenlenen_urun = None

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO"])

# --- 1. REÇETE TANIMLAMA (YENİ) ---
if menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE OLUŞTUR")
    urun_adi = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Malzeme Adı")
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    
    if st.button("➕ Listeye Ekle"):
        if urun_adi not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun_adi] = {}
        st.session_state.data["RECETELER"][urun_adi][h_ad.upper()] = {"MİKTAR": h_mik, "BİRİM": h_bir}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- 2. MEVCUT REÇETELER (DETAYLI DÜZENLEME) ---
elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 REÇETE DÜZENLEME")
    urunler = list(st.session_state.data["RECETELER"].keys())
    secilen = st.selectbox("DÜZENLEMEK İÇİN ÜRÜN SEÇİN", [""] + urunler)
    
    if secilen:
        recete = st.session_state.data["RECETELER"][secilen]
        for mat, info in list(recete.items()):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**{mat}**")
            yeni_mik = col2.number_input("Mik", value=float(info['MİKTAR']), key=f"mik_{mat}", format="%.4f")
            yeni_bir = col3.selectbox("Birim", BIRIM_LISTESI, index=BIRIM_LISTESI.index(info['BİRİM']), key=f"bir_{mat}")
            
            if col4.button("💾 Güncelle", key=f"upd_{mat}"):
                recete[mat] = {"MİKTAR": yeni_mik, "BİRİM": yeni_bir}
                verileri_kaydet(st.session_state.data); st.rerun()
            if col4.button("❌ Sil", key=f"del_{mat}"):
                del recete[mat]; verileri_kaydet(st.session_state.data); st.rerun()

# --- 3. DEPO (PROFESYONEL) ---
elif menu == "📦 DEPO":
    st.header("📦 DEPO")
    # Düzenleme veya yeni giriş
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    isim = c1.text_input("MALZEME ADI")
    mik = c2.number_input("MİKTAR", format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI)
    fiy = c4.number_input("FİYAT", format="%.2f")
    
    if st.button("💾 Kaydet / Güncelle"):
        st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": bir, "FİYAT": fiy}
        verileri_kaydet(st.session_state.data); st.rerun()
        
    st.write("---")
    for k, v in st.session_state.data["DEPO"].items():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v.get('MİKTAR',0)} {v.get('BİRİM','-')} | {v.get('FİYAT',0)} ₺")
        if col2.button("✏️ Düzenle", key=f"edit_{k}"):
            # Buraya tıklandığında yukarıdaki kutulara veriyi otomatik taşıyacak bir logic eklenebilir
            pass
