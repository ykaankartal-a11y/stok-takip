import streamlit as st
import json
import os
import datetime
import pandas as pd

# 1. VERİ YÖNETİMİ
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {
        "hammadde_depo": {}, 
        "mamul_depo": [], 
        "urun_agaclari": {}, 
        "siparisler": [],
        "tamamlanan_siparisler": [],
        "kullanicilar": {"admin": "1234", "personel": "5678"}
    }

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="Pro ERP - Akıllı Fabrika", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.title("🔐 Pro ERP Yönetim Sistemi")
    with st.form("login"):
        k = st.text_input("Kullanıcı Adı")
        s = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            users = st.session_state.data.get("kullanicilar", {})
            if k in users and users[k] == s:
                st.session_state.authenticated = True
                st.session_state.current_user = k
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
    st.stop()

# --- ANA MENÜ ---
st.sidebar.title(f"👤 {st.session_state.current_user}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("İşlem Merkezi:", ["🛒 Sipariş Yönetimi", "⚙️ Ürün Ağacı (BOM)", "📦 Depo & Stok", "🛠️ Üretim Hattı", "📊 Analiz & Arşiv"])

# --- BÖLÜM 1: SİPARİŞ YÖNETİMİ ---
if menu == "🛒 Sipariş Yönetimi":
    st.header("🛒 Müşteri Siparişleri")
    
    # Termin Uyarıları
    bugun = datetime.date.today()
    for s in st.session_state.data["siparisler"]:
        termin = datetime.datetime.strptime(s["termin"], "%Y-%m-%d").date()
        fark = (termin - bugun).days
        if fark <= 3:
            st.error(f"🚨 KRİTİK TERMİN: {s['musteri']} - {s['urun']} (Son {fark} gün!)")
    
    # Aktif Sipariş Listesi ve Kapatma
    if st.session_state.data["siparisler"]:
        st.subheader("📋 Aktif Siparişler")
        for idx, sip in enumerate(st.session_state.data["siparisler"]):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"**{sip['id']} - {sip['musteri']}** ({sip['urun']})")
            c2.write(f"Hedef: {sip['miktar']} / Üretilen: {sip['uretilen']}")
            c3.write(f"Termin: {sip['termin']}")
            if c4.button("Siparişi Kapat", key=f"close_{sip['id']}"):
                sip["bitis_tarihi"] = str(datetime.date.today())
                st.session_state.data["tamamlanan_siparisler"].append(sip)
                st.session_state.data["siparisler"].pop(idx)
                verileri_kaydet(st.session_state.data)
                st.rerun()

    with st.expander("➕ Yeni Sipariş Aç"):
        with st.form("yeni_sip"):
            mus = st.text_input("Müşteri Adı")
            u_l = list(st.session_state.data["urun_agaclari"].keys())
            sec_u = st.selectbox("Ürün", u_l)
            c1, c2 = st.columns(2)
            mik = c1.number_input("Sipariş Miktarı", min_value=1)
            term = c2.date_input("Termin Tarihi")
            if st.form_submit_button("Siparişi Kaydet"):
                yeni = {
                    "id": len(st.session_state.data["siparisler"]) + len(st.session_state.data["tamamlanan_siparisler"]) + 1,
                    "musteri": mus, "urun": sec_u, "miktar": mik, "uretilen": 0,
                    "gelis_tarihi": str(datetime.date.today()), "termin": str(term)
                }
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data)
                st.success("Sipariş açıldı!")
                st.rerun()

# --- BÖLÜM 2: ÜRÜN AĞACI ---
elif menu == "⚙️ Ürün Ağacı (BOM)":
    st.header("⚙️ Ürün Reçetesi Tanımlama")
    with st.form("bom"):
        c1, c2, c3, c4 = st.columns(4)
        u = c1.text_input("Ana Ürün")
        m = c2.text_input("Hammadde")
        b = c3.selectbox("Birim", ["Adet", "mm", "cm", "Metre", "Gram", "Kg"])
        mik = c4.number_input("Miktar", min_value=0.001, format="%.3f")
        if st.form_submit_button("Reçeteye Ekle"):
            if u not in st.session_state.data["urun_agaclari"]: st.session_state.data["urun_agaclari"][u] = {}
            st.session_state.data["urun_agaclari"][u][m] = {"miktar": mik, "birim": b}
            if m not in st.session_state.data["hammadde_depo"]:
                st.session_state.data["hammadde_depo"][m] = {"miktar": 0.0, "birim": b}
            verileri_kaydet(st.session_state.data); st.success("Malzeme eklendi!"); st.rerun()

# --- BÖLÜM 3: DEPO ---
elif menu == "📦 Depo & Stok":
    st.header("📦 Depo Yönetimi")
    t1, t2 = st.tabs(["🏗️ Hammadde Stoğu", "🏬 Mamul (Ürün) Stoğu"])
    with t1:
        if st.session_state.data["hammadde_depo"]:
            df_h = pd.DataFrame([{"Malzeme": k, "Miktar": v["miktar"], "Birim": v["birim"]} for k, v in st.session_state.data["hammadde_depo"].items()])
            st.table(df_h)
            with st.expander("Hammadde Girişi Yap"):
                h_sec = st.selectbox("Malzeme", list(st.session_state.data["hammadde_depo"].keys()))
                h_mik = st.number_input("Miktar", min_value=0.0)
                if st.button("Stok Ekle"):
                    st.session_state.data["hammadde_depo"][h_sec]["miktar"] += h_mik
                    verileri_kaydet(st.session_state.data); st.rerun()
    with t2:
        if st.session_state.data["mamul_depo"]:
            st.table(pd.DataFrame(st.session_state.data["mamul_depo"]))

# --- BÖLÜM 4: ÜRETİM HATTI ---
elif menu == "🛠️ Üretim Hattı":
    st.header("🛠️ Siparişe Bağlı Üretim Girişi")
    s_options = [f"#{s['id']} | {s['musteri']} | {s['urun']}" for s in st.session_state.data["siparisler"]]
    
    if s_options:
        with st.form("uretim"):
            secilen_s = st.selectbox("Sipariş Seç", s_options)
            u_mik = st.number_input("Üretilen Adet", min_value=1)
            fire = st.number_input("Fire Oranı (%)", min_value=0, value=5)
            if st.form_submit_button("Üretimi Onayla"):
                s_id = int(secilen_s.split(" | ")[0].replace("#", ""))
                sip = next(s for s in st.session_state.data["siparisler"] if s["id"] == s_id)
                
                # Hammadde düşüşü
                recete = st.session_state.data["urun_agaclari"][sip['urun']]
                for m, d in recete.items():
                    lazim = d["miktar"] * u_mik * (1 + (fire/100))
                    st.session_state.data["hammadde_depo"][m]["miktar"] -= lazim
                
                # Mamul girişi
                st.session_state.data["mamul_depo"].append({
                    "Tarih": str(datetime.date.today()), "Sipariş": s_id, "Ürün": sip["urun"], "Miktar": u_mik
                })
                sip["uretilen"] += u_mik
                verileri_kaydet(st.session_state.data)
                st.balloons(); st.rerun()
    else: st.info("Aktif sipariş yok.")

# --- BÖLÜM 5: ANALİZ ---
elif menu == "📊 Analiz & Arşiv":
    st.header("📊 Tamamlanan İşler Analizi")
    if st.session_state.data["tamamlanan_siparisler"]:
        st.table(pd.DataFrame(st.session_state.data["tamamlanan_siparisler"]))
    else: st.info("Arşiv boş.")
