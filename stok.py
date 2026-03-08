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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODAL: ÜRETİM GİRİŞİ ---
@st.dialog("🚀 ÜRETİM GİRİŞİ")
def uretim_modal(index):
    s = st.session_state.data["SIPARISLER"][index]
    miktar = st.number_input("Üretilecek Miktar", min_value=1, step=1)
    if st.button("ONAYLA"):
        recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
        hata, toplam_maliyet, anlik_detay = False, 0, {}
        for mad, info in recete.items():
            req = info["MİKTAR"] * miktar
            if mad == "İŞÇİLİK":
                toplam_maliyet += req
                anlik_detay["İŞÇİLİK"] = anlik_detay.get("İŞÇİLİK", 0) + req
            else:
                stok = st.session_state.data["DEPO"].get(mad, {})
                if stok.get("MİKTAR", 0) < req: hata = True; st.error(f"Eksik: {mad}")
                else:
                    tutar = req * stok.get("FİYAT", 0)
                    toplam_maliyet += tutar
                    anlik_detay[mad] = anlik_detay.get(mad, 0) + tutar
                    st.session_state.data["DEPO"][mad]["MİKTAR"] -= req
        if not hata:
            s["ÜRETİLEN"] += miktar; s["MALIYET"] += toplam_maliyet
            for k, v in anlik_detay.items(): s["DETAY"][k] = s.get("DETAY", {}).get(k, 0) + v
            verileri_kaydet(st.session_state.data)
            st.success("✅ Üretim Kaydedildi!"); st.rerun()

# --- MENÜLER ---
if menu == "🛒 SİPARİŞ AÇ":
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    c1, c2 = st.columns(2)
    adet = c1.number_input("ADET", min_value=1)
    fiyat = c2.number_input("SATIŞ FİYATI", format="%.2f")
    if st.button("SİPARİŞİ ONAYLA"):
        if mus and uru:
            st.session_state.data["SIPARIS_SAYAC"] += 1
            st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "ÜRETİLEN": 0, "MALIYET": 0.0, "DETAY": {}})
            verileri_kaydet(st.session_state.data); st.success("Sipariş Açıldı!"); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s['NO']} | {s['MÜŞTERİ']} | {s['ÜRÜN']} | Üretilen: {s['ÜRETİLEN']} | Maliyet: {s['MALIYET']:.2f} ₺"):
            if st.button("➕ ÜRETİM GİR", key=f"u_{i}"): uretim_modal(i)
            not_val = st.text_input("Kapatma Notu", key=f"n_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Hammadde/İşçilik")
    h_mik = c2.number_input("Miktar/Tutar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"): st.session_state.temp_liste.append({"H": h_ad.upper(), "M": h_mik, "B": h_bir}); st.rerun()
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["H"]: {"MİKTAR": i["M"], "BİRİM": i["B"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.success("Reçete Kaydedildi!"); st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T)
        if st.button("❌ SİL"): del st.session_state.data["RECETELER"][secilen]; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    isim = st.text_input("MALZEME ARA/EKLE").upper()
    c1, c2, c3 = st.columns(3)
    miktar = c1.number_input("MİKTAR", format="%.3f")
    birim = c2.selectbox("BİRİM", BIRIM_LISTESI)
    fiyat = c3.number_input("FİYAT", format="%.2f")
    if st.button("💾 KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.success("Depo Güncellendi!"); st.rerun()
    st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "📊 ARŞİV":
    for s in st.session_state.data.get("ARSIV", []):
        with st.expander(f"No: {s['NO']} | {s['ÜRÜN']} | Maliyet: {s['MALIYET']:.2f} ₺"):
            st.write(f"Not: {s.get('KAPATMA_NOTU')}")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))
