import streamlit as st
import json
import os
import pandas as pd

# --- AYARLAR ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET", "İŞÇİLİK(TL)"]

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

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- 1. SİPARİŞ AÇ ---
if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ AÇ")
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
            miktar = st.number_input("Üretim Miktarı", 1, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                verileri_kaydet(st.session_state.data); st.rerun()
            not_val = st.text_input("Kapatma Notu", key=f"not_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

# --- 3. REÇETE TANIMLA ---
elif menu == "⚙️ REÇETE TANIMLA":
    st.header("⚙️ REÇETE TANIMLA")
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Malzeme Adı").upper()
    h_mik = c2.number_input("Miktar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"):
        if urun not in st.session_state.data["RECETELER"]: st.session_state.data["RECETELER"][urun] = {}
        st.session_state.data["RECETELER"][urun][h_ad] = {"MİKTAR": h_mik, "BİRİM": h_bir}
        verileri_kaydet(st.session_state.data); st.rerun()

# --- 4. MEVCUT REÇETELER ---
elif menu == "📋 MEVCUT REÇETELER":
    st.header("📋 MEVCUT REÇETELER")
    secilen = st.selectbox("ÜRÜN SEÇİN", [""] + list(st.session_state.data["RECETELER"].keys()))
    if secilen:
        recete = st.session_state.data["RECETELER"][secilen]
        for mat, info in list(recete.items()):
            cols = st.columns([3, 1, 1, 1])
            cols[0].write(f"**{mat}**")
            yeni_mik = cols[1].number_input("Miktar", value=float(info['MİKTAR']), key=f"mik_{mat}", format="%.4f")
            if cols[2].button("💾 Güncelle", key=f"upd_{mat}"):
                recete[mat]['MİKTAR'] = yeni_mik
                verileri_kaydet(st.session_state.data); st.rerun()
            if cols[3].button("❌ Sil", key=f"del_{mat}"):
                del recete[mat]; verileri_kaydet(st.session_state.data); st.rerun()

# --- 5. DEPO ---
elif menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    mev = st.session_state.data["DEPO"].get(st.session_state.edit_malzeme, {}) if st.session_state.edit_malzeme else {}
    
    isim = c1.text_input("MALZEME ADI", value=st.session_state.edit_malzeme or "")
    mik = c2.number_input("MİKTAR", value=float(mev.get("MİKTAR", 0.0)), format="%.3f")
    bir = c3.selectbox("BİRİM", BIRIM_LISTESI, index=BIRIM_LISTESI.index(mev.get("BİRİM", "ADET")) if mev.get("BİRİM") in BIRIM_LISTESI else 0)
    fiy = c4.number_input("FİYAT", value=float(mev.get("FİYAT", 0.0)), format="%.2f")
    
    if st.button("💾 KAYDET / GÜNCELLE"):
        st.session_state.data["DEPO"][isim.upper()] = {"MİKTAR": mik, "BİRİM": bir, "FİYAT": fiy}
        verileri_kaydet(st.session_state.data); st.session_state.edit_malzeme = None; st.rerun()

    st.write("---")
    arama = st.text_input("🔍 MALZEME ARA").upper()
    for k, v in {k:v for k,v in st.session_state.data["DEPO"].items() if arama in k}.items():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k}**: {v.get('MİKTAR', 0)} {v.get('BİRİM', '-')} | {v.get('FİYAT', 0)} ₺")
        if col2.button("✏️ Düzenle", key=f"edit_{k}"): st.session_state.edit_malzeme = k; st.rerun()

# --- 6. ARŞİV ---
elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    for s in st.session_state.data.get("ARSIV", []):
        
        with st.expander(f"No: {s.get('NO', '---')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            st.write(f"**Not:** {s.get('KAPATMA_NOTU', 'Not eklenmemiş')}")
            st.write(f"**Toplam Maliyet:** {s.get('MALIYET', 0):.2f} ₺")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))
