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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📦 DEPO", "📊 ARŞİV"])

# --- MODAL: ÜRETİM GİRİŞİ ---
@st.dialog("🚀 ÜRETİM GİRİŞİ")
def uretim_modal(index):
    s = st.session_state.data["SIPARISLER"][index]
    miktar = st.number_input("Üretilecek Miktar", min_value=1, step=1)
    if st.button("ONAYLA VE ÜRET"):
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
            st.success("✅ Üretim Başarıyla Kaydedildi!"); st.rerun()

# --- MODÜLLER ---
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
        with st.expander(f"No: {s['NO']} | {s['MÜŞTERİ']} | {s['ÜRÜN']}"):
            if st.button("➕ ÜRETİM GİR", key=f"u_{i}"): uretim_modal(i)
            not_val = st.text_input("Kapatma Notu", key=f"n_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    if 'depo_edit' not in st.session_state: st.session_state.depo_edit = None
    arama = st.text_input("🔍 MALZEME ARA").upper()
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME", value=st.session_state.depo_edit or "")
    miktar = c2.number_input("MİKTAR", format="%.3f")
    birim = c3.selectbox("BİRİM", BIRIM_LISTESI)
    fiyat = c4.number_input("FİYAT", format="%.2f")
    if st.button("💾 KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.success("Kaydedildi."); st.rerun()
    
    # Sayfalamalı Tablo
    st.write("---")
    depo_items = {k: v for k, v in st.session_state.data["DEPO"].items() if arama in k}
    for k, v in depo_items.items():
        if st.button(f"✏️ Düzenle: {k}"): st.session_state.depo_edit = k; st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arsiv = st.session_state.data.get("ARSIV", [])
    for s in arsiv:
        with st.expander(f"No: {s['NO']} | {s['ÜRÜN']} | Maliyet: {s['MALIYET']:.2f} ₺"):
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))
