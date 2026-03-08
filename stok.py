import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

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
if 'page' not in st.session_state: st.session_state.page = 0

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ AÇ", "📋 AKTİF SİPARİŞLER", "⚙️ REÇETE TANIMLA", "📋 MEVCUT REÇETELER", "📦 DEPO", "📊 ARŞİV"])

# --- 1. SİPARİŞ AÇ ---
if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    mus = st.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data["RECETELER"].keys())
    uru = st.selectbox("ÜRÜN", ["SEÇİNİZ..."] + urunler)
    c3, c4, c5 = st.columns(3)
    adet = c3.number_input("ADET", min_value=1, step=1)
    fiyat = c4.number_input("SATIŞ FİYATI (₺)", min_value=0.0, format="%.2f")
    termin = c5.date_input("TERMİN")
    if st.button("SİPARİŞİ ONAYLA"):
        if uru != "SEÇİNİZ..." and mus:
            st.session_state.data["SIPARIS_SAYAC"] += 1
            st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin), "ÜRETİLEN": 0, "MALIYET": 0.0, "DETAY": {}})
            verileri_kaydet(st.session_state.data)
            st.success(f"Sipariş {st.session_state.data['SIPARIS_SAYAC']} başarıyla oluşturuldu!"); st.rerun()
        else: st.error("Lütfen müşteri ve ürün seçin.")

# --- 2. AKTİF SİPARİŞLER ---
elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            miktar = st.number_input(f"Üretim Miktarı", 0, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                if miktar > 0:
                    recete = st.session_state.data["RECETELER"].get(s.get('ÜRÜN'), {})
                    hata, toplam_maliyet = False, 0
                    anlik_detay = {}
                    for mad, info in recete.items():
                        miktar_gerekli = info["MİKTAR"] * miktar
                        if mad == "İŞÇİLİK":
                            toplam_maliyet += miktar_gerekli
                            anlik_detay["İŞÇİLİK"] = anlik_detay.get("İŞÇİLİK", 0) + miktar_gerekli
                        else:
                            stok = st.session_state.data["DEPO"].get(mad, {})
                            if stok.get("MİKTAR", 0) < miktar_gerekli:
                                hata = True; st.error(f"Eksik: {mad}")
                            else:
                                tutar = miktar_gerekli * stok.get("FİYAT", 0)
                                toplam_maliyet += tutar
                                anlik_detay[mad] = anlik_detay.get(mad, 0) + tutar
                                st.session_state.data["DEPO"][mad]["MİKTAR"] -= miktar_gerekli
                    if not hata:
                        s["ÜRETİLEN"] += miktar; s["MALIYET"] += toplam_maliyet
                        for k, v in anlik_detay.items(): s["DETAY"][k] = s.get("DETAY", {}).get(k, 0) + v
                        verileri_kaydet(st.session_state.data); st.rerun()
            
            not_val = st.text_input("Kapatma Notu", key=f"not_{i}")
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = not_val
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.success("Sipariş arşive taşındı."); st.rerun()

# --- 3. REÇETE ---
elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    c1, c2, c3 = st.columns(3)
    h_ad = c1.text_input("Hammadde / İşçilik Adı")
    h_mik = c2.number_input("Miktar / Tutar", format="%.4f")
    h_bir = c3.selectbox("Birim", BIRIM_LISTESI)
    if st.button("➕ EKLE"): 
        st.session_state.temp_liste.append({"H": h_ad.upper(), "M": h_mik, "B": h_bir})
        st.rerun()
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["H"]: {"MİKTAR": i["M"], "BİRİM": i["B"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.success("Reçete kaydedildi!"); st.rerun()

# --- 4. DEPO ---
elif menu == "📦 DEPO":
    c1, c2, c3, c4 = st.columns(4)
    isim = c1.text_input("MALZEME").upper()
    miktar = c2.number_input("MİKTAR", format="%.3f")
    birim = c3.selectbox("BİRİM", BIRIM_LISTESI)
    fiyat = c4.number_input("FİYAT", format="%.2f")
    if st.button("KAYDET"):
        st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "BİRİM": birim, "FİYAT": fiyat}
        verileri_kaydet(st.session_state.data); st.success(f"{isim} depoya eklendi."); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)

# --- 5. ARŞİV ---
elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV")
    arama = st.text_input("🔍 ARA").upper()
    arsiv = [s for s in st.session_state.data.get("ARSIV", []) if arama in str(s.get('MÜŞTERİ', '')).upper() or arama in str(s.get('ÜRÜN', '')).upper()]
    
    toplam_sayfa = (len(arsiv) - 1) // SAYFA_BASI + 1
    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    c2.write(f"Sayfa {st.session_state.page + 1} / {toplam_sayfa}")
    if c3.button("➡️") and st.session_state.page < toplam_sayfa - 1: st.session_state.page += 1; st.rerun()
    
    for s in arsiv[st.session_state.page * SAYFA_BASI : (st.session_state.page + 1) * SAYFA_BASI]:
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            st.write(f"**Not:** {s.get('KAPATMA_NOTU', 'Yok')}")
            if s.get('DETAY'): st.table(pd.DataFrame.from_dict(s['DETAY'], orient='index', columns=['Tutar (₺)']))
