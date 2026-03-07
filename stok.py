import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

# ... (verileri_yukle ve verileri_kaydet fonksiyonları aynı) ...
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
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            with st.container(border=True):
                st.write(f"**No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Sipariş:** {s['ADET']} | **Üretilen:** {s.get('ÜRETİLEN', 0)}")
                
                # Üretim kısmı
                c1, c2 = st.columns([2, 1])
                miktar = c1.number_input(f"Üretim Miktarı ({s['NO']})", min_value=1, step=1, key=f"uretim_{i}")
                if c2.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                    recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                    # Hammadde kontrolü
                    hata = False
                    for mad, info in recete.items():
                        gerekli = info["MİKTAR"] * miktar
                        if mad not in st.session_state.data["DEPO"] or st.session_state.data["DEPO"][mad]["MİKTAR"] < gerekli:
                            hata = True; st.error(f"Eksik Hammadde: {mad}")
                    
                    if not hata:
                        for mad, info in recete.items():
                            st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                        s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                        verileri_kaydet(st.session_state.data); st.rerun()

                # Manuel Arşivleme/Kapatma kısmı
                if st.button("✅ SİPARİŞİ KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
                    s["KAPATILMA_TARİHİ"] = str(datetime.now())
                    st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                    verileri_kaydet(st.session_state.data); st.rerun()

# (Diğer menüler aynı şekilde kalabilir...)
