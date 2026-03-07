import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    default = {"DEPO": {}, "RECETELER": {}, "SIPARISLER": [], "ARSIV": []}
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
if 'satir_sayisi' not in st.session_state: st.session_state.satir_sayisi = 5

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["📦 DEPO", "⚙️ REÇETE TANIMLA VE DÜZENLE", "🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "📊 ARŞİV"])

# --- MODÜLLER ---

if menu == "📦 DEPO":
    st.header("📦 DEPO YÖNETİMİ")
    c1, c2, c3 = st.columns(3)
    isim = c1.text_input("MALZEME ADI").upper()
    miktar = c2.number_input("MİKTAR", format="%.3f")
    fiyat = c3.number_input("BİRİM FİYAT (₺)")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data.get("DEPO"): st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

elif menu == "⚙️ REÇETE TANIMLA VE DÜZENLE":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    
    # 1. BÖLÜM: REÇETE SEÇİMİ VE DÜZENLEME
    secilen_recete = st.selectbox("DÜZENLEMEK İÇİN BİR ÜRÜN SEÇ", ["YENİ KAYIT"] + list(st.session_state.data.get("RECETELER", {}).keys()))
    
    urun = st.text_input("ÜRÜN ADI", value=secilen_recete if secilen_recete != "YENİ KAYIT" else "").upper()
    
    # Mevcut reçeteyi tablo olarak göster
    if secilen_recete != "YENİ KAYIT":
        st.write(f"**{secilen_recete}** reçetesini düzenliyorsunuz:")
        st.table(pd.DataFrame(st.session_state.data["RECETELER"][secilen_recete].items(), columns=["MALZEME", "MİKTAR"]))

    # 2. BÖLÜM: DİNAMİK GİRİŞ
    st.write("---")
    recete_temp = {}
    for i in range(st.session_state.satir_sayisi):
        c1, c2 = st.columns([3, 1])
        h_ad = c1.text_input(f"Hammadde {i+1}", key=f"h_{i}").upper()
        h_mik = c2.number_input("Miktar", key=f"m_{i}", format="%.4f")
        if h_ad: recete_temp[h_ad] = h_mik
    
    col_a, col_b = st.columns(2)
    if col_a.button("➕ Satır Ekle"): st.session_state.satir_sayisi += 1; st.rerun()
    if col_b.button("💾 REÇETEYİ KAYDET / GÜNCELLE", type="primary"):
        if urun and recete_temp:
            st.session_state.data["RECETELER"][urun] = recete_temp
            verileri_kaydet(st.session_state.data)
            st.success("İşlem Başarılı!"); st.rerun()

elif menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    receteler = list(st.session_state.data.get("RECETELER", {}).keys())
    uru = st.selectbox("ÜRÜN", receteler if receteler else ["ÖNCE REÇETE TANIMLA"])
    satis = st.number_input("SATIŞ FİYATI (₺)")
    if st.button("SİPARİŞİ ONAYLA"):
        st.session_state.data["SIPARISLER"].append({"MÜŞTERİ": mus, "ÜRÜN": uru, "FİYAT": satis, "TARİH": str(datetime.now().date())})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 AKTİF SİPARİŞLER")
    for i, s in enumerate(st.session_state.data.get("SIPARISLER", [])):
        st.write(f"**{s['MÜŞTERİ']}** | {s['ÜRÜN']} | {s['FİYAT']} ₺")
        if st.button(f"KAPAT VE ARŞİVLE", key=f"kapat_{i}"):
            kapali = st.session_state.data["SIPARISLER"].pop(i)
            st.session_state.data["ARSIV"].append(kapali)
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    if st.session_state.data.get("ARSIV"): st.table(pd.DataFrame(st.session_state.data["ARSIV"]))
    else: st.info("Arşiv henüz boş.")
