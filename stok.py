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

# --- MODÜLLER ---

if menu == "🛒 SİPARİŞ AÇ":
    st.header("🛒 SİPARİŞ OLUŞTUR")
    c1, c2 = st.columns(2)
    mus = c1.text_input("MÜŞTERİ ADI").upper()
    urunler = list(st.session_state.data["RECETELER"].keys())
    uru = c2.selectbox("ÜRÜN", urunler) if urunler else None
    c3, c4, c5 = st.columns(3)
    adet = c3.number_input("ADET", min_value=1, step=1)
    fiyat = c4.number_input("SATIŞ FİYATI (₺)", min_value=0.0, format="%.2f")
    termin = c5.date_input("TERMİN")
    if st.button("SİPARİŞİ ONAYLA") and uru:
        st.session_state.data["SIPARIS_SAYAC"] += 1
        st.session_state.data["SIPARISLER"].append({"NO": st.session_state.data["SIPARIS_SAYAC"], "MÜŞTERİ": mus, "ÜRÜN": uru, "ADET": adet, "FİYAT": fiyat, "TERMİN": str(termin), "ÜRETİLEN": 0, "MALIYET": 0.0, "DETAY": {}})
        verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📋 AKTİF SİPARİŞLER":
    st.header("📋 KADEMELİ ÜRETİM")
    if not st.session_state.data["SIPARISLER"]: st.info("Aktif sipariş yok.")
    for i, s in enumerate(st.session_state.data["SIPARISLER"]):
        with st.expander(f"No: {s.get('NO')} | Müşteri: {s.get('MÜŞTERİ')} | Ürün: {s.get('ÜRÜN')}"):
            miktar = st.number_input(f"Üretim Miktarı", 1, key=f"u_{i}")
            if st.button("🚀 ÜRETİMİ KAYDET", key=f"b_{i}"):
                recete = st.session_state.data["RECETELER"].get(s.get('ÜRÜN'), {})
                hata, toplam_maliyet = False, 0
                anlik_detay = {}
                for mad, info in recete.items():
                    if mad == "İŞÇİLİK":
                        tutar = info["MİKTAR"] * miktar
                        toplam_maliyet += tutar
                        anlik_detay["İŞÇİLİK"] = anlik_detay.get("İŞÇİLİK", 0) + tutar
                    else:
                        stok_fiyat = st.session_state.data["DEPO"].get(mad, {}).get("FİYAT", 0)
                        tutar = info["MİKTAR"] * miktar * stok_fiyat
                        if st.session_state.data["DEPO"].get(mad, {}).get("MİKTAR", 0) < (info["MİKTAR"] * miktar):
                            hata = True; st.error(f"Eksik: {mad}")
                        else:
                            toplam_maliyet += tutar
                            anlik_detay[mad] = anlik_detay.get(mad, 0) + tutar
                            st.session_state.data["DEPO"][mad]["MİKTAR"] -= (info["MİKTAR"] * miktar)
                if not hata:
                    s["ÜRETİLEN"] = s.get("ÜRETİLEN", 0) + miktar
                    s["MALIYET"] = s.get("MALIYET", 0) + toplam_maliyet
                    for k, v in anlik_detay.items(): s["DETAY"][k] = s["DETAY"].get(k, 0) + v
                    verileri_kaydet(st.session_state.data); st.rerun()
            if st.button("✅ KAPAT VE ARŞİVLE", key=f"k_{i}"):
                s["KAPATMA_NOTU"] = st.text_input("Not", key=f"not_{i}")
                st.session_state.data["ARSIV"].append(st.session_state.data["SIPARISLER"].pop(i))
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📊 ARŞİV":
    st.header("📊 ARŞİV - DETAYLI MALİYET")
    arama = st.text_input("🔍 ARA (Müşteri/Ürün)").upper()
    arsiv = [s for s in st.session_state.data.get("ARSIV", []) if arama in str(s.get('MÜŞTERİ', '')).upper() or arama in str(s.get('ÜRÜN', '')).upper()]
    
    # Sayfalama Mantığı
    toplam_sayfa = (len(arsiv) - 1) // SAYFA_BASI + 1
    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    c2.write(f"Sayfa {st.session_state.page + 1} / {toplam_sayfa}")
    if c3.button("➡️") and st.session_state.page < toplam_sayfa - 1: st.session_state.page += 1; st.rerun()
    
    for s in arsiv[st.session_state.page * SAYFA_BASI : (st.session_state.page + 1) * SAYFA_BASI]:
        with st.expander(f"No: {s.get('NO')} | {s.get('MÜŞTERİ')} | {s.get('ÜRÜN')}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Satış", f"{s.get('FİYAT', 0)} ₺")
            c2.metric("Maliyet", f"{s.get('MALIYET', 0):.2f} ₺")
            c3.metric("Kâr", f"{s.get('FİYAT', 0) - s.get('MALIYET', 0):.2f} ₺")
            
            detay = s.get('DETAY', {})
            if detay:
                st.write("**Maliyet Kırılımı:**")
                st.table(pd.DataFrame.from_dict(detay, orient='index', columns=['Tutar (₺)']))
            else:
                st.warning("Bu siparişte detay verisi henüz oluşmamış (eski kayıt olabilir).")

elif menu == "⚙️ REÇETE TANIMLA":
    urun = st.text_input("ÜRÜN ADI").upper()
    h_ad = st.text_input("Hammadde Adı (İşçilik için 'İŞÇİLİK')").upper()
    h_mik = st.number_input("Miktar / Tutar", format="%.4f")
    if st.button("➕ EKLE"): st.session_state.temp_liste.append({"Hammadde": h_ad, "Miktar": h_mik})
    if st.session_state.temp_liste:
        st.table(pd.DataFrame(st.session_state.temp_liste))
        if st.button("💾 KAYDET"):
            st.session_state.data["RECETELER"][urun] = {i["Hammadde"]: {"MİKTAR": i["Miktar"]} for i in st.session_state.temp_liste}
            verileri_kaydet(st.session_state.data); st.session_state.temp_liste = []; st.rerun()

elif menu == "📦 DEPO":
    c1, c2, c3, c4 = st.columns(4)
    isim, miktar = c1.text_input("MALZEME").upper(), c2.number_input("MİKTAR", format="%.3f")
    fiyat = c4.number_input("BİRİM FİYAT", format="%.2f")
    if st.button("KAYDET"): st.session_state.data["DEPO"][isim] = {"MİKTAR": miktar, "FİYAT": fiyat}; verileri_kaydet(st.session_state.data); st.rerun()
    if st.session_state.data["DEPO"]: st.table(pd.DataFrame(st.session_state.data["DEPO"]).T)
