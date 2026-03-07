import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ VE DOSYA YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"
BIRIM_LISTESI = ["KG", "GR", "ADET", "LİTRE", "METRE", "PAKET"]

# Yardımcı: Basit maliyet hesaplama (Hammadde miktarı * 1 birim fiyatı varsayımı)
# Gerçek senaryoda buraya depo girişindeki 'Birim Fiyat' eklenebilir.
def maliyet_hesapla(recete, miktar, depo):
    toplam = 0
    for mad, info in recete.items():
        # Burada hammadde birim maliyetini 1 varsayıyoruz, 
        # istersen depo girişine 'fiyat' alanı ekleyebiliriz.
        toplam += (info["MİKTAR"] * miktar) * 1.0 
    return toplam

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": [], "SIPARIS_SAYAC": 100}
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
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
    col1, col2 = st.columns(2)
    mus = col1.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data["RECETELER"].keys())
    uru = col2.selectbox("ÜRÜN", urunler) if urunler else None
    col3, col4, col5 = st.columns(3)
    adet = col3.number_input("ADET", min_value=1, step=1)
    fiyat = col4.number_input("SATIŞ FİYATI (₺)", min_value=0.0, format="%.2f")
    termin = col5.date_input("TERMİN")
    if st.button("SİPARİŞİ ONAYLA") and uru:
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({
            "NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, 
            "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin), "ÜRETİLEN": 0, "TOPLAM_MALIYET": 0
        })
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    else:
        for i, s in enumerate(st.session_state.data["SIPARISLER"]):
            with st.container(border=True):
                st.write(f"**No:** {s['NO']} | **Ürün:** {s['ÜRÜN']} | **Üretilen:** {s.get('ÜRETİLEN', 0)}")
                miktar = st.number_input(f"Üretim Miktarı ({s['NO']})", 1, step=1, key=f"uretim_{i}")
                
                if st.button("🚀 ÜRETİMİ KAYDET", key=f"btn_{i}"):
                    recete = st.session_state.data["RECETELER"].get(s['ÜRÜN'], {})
                    # Maliyet hesapla
                    maliyet = maliyet_hesapla(recete, miktar, st.session_state.data["DEPO"])
                    
                    # Hammadde kontrolü
                    hata = False
                    for mad, info in recete.items():
                        if st.session_state.data["DEPO"].get(mad, {}).get("MİKTAR", 0) < (info["MİKTAR"] * miktar):
                            hata = True; st.error(f"Eksik: {mad}")
                    
                    if not hata:
                        for mad, info in recete.items(): st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                        s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                        s["TOPLAM_MALIYET"] = s.get("TOPLAM_MALIYET", 0) + maliyet
                        verileri_kaydet(st.session_state.data); st.rerun()
                
                if st.button("✅ SİPARİŞİ KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
                    st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                    verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV (MALİYET ANALİZİ)")
    df = pd.DataFrame(st.session_state.data["ARSIV"])
    if not df.empty:
        # Kar/Zarar hesabı (Satış - Maliyet)
        df["KAR_ZARAR"] = df["FİYAT"] - df["TOPLAM_MALIYET"]
        st.table(df)
    else: st.info("Arşiv boş.")

# ... (REÇETE, DEPO modülleri önceki kodla aynı) ...
