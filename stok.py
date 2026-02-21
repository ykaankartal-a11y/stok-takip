import streamlit as st
import json
import os
import datetime
import pandas as pd

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

# Kullanıcı Bilgilerini Buradan Değiştirebilirsin
GECERLI_KULLANICI = "admin"
GECERLI_SIFRE = "1234"

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
        "tamamlanan_siparisler": []
    }

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="Pro ERP - Yönetim", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.title("🔐 Pro ERP Giriş Paneli")
    with st.form("login_form"):
        kullanici_girisi = st.text_input("Kullanıcı Adı (admin)")
        sifre_girisi = st.text_input("Şifre (1234)", type="password")
        submit = st.form_submit_button("Sisteme Gir")
        
        if submit:
            # Burada küçük/büyük harf duyarlılığını kaldırmak için .lower() kullandım
            if kullanici_girisi.lower() == GECERLI_KULLANICI and sifre_girisi == GECERLI_SIFRE:
                st.session_state.authenticated = True
                st.session_state.current_user = kullanici_girisi
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("❌ Kullanıcı adı veya şifre yanlış. Lütfen tekrar deneyin.")
    st.stop()

# --- ANA UYGULAMA (Giriş Yapıldıysa) ---
st.sidebar.title(f"👤 Operatör: {st.session_state.current_user}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("İşlem Menüsü:", [
    "🛒 Sipariş Yönetimi", 
    "⚙️ Ürün Ağacı (BOM)", 
    "📦 Depo & Stok", 
    "🛠️ Üretim Hattı", 
    "📊 Analiz & Arşiv"
])

# --- BÖLÜM 1: SİPARİŞ YÖNETİMİ ---
if menu == "🛒 Sipariş Yönetimi":
    st.header("🛒 Müşteri Siparişleri")
    
    # Aktif Siparişler
    if st.session_state.data["siparisler"]:
        for idx, sip in enumerate(st.session_state.data["siparisler"]):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{sip['musteri']}** - {sip['urun']} (Hedef: {sip['miktar']})")
            c2.info(f"Üretilen: {sip['uretilen']}")
            if c3.button("Siparişi Arşivle/Kapat", key=f"kapat_{sip['id']}"):
                sip["bitis_tarihi"] = str(datetime.date.today())
                st.session_state.data["tamamlanan_siparisler"].append(sip)
                st.session_state.data["siparisler"].pop(idx)
                verileri_kaydet(st.session_state.data)
                st.rerun()

    with st.expander("➕ Yeni Sipariş Oluştur"):
        with st.form("yeni_sip_form"):
            mus = st.text_input("Müşteri")
            u_l = list(st.session_state.data["urun_agaclari"].keys())
            sec_u = st.selectbox("Ürün", u_l if u_l else ["Önce Reçete Tanımlayın"])
            c1, c2 = st.columns(2)
            mik = c1.number_input("Miktar", min_value=1)
            term = c2.date_input("Termin")
            if st.form_submit_button("Siparişi Kaydet"):
                yeni = {
                    "id": len(st.session_state.data["siparisler"]) + len(st.session_state.data["tamamlanan_siparisler"]) + 1,
                    "musteri": mus, "urun": sec_u, "miktar": mik, "uretilen": 0,
                    "gelis_tarihi": str(datetime.date.today()), "termin": str(term)
                }
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data)
                st.success("Sipariş sisteme alındı.")
                st.rerun()

# --- BÖLÜM 2: ÜRÜN AĞACI ---
elif menu == "⚙️ Ürün Ağacı (BOM)":
    st.header("⚙️ Ürün Reçeteleri")
    with st.form("bom_form"):
        c1, c2, c3, c4 = st.columns(4)
        u = c1.text_input("Ürün Adı")
        m = c2.text_input("Hammadde")
        b = c3.selectbox("Birim", ["Adet", "Metre", "Kg", "mm", "cm", "Gram"])
        mik = c4.number_input("Miktar", min_value=0.001, format="%.3f")
        if st.form_submit_button("Reçeteye Kaydet"):
            if u not in st.session_state.data["urun_agaclari"]: 
                st.session_state.data["urun_agaclari"][u] = {}
            st.session_state.data["urun_agaclari"][u][m] = {"miktar": mik, "birim": b}
            if m not in st.session_state.data["hammadde_depo"]:
                st.session_state.data["hammadde_depo"][m] = {"miktar": 0.0, "birim": b}
            verileri_kaydet(st.session_state.data)
            st.success("BOM Kaydedildi.")
            st.rerun()

# --- BÖLÜM 3: DEPO ---
elif menu == "📦 Depo & Stok":
    st.header("📦 Stok Durumu")
    h_tab, m_tab = st.tabs(["🏗️ Hammadde", "🏬 Mamul (Bitmiş Ürün)"])
    with h_tab:
        if st.session_state.data["hammadde_depo"]:
            df_h = pd.DataFrame([{"Malzeme": k, "Stok": v["miktar"], "Birim": v["birim"]} for k, v in st.session_state.data["hammadde_depo"].items()])
            st.table(df_h)
            with st.expander("📥 Hammadde Girişi"):
                h_sec = st.selectbox("Malzeme Seç", list(st.session_state.data["hammadde_depo"].keys()))
                g_mik = st.number_input("Gelen Miktar", min_value=0.1)
                if st.button("Stok Güncelle"):
                    st.session_state.data["hammadde_depo"][h_sec]["miktar"] += g_mik
                    verileri_kaydet(st.session_state.data)
                    st.rerun()
    with m_tab:
        if st.session_state.data["mamul_depo"]:
            st.table(pd.DataFrame(st.session_state.data["mamul_depo"]))

# --- BÖLÜM 4: ÜRETİM ---
elif menu == "🛠️ Üretim Hattı":
    st.header("🛠️ Üretim Kaydı")
    s_options = [f"#{s['id']} | {s['musteri']} | {s['urun']}" for s in st.session_state.data["siparisler"]]
    if s_options:
        with st.form("uretim_form"):
            sec_s = st.selectbox("Sipariş Seçin", s_options)
            adet = st.number_input("Üretilen Adet", min_value=1)
            fire = st.slider("Fire Oranı (%)", 0, 20, 5)
            if st.form_submit_button("Üretimi Onayla"):
                s_id = int(sec_s.split(" | ")[0].replace("#", ""))
                sip = next(s for s in st.session_state.data["siparisler"] if s["id"] == s_id)
                
                # Stoktan Düş
                recete = st.session_state.data["urun_agaclari"][sip['urun']]
                for m, d in recete.items():
                    toplam_sarf = d["miktar"] * adet * (1 + (fire/100))
                    st.session_state.data["hammadde_depo"][m]["miktar"] -= toplam_sarf
                
                # Mamule Ekle
                st.session_state.data["mamul_depo"].append({
                    "Tarih": str(datetime.date.today()), "Müşteri": sip["musteri"], "Ürün": sip["urun"], "Adet": adet
                })
                sip["uretilen"] += adet
                verileri_kaydet(st.session_state.data)
                st.balloons()
                st.rerun()
    else:
        st.info("Aktif sipariş bulunmuyor.")

# --- BÖLÜM 5: ANALİZ ---
elif menu == "📊 Analiz & Arşiv":
    st.header("📊 Arşivlenmiş Siparişler")
    if st.session_state.data["tamamlanan_siparisler"]:
        st.table(pd.DataFrame(st.session_state.data["tamamlanan_siparisler"]))
