import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]

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
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s['NO']} | Müşteri: {s['MÜŞTERİ']} | Ürün: {s['ÜRÜN']}"):
            st.write(f"**Üretim:** {s.get('ÜRETİLEN', 0)} / {s['ADET']}")
            miktar = st.number_input(f"Üretim Miktarı", 1, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                hata, maliyet = False, 0
                for mad, info in recete.items():
                    if mad == "İŞÇİLİK":
                        maliyet += (info["MİKTAR"] * miktar) # İşçilikte direkt TL tutarını ekle
                    else:
                        if st.session_state.data["DEPO"].get(mad, {}).get("MİKTAR", 0) < (info["MİKTAR"] * miktar):
                            hata = True; st.error(f"Eksik Hammadde: {mad}")
                        else: maliyet += (info["MİKTAR"] * miktar) * st.session_state.data["DEPO"][mad].get("FİYAT", 0)
                if not hata:
                    for mad, info in recete.items():
                        if mad != "İŞÇİLİK": st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                    s["ÜRETİLEN"] += miktar; s["MALIYET"] += maliyet
                    verileri_kaydet(st.session_state.data); st.rerun()
            not_val = st.text_input("Kapatma Notu", key=f"not_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val; s["KAPATILMA_TARİHİ"] = str(datetime.now())
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    h_ad = st.text_input("Hammadde Adı (İşçilik için 'İŞÇİLİK' yaz)").upper()
    h_mik = st.number_input("Miktar / Tutar", format="%.4f")
    h_bir = st.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"): st.session_state.temp_liste.append({"Hammadde": h_ad, "Miktar": h_mik, "Birim": h_bir})
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["Hammadde"]: {"MİKTAR": i["Miktar"], "BİRİM": i["Birim"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        df = pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T
        st.table(df)
        if st.button("❌ SİL"): del st.session_state.data["RECETELER"][secilen]; verileri_kaydet(st.session_state.data); st.rerun()
        mad = st.selectbox("Düzenle", df.index.tolist())
        y_mik = st.number_input("Yeni Değer", value=float(df.loc[mad, "MİKTAR"]))
        if st.button("✅ GÜNCELLE"): st.session_state.data["RECETELER"][secilen][mad]["MİKTAR"] = y_mik; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    c1, c2, c3, c4 = st.columns(4)
    isim, miktar = c1.text_input("MALZEME").upper(), c2.number_input("MİKTAR", format="%.3f")
    birim, fiyat = c3.selectbox("BİRİM", BIRIM_LISTESI), c4.number_input("BİRİM FİYAT", format="%.2f")
    if st.button("KAYDET"): st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}; verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV - MALİYET KARTLARI")
    for s in st.session_state.data["ARSIV"]:
        with st.expander(f"No: {s['NO']} | {s['MÜŞTERİ']} | {s['ÜRÜN']}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Satış", f"{s['FİYAT']} ₺")
            c2.metric("Maliyet", f"{s['MALIYET']:.2f} ₺")
            c3.metric("Kâr", f"{s['FİYAT'] - s['MALIYET']:.2f} ₺")
            st.write(f"**Not:** {s.get('KAPATMA_NOTU', 'Yok')}")
