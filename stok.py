import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ VE DOSYA YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

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
if 'temp_liste' not in st.session_state: st.session_state.temp_liste = []

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data["RECETELER"].keys())
    uru = st.selectbox("ÜRÜN", urunler) if urunler else None
    adet = st.number_input("SİPARİŞ ADEDİ", min_value=1, step=1)
    if st.button("SİPARİŞİ ONAYLA") and uru:
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "ÜRETİLEN": 0})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            with st.container(border=True):
                st.write(f"**No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Sipariş:** {s['ADET']} | **Üretilen:** {s.get('ÜRETİLEN', 0)}")
                c1, c2 = st.columns([2, 1])
                miktar = c1.number_input(f"Üretim Adedi ({s['NO']})", min_value=1, step=1, key=f"uretim_{i}")
                if c2.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                    recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                    hata = False
                    for mad, info in recete.items():
                        gerekli = info["MİKTAR"] * miktar
                        if mad not in st.session_state.data["DEPO"] or st.session_state.data["DEPO"][mad]["MİKTAR"] < gerekli:
                            hata = True; st.error(f"Eksik Hammadde: {mad}")
                    if not hata:
                        for mad, info in recete.items(): st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                        s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                        verileri_kaydet(st.session_state.data); st.rerun()
                
                not_val = st.text_input(f"Kapatma Notu", key=f"not_{i}")
                if st.button("✅ SİPARİŞİ KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
                    s["KAPATMA_NOTU"] = not_val
                    s["KAPATILMA_TARİHİ"] = str(datetime.now())
                    st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                    verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    
    # 1. Arama Bloğu (Sipariş Kodu, Müşteri, Ürün)
    arama = st.text_input("🔍 ARA (Sipariş No, Müşteri veya Ürün)").upper()
    df = pd.DataFrame(st.session_state.data["ARSIV"])
    
    if not df.empty:
        # Filtreleme
        if arama:
            df = df[df.apply(lambda row: arama in str(row['NO']) or arama in str(row['MÜŞTERİ']) or arama in str(row['ÜRÜN']), axis=1)]
        
        # 2. Sayfalandırma (Butonlu)
        s_bas = 10
        toplam_sayfa = (len(df) - 1) // s_bas + 1
        
        # Sayfa durumu yönetimi
        if 'page' not in st.session_state: st.session_state.page = 1
        
        # Buton satırı
        cols = st.columns(min(toplam_sayfa, 10))
        for i in range(toplam_sayfa):
            if cols[i].button(str(i+1)): st.session_state.page = i+1
        
        st.table(df.iloc[(st.session_state.page-1)*s_bas : st.session_state.page*s_bas])
    else: st.info("Arşiv boş.")
