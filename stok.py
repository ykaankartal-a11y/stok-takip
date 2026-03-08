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

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    mus = st.text_input("MÜŞTERİ ADI").upper()
    uru = st.selectbox("ÜRÜN", [""] + list(st.session_state.data["RECETELER"].keys()))
    c1, c2 = st.columns(2)
    adet = c1.number_input("ADET", min_value=1)
    fiyat = c2.number_input("SATIŞ FİYATI", format="%.2f")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "ÜRETİLEN": 0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.success("Sipariş açıldı!"); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            miktar = st.number_input("Üretim Miktarı", 0, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                for mat, info in recete.items():
                    s["DETAY"][mat] = s.get("DETAY", {}).get(mat, 0) + (miktar * info.get("MİKTAR", 0) * info.get("MALİYET", 0))
                verileri_kaydet(st.session_state.data); st.rerun()
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3, c4 = st.columns(4)
    h_ad = c1.text_input("Ad").upper(); h_mik = c2.number_input("Mik", 0.0)
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI); h_fiy = c4.number_input("Maliyet", 0.0)
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir, "MALİYET": h_fiy}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.button("➕ İŞÇİLİK EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun]["İŞÇİLİK"] = {"MİKTAR": 1, "BİRİM": "İŞÇİLİK(TL)", "MALİYET": 0}
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 MEVCUT REÇETELER":
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        # Eski pratik tablo görünümü
        df = pd.DataFrame(st.session_state.data["RECETELER"][secilen]).T
        st.table(df)
        # Düzenleme ve yeni ekleme alanı
        st.write("---")
        n_ad = st.text_input("Yeni Malzeme/İşçilik Adı").upper()
        if st.button("➕ İŞÇİLİK EKLE"): st.session_state.data["RECETELER"][secilen]["İŞÇİLİK"] = {"MİKTAR": 1, "BİRİM": "İŞÇİLİK(TL)", "MALİYET": 0}; verileri_kaydet(st.session_state.data); st.rerun()
        if n_ad and st.button("➕ Ekle"): st.session_state.data["RECETELER"][secilen][n_ad] = {"MİKTAR": 0, "BİRİM": "ADET", "MALİYET": 0}; verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO":
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    isim = c1.text_input("MALZEME", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}).get("MİKTAR", 0)))
    if st.button("💾 KAYDET"): st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": "ADET"}; verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme=None; st.rerun()
    for k, v in st.session_state.data["DEPO"].items():
        if st.button(f"✏️ {k}", key=f"e_{k}"): st.session_state.edit_malzeme = k; st.rerun()

elif menu == "📊 ARŞİV":
    for s in st.session_state.data.get("ARSIV", []):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')}"):
            st.metric("Maliyet", f"{sum(s.get('DETAY', {}).values()):.2f} ₺")
