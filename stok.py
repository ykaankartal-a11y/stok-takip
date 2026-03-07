import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

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

menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    c1, c2 = st.columns(2)
    mus = c1.text_input("MÜŞTERİ ADI").upper()
    uru = c2.selectbox("ÜRÜN", list(st.session_state.data["RECETELER"].keys()))
    c3, c4, c5 = st.columns(3)
    adet = c3.number_input("ADET", min_value=1, step=1)
    fiyat = c4.number_input("TOPLAM FİYAT (₺)", min_value=0.0)
    termin = c5.date_input("TERMİN TARİHİ")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "ID": datetime.now().strftime("%Y%m%d%H%M%S%f"), "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin)})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**Sipariş No:** {s['NO']} | **Müşteri:** {s['MÜŞTERİ']} | **Ürün:** {s['ÜRÜN']} ({s['ADET']} Adet)")
                
                # Hammaddeyi tablo olarak göster
                recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                df_recete = pd.DataFrame(recete).T
                c1.write("**Gerekli Hammadde:**")
                c1.table(df_recete)
                
                not_val = c2.text_input("Not", key=f"not_{i}")
                if c2.button("🚀 ÜRET VE ARŞİVLE", key=f"btn_{i}", type="primary"):
                    hata = False
                    for mad, info in recete.items():
                        gerekli = info["MİKTAR"] * s["ADET"]
                        if mad in st.session_state.data["DEPO"] and st.session_state.data["DEPO"][mad]["MİKTAR"] >= gerekli:
                            st.session_state.data["DEPO"][mad]["MİKTAR"] -= gerekli
                        else: hata = True; st.error(f"Eksik: {mad}")
                    if not hata:
                        s["KAPATMA_NOTU"] = not_val; s["KAPATILMA_TARİHİ"] = str(datetime.now())
                        st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ YENİ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    h_ad = c1.text_input("Hammadde Adı")
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if c4.button("➕ LİSTEYE EKLE"):
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
    if secilen:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)
        if st.button("❌ REÇETEYİ SİL"): del st.session_state.data["RECETELER"][secilen]; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3, c4 = st.columns(4)
    isim, miktar, birim, fiyat = c1.text_input("MALZEME"), c2.number_input("MİKTAR", format="%.3f"), c3.selectbox("BİRİM", BIRIM_LISTESI), c4.number_input("FİYAT")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data["ARSIV"]: st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
