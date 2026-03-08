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
if 'edit_malzeme' not in st.session_state: st.session_state.edit_malzeme = None

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- MODAL: ÜRETİM ---
@st.dialog("🚀 ÜRETİM GİRİŞİ")
def uretim_modal(index):
    s = st.session_state.data["SIPARISLER"][index]
    miktar = st.number_input("Üretilecek Miktar", min_value=1, step=1)
    if st.button("ONAYLA"):
        recete = st.session_state.data["RECETELER"].get(s.get('ÜRÜN'), {})
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
            s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
            s["MALIYET"] = s.get("MALIYET", 0) + toplam_maliyet
            for k, v in anlik_detay.items(): s["DETAY"][k] = s.get("DETAY", {}).get(k, 0) + v
            verileri_kaydet(st.session_state.data); st.rerun()

# --- MODÜLLER ---
if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    arama = st.text_input("🔍 MALZEME ARA").upper()
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    
    # Düzenleme modu
    kutu_isim = c1.text_input("MALZEME ADI", value=st.session_state.edit_malzeme or "")
    kutu_mik = c2.number_input("MİKTAR", value=st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("MİKTAR", 0.0), format="%.3f")
    kutu_bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("BİRİM", "ADET")) if st.session_state.edit_malzeme else 0)
    kutu_fiy = c4.number_input("FİYAT", value=st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("FİYAT", 0.0), format="%.2f")
    
    if st.button("💾 KAYDET / GÜNCELLE"):
        st.session_state.data["DEPO"][kutu_isim] = {"MİKTAR": kutu_mik, "BİRİM": kutu_bir, "FİYAT": kutu_fiy}
        verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme = None; st.rerun()

    # Sayfalamalı Tablo
    filtreli = {k: v for k, v in st.session_state.data["DEPO"].items() if arama in k.upper()}
    for k, v in filtreli.items():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v['MİKTAR']} {v['BİRİM']} | {v['FİYAT']} TL")
        if col2.button("✏️ Düzenle", key=f"edit_{k}"): st.session_state.edit_malzeme = k; st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        df = pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T
        st.table(df)
        if st.button("✏️ REÇETEYİ DÜZENLE"): st.session_state.temp_liste = [{"H": k, "M": v["MİKTAR"], "B": v["BİRİM"]} for k, v in st.session_state.data["RECETELER"][secilen].items()]; st.session_state.duzenlenen_urun = secilen; st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arsiv = st.session_state.data.get("ARSIV", [])
    for s in arsiv:
        # Hata vermemesi için .get() kullanıldı
        no = s.get('NO', 'Bilinmiyor')
        urun = s.get('ÜRÜN', 'Tanımsız')
        maliyet = s.get('MALIYET', 0.0)
        with st.expander(f"No: {no} | {urun} | Maliyet: {maliyet:.2f} ₺"):
            st.write(f"Not: {s.get('KAPATMA_NOTU', 'Yok')}")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))

# Diğer menüler (Sipariş Aç, Aktif Siparişler, Reçete Tanımla) önceki yapıda kalabilir.
