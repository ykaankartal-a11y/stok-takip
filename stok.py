import streamlit as st
import json
import os
import datetime
import pandas as pd

# --- VERİ YÖNETİMİ ---
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    varsayilan = {"hammadde_depo": {}, "mamul_depo": [], "urun_agaclari": {}, "siparisler": [], "tamamlanan_siparisler": [], "kullanicilar": {"admin": "1234"}}
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

st.set_page_config(page_title="Pro ERP | Üretim & Stok", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.title("🔐 FABRİKA YÖNETİM SİSTEMİ")
    with st.container():
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            with st.form("login"):
                u = st.text_input("Kullanıcı Adı")
                p = st.text_input("Şifre", type="password")
                if st.form_submit_button("Sisteme Giriş Yap"):
                    if u.lower() == "admin" and p == "1234":
                        st.session_state.authenticated = True
                        st.rerun()
                    else: st.error("Hatalı Giriş!")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
def stok_kontrol_et(urun, hedef_miktar):
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    if not recete: return True, []
    eksikler = []
    for malz, detay in recete.items():
        gerekli = detay["miktar"] * hedef_miktar
        mevcut = st.session_state.data["hammadde_depo"].get(malz, {}).get("miktar", 0)
        if mevcut < gerekli:
            eksikler.append(f"{malz} ({gerekli - mevcut:.2f} {detay['birim']} eksik)")
    return (len(eksikler) == 0, eksikler)

# --- ANA MENÜ ---
st.sidebar.markdown("### 🏢 ANA MENÜ")
menu = st.sidebar.radio("", ["🛒 SİPARİŞ TAKİBİ", "🛠️ ÜRETİM KAYDI", "⚙️ ÜRÜN REÇETELERİ", "📦 DEPO DURUMU", "📊 ARŞİV"])

# --- BÖLÜM 1: SİPARİŞ TAKİBİ (YENİ GÖRÜNÜM) ---
if menu == "🛒 SİPARİŞ TAKİBİ":
    st.header("🛒 Aktif Sipariş Yönetimi")
    
    with st.expander("➕ YENİ SİPARİŞ EKLE"):
        toplam = len(st.session_state.data["siparisler"]) + len(st.session_state.data["tamamlanan_siparisler"])
        otomatik_kod = f"SIP-{1001 + toplam}"
        with st.form("yeni_sip"):
            c1, c2 = st.columns(2)
            m_adi = c1.text_input("Müşteri Adı")
            u_list = list(st.session_state.data.get("urun_agaclari", {}).keys())
            sec_u = c2.selectbox("Ürün Seçin", u_list if u_list else ["Önce Reçete Tanımlayın"])
            c3, c4 = st.columns(2)
            mik = c3.number_input("Sipariş Miktarı", min_value=1)
            term = c4.date_input("Termin Tarihi")
            if st.form_submit_button("Siparişi Kaydet"):
                yeni = {"kod": otomatik_kod, "musteri": m_adi.upper(), "urun": sec_u, "miktar": mik, "uretilen": 0, "termin": str(term)}
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data)
                st.success(f"Sipariş {otomatik_kod} başarıyla eklendi.")
                st.rerun()

    st.markdown("---")
    
    if st.session_state.data["siparisler"]:
        for idx, s in enumerate(st.session_state.data["siparisler"]):
            stok_ok, eksik_list = stok_kontrol_et(s["urun"], s["miktar"])
            renk = "green" if stok_ok else "red"
            durum_metni = "✅ STOK HAZIR" if stok_ok else "❌ STOK YETERSİZ"
            
            # Şık Sipariş Kartı
            with st.container():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.subheader(f"{s['kod']} | {s['musteri']}")
                    st.write(f"📦 **Ürün:** {s['urun']} | 🎯 **Hedef:** {s['miktar']} | 🛠️ **Üretilen:** {s['uretilen']} | 📅 **Termin:** {s['termin']}")
                    if not stok_ok:
                        st.caption(f"⚠️ Eksikler: {', '.join(eksik_list)}")
                with col_b:
                    st.markdown(f"### :{renk}[{durum_metni}]")
                
                # Düzenleme Seçenekleri (Expander içinde)
                with st.expander("Siparişi Düzenle veya Kapat"):
                    c1, c2, c3 = st.columns(3)
                    e_mik = c1.number_input("Miktar", value=int(s['miktar']), key=f"e_m_{idx}")
                    e_term = c2.date_input("Termin", value=datetime.datetime.strptime(s['termin'], "%Y-%m-%d"), key=f"e_t_{idx}")
                    e_kod = c3.text_input("Kod", value=s.get('kod'), key=f"e_k_{idx}")
                    
                    b1, b2 = st.columns(2)
                    if b1.button("Güncelle", key=f"up_{idx}"):
                        s['miktar'], s['termin'], s['kod'] = e_mik, str(e_term), e_kod.upper()
                        verileri_kaydet(st.session_state.data); st.rerun()
                    if b2.button("Siparişi Kapat (Arşivle)", key=f"cl_{idx}"):
                        s["bitis"] = str(datetime.date.today())
                        st.session_state.data["tamamlanan_siparisler"].append(s)
                        st.session_state.data["siparisler"].pop(idx)
                        verileri_kaydet(st.session_state.data); st.rerun()
            st.markdown("---")

# --- BÖLÜM 2: ÜRETİM KAYDI (NETLEŞTİRİLDİ) ---
elif menu == "🛠️ ÜRETİM KAYDI":
    st.header("🛠️ Üretim Sonu Kaydı Girişi")
    sips = st.session_state.data.get("siparisler", [])
    
    if sips:
        # Hangi sipariş için üretim yapıldığını netleştiren liste
        sip_secenekleri = {f"{s['kod']} - {s['musteri']} ({s['urun']})": s for s in sips}
        secilen_etiket = st.selectbox("Üretim Yapılan Siparişi Seçin:", list(sip_secenekleri.keys()))
        secilen_sip = sip_secenekleri[secilen_etiket]
        
        st.info(f"Seçili Sipariş: **{secilen_sip['kod']}** | Kalan İhtiyaç: **{secilen_sip['miktar'] - secilen_sip['uretilen']}** adet.")
        
        with st.form("uretim_form"):
            u_miktar = st.number_input("Şu An Üretilen Miktar (Adet)", min_value=1)
            if st.form_submit_button("Üretimi Depoya İşle"):
                # Stok Düşümü ve Kontrolü
                hata = False
                recete = st.session_state.data["urun_agaclari"].get(secilen_sip['urun'], {})
                for m, d in recete.items():
                    if st.session_state.data["hammadde_depo"].get(m, {}).get("miktar", 0) < (d["miktar"] * u_miktar):
                        hata = True
                        st.error(f"Yetersiz Hammadde: {m}")
                
                if not hata:
                    for m, d in recete.items():
                        st.session_state.data["hammadde_depo"][m]["miktar"] -= (d["miktar"] * u_miktar)
                    
                    # Mamul depoya ekle ve siparişi güncelle
                    st.session_state.data["mamul_depo"].append({
                        "tarih": str(datetime.date.today()),
                        "kod": secilen_sip['kod'],
                        "musteri": secilen_sip['musteri'],
                        "urun": secilen_sip['urun'],
                        "miktar": u_miktar
                    })
                    secilen_sip["uretilen"] += u_miktar
                    verileri_kaydet(st.session_state.data)
                    st.balloons()
                    st.success("Üretim kaydı başarıyla işlendi!")
                    st.rerun()
    else:
        st.warning("Üretim yapılacak aktif bir sipariş bulunamadı.")

# --- DİĞER BÖLÜMLER (BOM ve DEPO) ---
elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ Ürün Reçete Tanımları (BOM)")
    with st.form("bom"):
        c1, c2, c3, c4 = st.columns(4)
        u = c1.text_input("Ürün Adı").upper()
        m = c2.text_input("Hammadde").upper()
        b = c3.selectbox("Birim", ["Adet", "Metre", "Kg", "Gr"])
        mik = c4.number_input("Tüketim Miktarı", min_value=0.001, format="%.3f")
        if st.form_submit_button("Reçeteye Kaydet"):
            if u not in st.session_state.data["urun_agaclari"]: st.session_state.data["urun_agaclari"][u] = {}
            st.session_state.data["urun_agaclari"][u][m] = {"miktar": mik, "birim": b}
            if m not in st.session_state.data["hammadde_depo"]: st.session_state.data["hammadde_depo"][m] = {"miktar": 0.0, "birim": b}
            verileri_kaydet(st.session_state.data); st.rerun()
    
    if st.session_state.data["urun_agaclari"]:
        for urun, malzemeler in st.session_state.data["urun_agaclari"].items():
            with st.expander(f"📖 {urun} Reçetesi"):
                st.write(pd.DataFrame([{"Malzeme": k, "Miktar": v["miktar"], "Birim": v["birim"]} for k, v in malzemeler.items()]))

elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo ve Stok Yönetimi")
    t1, t2 = st.tabs(["🏗️ Hammadde", "🏬 Üretilen Mamuller"])
    with t1:
        h_depo = st.session_state.data.get("hammadde_depo", {})
        if h_depo:
            st.table(pd.DataFrame([{"MALZEME": k, "MEVCUT STOK": v["miktar"], "BİRİM": v["birim"]} for k, v in h_depo.items()]))
            with st.expander("📥 Stok Girişi Yap"):
                s_m = st.selectbox("Malzeme Seç", list(h_depo.keys()))
                s_mik = st.number_input("Gelen Miktar", min_value=0.1)
                if st.button("Stoku Güncelle"):
                    st.session_state.data["hammadde_depo"][s_m]["miktar"] += s_mik
                    verileri_kaydet(st.session_state.data); st.rerun()
    with t2:
        m_depo = st.session_state.data.get("mamul_depo", [])
        if m_depo: st.dataframe(pd.DataFrame(m_depo), use_container_width=True)

elif menu == "📊 ARŞİV":
    st.header("📊 Tamamlanan Siparişler Arşivi")
    arsiv = st.session_state.data.get("tamamlanan_siparisler", [])
    if arsiv: st.dataframe(pd.DataFrame(arsiv), use_container_width=True)
