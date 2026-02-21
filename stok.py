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
                for anahtar, tip in varsayilan.items():
                    if anahtar not in mevcut or type(mevcut[anahtar]) != type(tip):
                        mevcut[anahtar] = tip
                return mevcut
        except: return varsayilan
    return varsayilan

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="Pro ERP - Sipariş Yönetimi", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.title("🔐 Pro ERP Yönetim")
    with st.form("login_panel"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u.lower() == "admin" and p == "1234":
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Hatalı Giriş!")
    st.stop()

# --- ANA MENÜ ---
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ YÖNETİMİ", "⚙️ ÜRÜN AĞACI (BOM)", "📦 DEPO & STOK", "🛠️ ÜRETİM GİRİŞİ", "📊 ARŞİV"])

# --- BÖLÜM 1: SİPARİŞ YÖNETİMİ ---
if menu == "🛒 SİPARİŞ YÖNETİMİ":
    st.header("🛒 SİPARİŞ YÖNETİM MERKEZİ")
    
    # Mevcut Siparişleri Tablo Olarak Göster (BÜYÜK HARF BAŞLIKLAR)
    if st.session_state.data["siparisler"]:
        df_sip = pd.DataFrame(st.session_state.data["siparisler"])
        # Sütunları Türkçeleştir ve Büyük Harf Yap
        df_sip = df_sip.rename(columns={
            "kod": "SİPARİŞ KODU",
            "musteri": "MÜŞTERİ ADI",
            "urun": "ÜRÜN",
            "miktar": "HEDEF MİKTAR",
            "uretilen": "ÜRETİLEN MİKTAR",
            "termin": "TERMİN TARİHİ"
        })
        st.subheader("📋 AKTİF SİPARİŞ LİSTESİ")
        st.dataframe(df_sip, use_container_width=True)

        # DÜZENLEME VE KAPATMA ALANI
        st.markdown("---")
        st.subheader("🛠️ SİPARİŞ DÜZENLE VEYA KAPAT")
        for idx, s in enumerate(st.session_state.data["siparisler"]):
            with st.expander(f"📝 DÜZENLE: {s.get('kod', 'KODSUZ')} - {s['musteri']}"):
                c1, c2, c3 = st.columns(3)
                y_mik = c1.number_input("YENİ MİKTAR", value=int(s['miktar']), key=f"mik_{idx}")
                y_term = c2.date_input("YENİ TERMİN", value=datetime.datetime.strptime(s['termin'], "%Y-%m-%d"), key=f"term_{idx}")
                y_kod = c3.text_input("SİPARİŞ KODU REVİZE", value=s.get('kod', ''), key=f"kod_{idx}")
                
                b1, b2, b3 = st.columns([1,1,2])
                if b1.button("✅ GÜNCELLE", key=f"btn_g_{idx}"):
                    s['miktar'] = y_mik
                    s['termin'] = str(y_term)
                    s['kod'] = y_kod
                    verileri_kaydet(st.session_state.data)
                    st.success("GÜNCELLENDİ!")
                    st.rerun()
                
                if b2.button("🏁 SİPARİŞİ KAPAT", key=f"btn_k_{idx}"):
                    s["bitis_tarihi"] = str(datetime.date.today())
                    st.session_state.data["tamamlanan_siparisler"].append(s)
                    st.session_state.data["siparisler"].pop(idx)
                    verileri_kaydet(st.session_state.data)
                    st.rerun()

    # YENİ SİPARİŞ EKLEME
    with st.expander("➕ YENİ SİPARİŞ OLUŞTUR"):
        with st.form("yeni_sip"):
            c1, c2 = st.columns(2)
            y_s_kod = c1.text_input("SİPARİŞ KODU (Örn: SK-202)")
            y_m_adi = c2.text_input("MÜŞTERİ ADI")
            
            u_list = list(st.session_state.data.get("urun_agaclari", {}).keys())
            y_urun = st.selectbox("ÜRÜN SEÇİN", u_list if u_list else ["Önce Reçete Tanımlayın"])
            
            c3, c4 = st.columns(2)
            y_mik = c3.number_input("SİPARİŞ MİKTARI", min_value=1)
            y_term = c4.date_input("TERMİN TARİHİ")
            
            if st.form_submit_button("💾 SİPARİŞİ KAYDET"):
                if not y_s_kod: y_s_kod = f"SIP-{len(st.session_state.data['siparisler']) + 101}"
                yeni = {
                    "kod": y_s_kod.upper(),
                    "musteri": y_m_adi.upper(),
                    "urun": y_urun,
                    "miktar": y_mik,
                    "uretilen": 0,
                    "termin": str(y_term)
                }
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data)
                st.success(f"{y_s_kod} NUMARALI SİPARİŞ AÇILDI")
                st.rerun()

# --- BÖLÜM 2: ÜRÜN AĞACI (BOM) ---
elif menu == "⚙️ ÜRÜN AĞACI (BOM)":
    st.header("⚙️ ÜRÜN REÇETESİ TANIMLAMA")
    with st.form("bom_form"):
        c1, c2, c3, c4 = st.columns(4)
        u = c1.text_input("ANA ÜRÜN ADI")
        m = c2.text_input("HAMMADDE ADI")
        b = c3.selectbox("BİRİM", ["Adet", "Metre", "Kg", "Gram"])
        mik = c4.number_input("MİKTAR", min_value=0.001, format="%.3f")
        if st.form_submit_button("REÇETEYE EKLE"):
            if u not in st.session_state.data["urun_agaclari"]: st.session_state.data["urun_agaclari"][u] = {}
            st.session_state.data["urun_agaclari"][u][m] = {"miktar": mik, "birim": b}
            if m not in st.session_state.data["hammadde_depo"]: st.session_state.data["hammadde_depo"][m] = {"miktar": 0.0, "birim": b}
            verileri_kaydet(st.session_state.data); st.success("BAŞARIYLA EKLENDİ"); st.rerun()

# --- BÖLÜM 3: DEPO ---
elif menu == "📦 DEPO & STOK":
    st.header("📦 DEPO DURUMU")
    h_tab, m_tab = st.tabs(["🏗️ HAMMADDE STOĞU", "🏬 MAMUL STOĞU"])
    with h_tab:
        depo = st.session_state.data.get("hammadde_depo", {})
        if depo:
            df_h = pd.DataFrame([{"MALZEME": k, "STOK": v["miktar"], "BİRİM": v["birim"]} for k, v in depo.items()])
            st.table(df_h)
            with st.expander("📥 STOK GİRİŞİ YAP"):
                s_m = st.selectbox("MALZEME SEÇ", list(depo.keys()))
                s_mik = st.number_input("GELEN MİKTAR", min_value=0.1)
                if st.button("STOK GÜNCELLE"):
                    st.session_state.data["hammadde_depo"][s_m]["miktar"] += s_mik
                    verileri_kaydet(st.session_state.data); st.rerun()
    with m_tab:
        mamul = st.session_state.data.get("mamul_depo", [])
        if mamul:
            df_m = pd.DataFrame(mamul).rename(columns={"Tarih": "TARİH", "Müşteri": "MÜŞTERİ", "Ürün": "ÜRÜN", "Adet": "MİKTAR"})
            st.table(df_m)

# --- BÖLÜM 4: ÜRETİM ---
elif menu == "🛠️ ÜRETİM GİRİŞİ":
    st.header("🛠️ ÜRETİM KAYDI OLUŞTUR")
    sips = st.session_state.data.get("siparisler", [])
    s_ops = [f"{s['kod']} | {s['musteri']} | {s['urun']}" for s in sips]
    if s_ops:
        with st.form("üretim_f"):
            s_sec = st.selectbox("ÜRETİM YAPILAN SİPARİŞ", s_ops)
            u_adet = st.number_input("ÜRETİLEN ADET", min_value=1)
            if st.form_submit_button("⚙️ ÜRETİMİ TAMAMLA"):
                s_kod_sec = s_sec.split(" | ")[0]
                sip = next(s for s in sips if s['kod'] == s_kod_sec)
                # Stoktan düş
                r = st.session_state.data["urun_agaclari"].get(sip['urun'], {})
                for malz, det in r.items():
                    if malz in st.session_state.data["hammadde_depo"]:
                        st.session_state.data["hammadde_depo"][malz]["miktar"] -= (det["miktar"] * u_adet)
                # Kaydet
                st.session_state.data["mamul_depo"].append({"Tarih": str(datetime.date.today()), "Müşteri": sip["musteri"], "Ürün": sip["urun"], "Adet": u_adet})
                sip["uretilen"] += u_adet
                verileri_kaydet(st.session_state.data); st.balloons(); st.rerun()
    else: st.info("Üretim yapılacak aktif sipariş bulunamadı.")

# --- BÖLÜM 5: ARŞİV ---
elif menu == "📊 ARŞİV":
    st.header("📊 TAMAMLANAN SİPARİŞLER")
    arsiv = st.session_state.data.get("tamamlanan_siparisler", [])
    if arsiv:
        df_a = pd.DataFrame(arsiv).rename(columns={
            "kod": "SİPARİŞ KODU", "musteri": "MÜŞTERİ", "urun": "ÜRÜN", 
            "miktar": "HEDEF", "uretilen": "GERÇEKLEŞEN", "bitis_tarihi": "KAPANIŞ"
        })
        st.dataframe(df_a, use_container_width=True)
