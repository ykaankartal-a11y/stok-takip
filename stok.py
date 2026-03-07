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

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    h_ad, h_mik = st.text_input("Hammadde Adı"), st.number_input("Miktar", format="%.4f")
    h_bir = st.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ LİSTEYE EKLE"): st.session_state.temp_liste.append({"Hammadde": h_ad.upper(), "Miktar": h_mik, "Birim": h_bir})
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["Hammadde"]: {"MİKTAR": i["Miktar"], "BİRİM": i["Birim"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)
        if st.button("❌ SİL"): del st.session_state.data["RECETELER"][secilen]; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    isim, miktar = st.text_input("MALZEME").upper(), st.number_input("MİKTAR", format="%.3f")
    if st.button("KAYDET"): st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar}; verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arama = st.text_input("🔍 ARA (Müşteri veya Ürün)").upper()
    df = pd.DataFrame(st.session_state.data["ARSIV"])
    if not df.empty:
        if arama: df = df[df.apply(lambda row: arama in str(row['MÜŞTERİ']) or arama in str(row['ÜRÜN']), axis=1)]
        sayfa_basina = 10
        sayfa = st.number_input("Sayfa", 1, max(1, (len(df)-1)//sayfa_basina + 1), 1)
        st.table(df.iloc[(sayfa-1)*sayfa_basina : sayfa*sayfa_basina])
    else: st.info("Arşiv boş.")
