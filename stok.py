import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
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

# --- MENÜ SİSTEMİ ---
menu = st.sidebar.radio("MENÜ", [
    "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", 
    "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"
])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data.get("RECETELER", {}).keys())
    uru = st.selectbox("ÜRÜN", urunler)
    adet = st.number_input("SİPARİŞ ADEDİ", min_value=1, step=1)
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({
            "NO": st.session_state.data["SIPARIS_SAYAC"],
            "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "ÜRETİLEN": 0
        })
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]:
        st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            kalan = s["ADET"] - s["ÜRETİLEN"]
            with st.container(border=True):
                st.write(f"**No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Toplam:** {s['ADET']} | **Üretilen:** {s['ÜRETİLEN']} | **Kalan:** {kalan}")
                miktar = st.number_input(f"Üretim Miktarı ({s['NO']})", 1, kalan, key=f"uretim_{i}")
                if st.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                    recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                    hata = False
                    for mad, info in recete.items():
                        gerekli = info["MİKTAR"] * miktar
                        if mad not in st.session_state.data["DEPO"] or st.session_state.data["DEPO"][mad]["MİKTAR"] < gerekli:
                            hata = True; st.error(f"Eksik Hammadde: {mad}")
                    if not hata:
                        for mad, info in recete.items():
                            st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                        s["ÜRETİLEN"] += miktar
                        if s["ÜRETİLEN"] >= s["ADET"]:
                            st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    h_ad = st.text_input("Hammadde Adı")
    h_mik = st.number_input("Miktar", format="%.4f")
    h_bir = st.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ LİSTEYE EKLE"):
        st.session_state.temp_liste.append({"Hammadde": h_ad.upper(), "Miktar": h_mik, "Birim": h_bir})
        st.rerun()
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 REÇETEYİ KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["Hammadde"]: {"MİKTAR": i["Miktar"], "BİRİM": i["Birim"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen: st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)

elif menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    isim, miktar = st.text_input("MALZEME").upper(), st.number_input("MİKTAR", format="%.3f")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data["ARSIV"]: st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
