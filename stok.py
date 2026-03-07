import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

# --- FONKSİYONLAR ---
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
if 'page' not in st.session_state: st.session_state.page = 1

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    c1, c2 = st.columns(2)
    mus = c1.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data["RECETELER"].keys())
    uru = c2.selectbox("ÜRÜN", urunler) if urunler else None
    c3, c4, c5 = st.columns(3)
    adet = c3.number_input("ADET", min_value=1, step=1)
    fiyat = c4.number_input("SATIŞ FİYATI (₺)", min_value=0.0, format="%.2f")
    termin = c5.date_input("TERMİN")
    if st.button("SİPARİŞİ ONAYLA") and uru:
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin), "ÜRETİLEN": 0, "MALIYET": 0.0})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            with st.container(border=True):
                st.write(f"**No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Adet:** {s['ADET']} | **Üretilen:** {s.get('ÜRETİLEN', 0)}")
                miktar = st.number_input(f"Üretim Miktarı ({s['NO']})", min_value=1, step=1, key=f"uretim_{i}")
                if st.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                    recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                    hata = False
                    for mad, info in recete.items():
                        if st.session_state.data["DEPO"].get(mad, {}).get("MİKTAR", 0) < (info["MİKTAR"] * miktar):
                            hata = True; st.error(f"Eksik Hammadde: {mad}")
                    if not hata:
                        for mad, info in recete.items(): 
                            st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                        s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                        verileri_kaydet(st.session_state.data); st.rerun()
                not_val = st.text_input("Kapatma Notu", key=f"not_{i}")
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
    if st.button("➕ EKLE"): st.session_state.temp_liste.append({"Hammadde": h_ad.upper(), "Miktar": h_mik, "Birim": h_bir})
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["Hammadde"]: {"MİKTAR": i["Miktar"], "BİRİM": i["Birim"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 REÇETE YÖNETİMİ")
    secilen = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        df = pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T
        st.table(df)
        if st.button("❌ SİL"): del st.session_state.data["RECETELER"][secilen]; verileri_kaydet(st.session_state.data); st.rerun()
        mad = st.selectbox("Düzenle", df.index.tolist())
        y_mik = st.number_input("Yeni Miktar", value=float(df.loc[mad, "MİKTAR"]))
        if st.button("✅ GÜNCELLE"): st.session_state.data["RECETELER"][secilen][mad]["MİKTAR"] = y_mik; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    st.header("📦 DEPO")
    c1, c2, c3 = st.columns(3)
    isim, miktar = c1.text_input("MALZEME").upper(), c2.number_input("MİKTAR", format="%.3f")
    birim = c3.selectbox("BİRİM", BIRIM_LISTESI)
    if st.button("KAYDET"): st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim}; verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arama = st.text_input("🔍 ARA (Kod/Müşteri/Ürün)").upper()
    df = pd.DataFrame(st.session_state.data["ARSIV"])
    if not df.empty:
        if arama: df = df[df.apply(lambda r: arama in str(r['NO']) or arama in str(r['MÜŞTERİ']) or arama in str(r['ÜRÜN']), axis=1)]
        s_bas = 10
        toplam = (len(df) - 1) // s_bas + 1
        cols = st.columns(min(toplam, 10))
        for i in range(min(toplam, 10)):
            if cols[i].button(str(i+1)): st.session_state.page = i+1; st.rerun()
        st.table(df.iloc[(st.session_state.page-1)*s_bas : st.session_state.page*s_bas])
