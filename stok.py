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
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return varsayilan
    return varsayilan

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state: st.session_state.data = verileri_yukle()
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- GİRİŞ ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #0078D7;'>ALFA TECH</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş"):
                if u.lower() == "admin" and p == "1234": st.session_state.authenticated = True; st.rerun()
                else: st.error("Hatalı!")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
def siparis_maliyet_ozeti(siparis):
    urun = siparis['urun']
    sip_miktar = siparis['miktar']
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    toplam_maliyet = 0
    analiz = []
    tamam_mi = True
    for malz, detay in recete.items():
        gereken = detay["miktar"] * sip_miktar
        depo = st.session_state.data["hammadde_depo"].get(malz, {"miktar": 0.0, "fiyat": 0.0})
        maliyet = gereken * depo.get("fiyat", 0)
        toplam_maliyet += maliyet
        if gereken > depo.get("miktar", 0): tamam_mi = False
        analiz.append({"MALZEME": malz, "GEREKEN": f"{gereken:.2f}", "MEVCUT": f"{depo.get('miktar',0):.2f}", "TOPLAM": f"{maliyet:.2f} ₺"})
    
    toplam_gider = toplam_maliyet + siparis.get('iscilik', 0)
    kar = siparis.get('satis_fiyati', 0) - toplam_gider
    return {"tamam_mi": tamam_mi, "analiz": pd.DataFrame(analiz), "kar": kar, "toplam_gider": toplam_gider}

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ TAKİBİ", "🛠️ ÜRETİM KAYDI", "⚙️ ÜRÜN REÇETELERİ", "📦 DEPO DURUMU", "📊 ARŞİV"])

# --- DIALOGLAR ---
@st.dialog("🏁 SİPARİŞİ KAPAT")
def siparis_kapat_penceresi(siparis, index):
    not_alani = st.text_area("Kapanış Notu")
    if st.button("ARŞİVE GÖNDER", type="primary"):
        siparis["bitis"] = str(datetime.date.today())
        siparis["not"] = not_alani
        st.session_state.data["tamamlanan_siparisler"].append(siparis)
        st.session_state.data["siparisler"].pop(index)
        verileri_kaydet(st.session_state.data); st.rerun()

# --- ANA SAYFALAR ---
if menu == "🛒 SİPARİŞ TAKİBİ":
    st.header("🛒 Aktif Siparişler")
    for idx, s in enumerate(st.session_state.data["siparisler"]):
        res = siparis_maliyet_ozeti(s)
        color = "#2e7d32" if res['tamam_mi'] else "#c62828"
        with st.container():
            st.markdown(f"<div style='border-left: 8px solid {color}; padding: 10px; background:#f4f4f4; margin-bottom:10px;'><b>{s['kod']}</b> | {s['musteri']} | 💰 Kâr: {res['kar']:.2f} ₺</div>", unsafe_allow_html=True)
            if st.button("🏁 KAPAT", key=f"kapat_{idx}"): siparis_kapat_penceresi(s, idx)

elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ ALFA TECH Reçete Editörü")
    if "satir_sayisi" not in st.session_state: st.session_state.satir_sayisi = 1
    ana_urun = st.text_input("ANA ÜRÜN ADI").upper()
    for i in range(st.session_state.satir_sayisi):
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.text_input(f"Hammadde {i+1}", key=f"h_ad_{i}").upper()
        c2.number_input("Miktar", key=f"h_mik_{i}", format="%.4f")
        c3.selectbox("Birim", ["KG", "ADET", "METRE"], key=f"h_birim_{i}")
    
    if st.button("➕ Satır Ekle"): st.session_state.satir_sayisi += 1; st.rerun()
    if st.button("💾 REÇETEYİ KAYDET", type="primary"):
        yeni = {}
        for i in range(st.session_state.satir_sayisi):
            n = st.session_state[f"h_ad_{i}"].upper()
            if n: yeni[n] = {"miktar": st.session_state[f"h_mik_{i}"], "birim": st.session_state[f"h_birim_{i}"]}
        st.session_state.data["urun_agaclari"][ana_urun] = yeni
        verileri_kaydet(st.session_state.data); st.success("Kaydedildi!"); st.rerun()

elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo")
    with st.expander("📥 Stok/Fiyat Güncelle"):
        sel = st.selectbox("Malzeme", list(st.session_state.data["hammadde_depo"].keys()) or ["Yok"])
        m = st.number_input("Miktar")
        f = st.number_input("Birim Fiyat")
        if st.button("GÜNCELLE"):
            st.session_state.data["hammadde_depo"][sel] = {"miktar": m, "fiyat": f}
            verileri_kaydet(st.session_state.data); st.rerun()
    st.table(pd.DataFrame(st.session_state.data["hammadde_depo"]).T)

elif menu == "📊 ARŞİV":
    st.header("📊 Arşiv")
    st.table(pd.DataFrame(st.session_state.data["tamamlanan_siparisler"]))
