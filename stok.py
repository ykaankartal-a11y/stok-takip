import streamlit as st
import json
import os
import pandas as pd
import math

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]
SAYFA_BASI = 10

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
if 'edit_malzeme' not in st.session_state: st.session_state.edit_malzeme = None
if 'page_depo' not in st.session_state: st.session_state.page_depo = 0
if 'page_arsiv' not in st.session_state: st.session_state.page_arsiv = 0

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- 1. SİPARİŞ AÇ ---
if menu == "🛒 SİPARİŞ AÇ":
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    c1, c2 = st.columns(2)
    adet = c1.number_input("ADET", min_value=1)
    fiyat = c2.number_input("SATIŞ FİYATI", format="%.2f")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "ÜRETİLEN": 0, "MALIYET": 0.0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.success("Sipariş açıldı!"); st.rerun()

# --- 2. AKTİF SİPARİŞLER ---
elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

# --- 3. REÇETE TANIMLA ---
elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Hammadde Adı").upper()
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- 4. MEVCUT REÇETELER (GELİŞMİŞ) ---
elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        st.write("### Yeni Hammadde Ekle")
        c1, c2, c3 = st.columns(3)
        y_mat = c1.text_input("Malzeme").upper()
        y_mik = c2.number_input("Miktar", format="%.4f", key="y_m")
        y_bir = c3.selectbox("Birim", BIRIM_LISTESI, key="y_b")
        if st.button("➕ EKLE/GÜNCELLE"): st.session_state.data["RECETELER"][secilen][y_mat] = {"MİKTAR": y_mik, "BİRİM": y_bir}; verileri_kaydet(st.session_state.data); st.rerun()
        
        for mat, info in list(st.session_state.data["RECETELER"][secilen].items()):
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            m = cols[1].number_input("Mik", value=float(info['MİKTAR']), key=f"mik_{mat}", format="%.4f")
            b = cols[2].selectbox("Bir", BIRIM_LISTESI, index=BIRIM_LISTESI.index(info['BİRİM']), key=f"bir_{mat}")
            if cols[3].button("💾 Kaydet", key=f"upd_{mat}"): st.session_state.data["RECETELER"][secilen][mat] = {"MİKTAR": m, "BİRİM": b}; verileri_kaydet(st.session_state.data); st.rerun()

# --- 5. DEPO (SAYFALAMALI) ---
elif menu == "📦 DEPO":
    arama = st.text_input("🔍 ARA").upper()
    filt = {k:v for k,v in st.session_state.data["DEPO"].items() if arama in k}
    toplam = math.ceil(len(filt) / SAYFA_BASI)
    
    # Ekleme Formu
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("MİKTAR", 0)), format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("BİRİM", "ADET")) if st.session_state.edit_malzeme else 0)
    fiy = c4.number_input("FİYAT", value=float(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("FİYAT", 0)), format="%.2f")
    if st.button("💾 KAYDET"): st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": bir, "FİYAT": fiy}; verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme=None; st.rerun()
    
    # Sayfalama
    bas, bit = st.session_state.page_depo * SAYFA_BASI, (st.session_state.page_depo + 1) * SAYFA_BASI
    for k, v in list(filt.items())[bas:bit]:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v['MİKTAR']} {v['BİRİM']} | {v['FİYAT']} ₺")
        if col2.button("✏️ Düzenle", key=f"e_{k}"): st.session_state.edit_malzeme = k; st.rerun()
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Önceki") and st.session_state.page_depo > 0: st.session_state.page_depo -= 1; st.rerun()
    if c3.button("Sonraki ➡️") and st.session_state.page_depo < toplam - 1: st.session_state.page_depo += 1; st.rerun()

# --- 6. ARŞİV (SAYFALAMALI + ARAMALI) ---
elif menu == "📊 ARŞİV":
    arama = st.text_input("🔍 Sipariş Ara (Müşteri/Ürün)").upper()
    arsiv = [s for s in st.session_state.data.get("ARSIV", []) if arama in str(s.get('MÜŞTERİ', '')).upper() or arama in str(s.get('ÜRÜN', '')).upper()]
    toplam = math.ceil(len(arsiv) / SAYFA_BASI)
    
    bas, bit = st.session_state.page_arsiv * SAYFA_BASI, (st.session_state.page_arsiv + 1) * SAYFA_BASI
    for s in arsiv[bas:bit]:
        with st.expander(f"No: {s.get('NO', '---')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            st.write(f"Maliyet: {s.get('MALIYET', 0):.2f} ₺ | Not: {s.get('KAPATMA_NOTU', '-')}")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar']))
            
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Önceki", key="p1") and st.session_state.page_arsiv > 0: st.session_state.page_arsiv -= 1; st.rerun()
    if c3.button("Sonraki ➡️", key="p2") and st.session_state.page_arsiv < toplam - 1: st.session_state.page_arsiv += 1; st.rerun()
