import streamlit as st
import json
import os
import datetime
import pandas as pd

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    varsayilan = {
        "hammadde_depo": {}, 
        "mamul_depo": [], 
        "urun_agaclari": {}, 
        "siparisler": [],
        "tamamlanan_siparisler": [],
        "kullanicilar": {"admin": "1234"}
    }
    
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                mevcut = json.load(f)
                # FORMAT KONTROLÜ VE TAMİRİ (AttributeError Önleyici)
                for anahtar, tip in varsayilan.items():
                    if anahtar not in mevcut or type(mevcut[anahtar]) != type(tip):
                        mevcut[anahtar] = tip
                return mevcut
        except:
            return varsayilan
    return varsayilan

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# Uygulama başladığında veriyi "Süper Güvenli" yükle
if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

# Çalışma anında her ihtimale karşı tip kontrolü
if not isinstance(st.session_state.data.get("siparisler"), list):
    st.session_state.data["siparisler"] = []
if not isinstance(st.session_state.data.get("tamamlanan_siparisler"), list):
    st.session_state.data["tamamlanan_siparisler"] = []

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="Pro ERP Yönetim", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.title("🔐 Fabrika Yönetim Sistemi")
    with st.form("login_panel"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u.lower() == "admin" and p == "1234":
                st.session_state.authenticated = True
                st.session_state.current_user = u
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı veya Şifre!")
    st.stop()

# --- ANA MENÜ ---
st.sidebar.title(f"👤 {st.session_state.current_user}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("Bölüm Seçiniz:", ["🛒 Siparişler", "⚙️ Ürün Ağacı", "📦 Depo", "🛠️ Üretim", "📊 Arşiv"])

# --- BÖLÜM 1: SİPARİŞLER ---
if menu == "🛒 Siparişler":
    st.header("🛒 Aktif Müşteri Siparişleri")
    
    # Mevcut siparişleri listele
    if st.session_state.data["siparisler"]:
        for idx, s in enumerate(st.session_state.data["siparisler"]):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{s['musteri']}** - {s['urun']} (Hedef: {s['miktar']})")
            c2.info(f"Üretilen: {s['uretilen']}")
            if c3.button("Kapat/Arşivle", key=f"kapat_{idx}"):
                s["bitis_tarihi"] = str(datetime.date.today())
                st.session_state.data["tamamlanan_siparisler"].append(s)
                st.session_state.data["siparisler"].pop(idx)
                verileri_kaydet(st.session_state.data)
                st.rerun()
    
    with st.expander("➕ Yeni Sipariş Ekle"):
        with st.form("y_sip"):
            m = st.text_input("Müşteri")
            u_l = list(st.session_state.data.get("urun_agaclari", {}).keys())
            sec_u = st.selectbox("Ürün", u_l if u_l else ["Önce Reçete Tanımlayın"])
            c1, c2 = st.columns(2)
            mik = c1.number_input("Miktar", min_value=1)
            term = c2.date_input("Termin")
            if st.form_submit_button("Kaydet"):
                yeni = {
                    "id": len(st.session_state.data["siparisler"]) + 100, 
                    "musteri": m, 
                    "urun": sec_u, 
                    "miktar": mik, 
                    "uretilen": 0, 
                    "termin": str(term)
                }
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data)
                st.success("Sipariş Başarıyla Oluşturuldu!")
                st.rerun()

# --- BÖLÜM 2: ÜRÜN AĞACI ---
elif menu == "⚙️ Ürün Ağacı":
    st.header("⚙️ Reçete (BOM) Girişi")
    with st.form("bom_g"):
        c1, c2, c3, c4 = st.columns(4)
        u_ad = c1.text_input("Ürün Adı")
        m_ad = c2.text_input("Hammadde")
        birim = c3.selectbox("Birim", ["Adet", "Metre", "Kg", "Gram"])
        mik = c4.number_input("Miktar", min_value=0.001, format="%.3f")
        if st.form_submit_button("Reçeteye Yaz"):
            if u_ad not in st.session_state.data["urun_agaclari"]: 
                st.session_state.data["urun_agaclari"][u_ad] = {}
            st.session_state.data["urun_agaclari"][u_ad][m_ad] = {"miktar": mik, "birim": birim}
            if m_ad not in st.session_state.data["hammadde_depo"]: 
                st.session_state.data["hammadde_depo"][m_ad] = {"miktar": 0.0, "birim": birim}
            verileri_kaydet(st.session_state.data)
            st.success("Kaydedildi.")
            st.rerun()

# --- BÖLÜM 3: DEPO ---
elif menu == "📦 Depo":
    st.header("📦 Depo Durumu")
    h_t, m_t = st.tabs(["🏗️ Hammadde", "🏬 Mamul"])
    with h_t:
        depo = st.session_state.data.get("hammadde_depo", {})
        if depo:
            st.write(pd.DataFrame([{"Malzeme": k, "Mevcut": v["miktar"], "Birim": v["birim"]} for k, v in depo.items()]))
            with st.expander("Stok Ekle"):
                s_m = st.selectbox("Malzeme", list(depo.keys()))
                s_mik = st.number_input("Miktar", min_value=0.1)
                if st.button("Güncelle"):
                    st.session_state.data["hammadde_depo"][s_m]["miktar"] += s_mik
                    verileri_kaydet(st.session_state.data)
                    st.rerun()
        else: st.info("Hammadde tanımlı değil.")
    with m_t:
        mamul = st.session_state.data.get("mamul_depo", [])
        if mamul: st.write(pd.DataFrame(mamul))
        else: st.info("Üretim yapılmamış.")

# --- BÖLÜM 4: ÜRETİM ---
elif menu == "🛠️ Üretim":
    st.header("🛠️ Üretim Kaydı")
    sips = st.session_state.data.get("siparisler", [])
    s_ops = [f"{s['musteri']} | {s['urun']}" for s in sips]
    if s_ops:
        with st.form("u_f"):
            s_sec = st.selectbox("Sipariş", s_ops)
            u_adet = st.number_input("Üretilen Adet", min_value=1)
            if st.form_submit_button("Üretimi İşle"):
                sip = next(s for s in sips if f"{s['musteri']} | {s['urun']}" == s_sec)
                r = st.session_state.data["urun_agaclari"].get(sip['urun'], {})
                for malz, det in r.items():
                    if malz in st.session_state.data["hammadde_depo"]:
                        st.session_state.data["hammadde_depo"][malz]["miktar"] -= (det["miktar"] * u_adet)
                st.session_state.data["mamul_depo"].append({"Tarih": str(datetime.date.today()), "Müşteri": sip["musteri"], "Ürün": sip["urun"], "Adet": u_adet})
                sip["uretilen"] += u_adet
                verileri_kaydet(st.session_state.data)
                st.balloons()
                st.rerun()
    else: st.info("Aktif sipariş yok.")

# --- BÖLÜM 5: ARŞİV ---
elif menu == "📊 Arşiv":
    st.header("📊 Tamamlanan Siparişler")
    arsiv = st.session_state.data.get("tamamlanan_siparisler", [])
    if arsiv: st.write(pd.DataFrame(arsiv))
    else: st.info("Arşiv boş.")
