import streamlit as st
import json
import os
import datetime
import pandas as pd

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    varsayilan = {"hammadde_depo": {}, "mamul_depo": [], "urun_agaclari": {}, "siparisler": [], "tamamlanan_siparisler": []}
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
    return varsayilan

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

def buyuk_tablo(df):
    df.columns = [c.upper() for c in df.columns]
    return df

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
if 'satir_sayisi' not in st.session_state: st.session_state.satir_sayisi = 1

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ TAKİBİ", "⚙️ ÜRÜN REÇETELERİ", "📦 DEPO DURUMU"])

if menu == "🛒 SİPARİŞ TAKİBİ":
    st.header("🛒 AKTİF SİPARİŞLER")
    for i, s in enumerate(st.session_state.data["siparisler"]):
        st.write(f"**{s['kod']}** | MÜŞTERİ: {s['musteri']} | ÜRÜN: {s['urun']}")
        if st.button(f"🏁 ARŞİVE GÖNDER - {s['kod']}", key=f"kapat_{i}"):
            s['bitis'] = str(datetime.date.today())
            st.session_state.data["tamamlanan_siparisler"].append(s)
            st.session_state.data["siparisler"].pop(i)
            verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ REÇETE EDİTÖRÜ")
    ana_urun = st.text_input("ANA ÜRÜN ADI").upper()
    
    for i in range(st.session_state.satir_sayisi):
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.text_input(f"MALZEME {i+1}", key=f"ad_{i}").upper()
        c2.number_input("MİKTAR", key=f"mik_{i}", format="%.4f")
        c3.selectbox("BİRİM", ["KG", "ADET", "METRE"], key=f"birim_{i}")

    if st.button("➕ SATIR EKLE"): st.session_state.satir_sayisi += 1; st.rerun()
    
    if st.button("💾 REÇETEYİ KAYDET", type="primary"):
        yeni = {}
        for i in range(st.session_state.satir_sayisi):
            n = st.session_state[f"ad_{i}"].upper()
            if n: yeni[n] = {"MİKTAR": st.session_state[f"mik_{i}"], "BİRİM": st.session_state[f"birim_{i}"]}
        st.session_state.data["urun_agaclari"][ana_urun] = yeni
        verileri_kaydet(st.session_state.data); st.success("BAŞARIYLA KAYDEDİLDİ!"); st.rerun()

    if st.session_state.data["urun_agaclari"]:
        st.subheader("📖 MEVCUT REÇETELER")
        for u, m in st.session_state.data["urun_agaclari"].items():
            st.write(f"**ÜRÜN:** {u}")
            st.table(buyuk_tablo(pd.DataFrame(m).T))

elif menu == "📦 DEPO DURUMU":
    st.header("📦 DEPO YÖNETİMİ")
    malzeme_ad = st.text_input("MALZEME ADI").upper()
    miktar = st.number_input("MİKTAR", format="%.3f")
    fiyat = st.number_input("BİRİM KG FİYATI (₺)")
    if st.button("STOK GÜNCELLE"):
        st.session_state.data["hammadde_depo"][malzeme_ad] = {"STOK": miktar, "BİRİM FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.rerun()
    
    if st.session_state.data["hammadde_depo"]:
        st.table(buyuk_tablo(pd.DataFrame(st.session_state.data["hammadde_depo"]).T))
