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

# --- YARDIMCI: AKILLI SAYI FORMATLAMA ---
def format_sayi(deger, birim="ADET"):
    try:
        if birim.upper() == "ADET":
            return f"{int(float(deger))}"
        return f"{float(deger):.2f}"
    except:
        return deger

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #0078D7;'>ALFA TECH</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Endüstriyel Üretim ve Stok Yönetimi</h3>", unsafe_allow_html=True)
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

# --- SOL ÜST KÖŞE LOGO/İSİM ---
st.sidebar.markdown("<h1 style='text-align: center; color: #0078D7; border-bottom: 2px solid #0078D7;'>ALFA TECH</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 0.8em;'>ERP SİSTEMİ v2.0</p>", unsafe_allow_html=True)

# --- YARDIMCI: STOK KONTROLÜ ---
def stok_kontrol_et(urun, hedef_miktar):
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    if not recete: return True, []
    eksikler = []
    for malz, detay in recete.items():
        gerekli = detay["miktar"] * hedef_miktar
        mevcut = st.session_state.data["hammadde_depo"].get(malz, {}).get("miktar", 0)
        if mevcut < gerekli:
            eksik_mik = gerekli - mevcut
            eksikler.append(f"{malz} (Eksik: {format_sayi(eksik_mik, detay['birim'])} {detay['birim']})")
    return (len(eksikler) == 0, eksikler)

# --- ANA MENÜ ---
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ TAKİBİ", "🛠️ ÜRETİM KAYDI", "⚙️ ÜRÜN REÇETELERİ", "📦 DEPO DURUMU", "📊 ARŞİV"])

# --- BÖLÜM 1: SİPARİŞ TAKİBİ ---
if menu == "🛒 SİPARİŞ TAKİBİ":
    st.header("🛒 Aktif Sipariş Yönetimi")
    
    with st.expander("➕ YENİ SİPARİŞ EKLE"):
        toplam = len(st.session_state.data["siparisler"]) + len(st.session_state.data["tamamlanan_siparisler"])
        otomatik_kod = f"SIP-{1001 + toplam}"
        with st.form("yeni_sip"):
            m_adi = st.text_input("Müşteri Adı")
            u_list = list(st.session_state.data.get("urun_agaclari", {}).keys())
            sec_u = st.selectbox("Ürün Seçin", u_list if u_list else ["Önce Reçete Tanımlayın"])
            c3, c4 = st.columns(2)
            mik = c3.number_input("Sipariş Miktarı (Adet)", min_value=1, step=1)
            term = c4.date_input("Termin Tarihi")
            if st.form_submit_button("Siparişi Kaydet"):
                yeni = {"kod": otomatik_kod, "musteri": m_adi.upper(), "urun": sec_u, "miktar": int(mik), "uretilen": 0, "termin": str(term)}
                st.session_state.data["siparisler"].append(yeni)
                verileri_kaydet(st.session_state.data); st.success(f"{otomatik_kod} açıldı."); st.rerun()

    st.markdown("---")
    
    if st.session_state.data["siparisler"]:
        for idx, s in enumerate(st.session_state.data["siparisler"]):
            stok_ok, eksik_list = stok_kontrol_et(s["urun"], s["miktar"])
            renk = "green" if stok_ok else "red"
            durum_metni = "✅ STOK HAZIR" if stok_ok else "❌ STOK YETERSİZ"
            
            with st.container():
                c_sol, c_sag = st.columns([4, 1])
                with c_sol:
                    st.subheader(f"{s['kod']} | {s['musteri']}")
                    h_mik = format_sayi(s['miktar'])
                    u_mik = format_sayi(s['uretilen'])
                    st.write(f"📦 **Ürün:** {s['urun']} | 🎯 **Hedef:** {h_mik} | 🛠️ **Üretilen:** {u_mik} | 📅 **Termin:** {s['termin']}")
                    if not stok_ok:
                        st.caption(f"⚠️ Eksikler: {', '.join(eksik_list)}")
                with c_sag:
                    st.markdown(f"### :{renk}[{durum_metni}]")
                
                with st.expander("Siparişi Düzenle veya Kapat"):
                    c1, c2, c3 = st.columns(3)
                    e_mik = c1.number_input("Miktar", value=int(s['miktar']), key=f"e_m_{idx}", step=1)
                    e_term = c2.date_input("Termin", value=datetime.datetime.strptime(s['termin'], "%Y-%m-%d"), key=f"e_t_{idx}")
                    e_kod = c3.text_input("Kod", value=s.get('kod'), key=f"e_k_{idx}")
                    if st.button("Güncelle", key=f"up_{idx}"):
                        s['miktar'], s['termin'], s['kod'] = int(e_mik), str(e_term), e_kod.upper()
                        verileri_kaydet(st.session_state.data); st.rerun()
                    if st.button("Siparişi Kapat", key=f"cl_{idx}"):
                        s["bitis"] = str(datetime.date.today())
                        st.session_state.data["tamamlanan_siparisler"].append(s)
                        st.session_state.data["siparisler"].pop(idx)
                        verileri_kaydet(st.session_state.data); st.rerun()
            st.markdown("---")

# --- BÖLÜM 2: ÜRETİM KAYDI ---
elif menu == "🛠️ ÜRETİM KAYDI":
    st.header("🛠️ ALFA TECH Üretim Girişi")
    sips = st.session_state.data.get("siparisler", [])
    if sips:
        sip_secenekleri = {f"{s['kod']} - {s['musteri']} ({s['urun']})": s for s in sips}
        sec_etiket = st.selectbox("Üretim Yapılan Siparişi Seçin:", list(sip_secenekleri.keys()))
        sec_sip = sip_secenekleri[sec_etiket]
        kalan = format_sayi(sec_sip['miktar'] - sec_sip['uretilen'])
        st.info(f"Seçili: **{sec_sip['kod']}** | Kalan İhtiyaç: **{kalan}** Adet")
        
        with st.form("uretim"):
            u_mik = st.number_input("Üretilen Miktar (Adet)", min_value=1, step=1)
            if st.form_submit_button("Üretimi Sisteme İşle"):
                hata = False
                recete = st.session_state.data["urun_agaclari"].get(sec_sip['urun'], {})
                for m, d in recete.items():
                    if st.session_state.data["hammadde_depo"].get(m, {}).get("miktar", 0) < (d["miktar"] * u_mik):
                        hata = True; st.error(f"Yetersiz Stok: {m}")
                if not hata:
                    for m, d in recete.items():
                        st.session_state.data["hammadde_depo"][m]["miktar"] -= (d["miktar"] * u_mik)
                    st.session_state.data["mamul_depo"].append({
                        "tarih": str(datetime.date.today()), "kod": sec_sip['kod'], 
                        "musteri": sec_sip['musteri'], "urun": sec_sip['urun'], "miktar": int(u_mik)
                    })
                    sec_sip["uretilen"] += int(u_mik)
                    verileri_kaydet(st.session_state.data); st.balloons(); st.rerun()
    else: st.warning("Aktif sipariş yok.")

# --- BÖLÜM 3: ÜRÜN REÇETELERİ ---
elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ ALFA TECH Reçete Merkezi")
    with st.form("bom"):
        c1, c2, c3, c4 = st.columns(4)
        u, m = c1.text_input("Ürün").upper(), c2.text_input("Hammadde").upper()
        b = c3.selectbox("Birim", ["ADET", "METRE", "KG", "GRAM"])
        mik = c4.number_input("Birim Tüketim", min_value=0.001, format="%.3f")
        if st.form_submit_button("Reçeteye Ekle"):
            if u not in st.session_state.data["urun_agaclari"]: st.session_state.data["urun_agaclari"][u] = {}
            st.session_state.data["urun_agaclari"][u][m] = {"miktar": mik, "birim": b}
            if m not in st.session_state.data["hammadde_depo"]: st.session_state.data["hammadde_depo"][m] = {"miktar": 0.0, "birim": b}
            verileri_kaydet(st.session_state.data); st.rerun()
    
    for urun, malz in st.session_state.data["urun_agaclari"].items():
        with st.expander(f"📖 {urun} Reçetesi"):
            df_view = pd.DataFrame([{"Malzeme": k, "Miktar": v["miktar"], "Birim": v["birim"]} for k, v in malz.items()])
            st.table(df_view)

# --- BÖLÜM 4: DEPO DURUMU ---
elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo ve Stok Yönetimi")
    t1, t2 = st.tabs(["🏗️ Hammadde", "🏬 Mamul (Stoktaki Ürünler)"])
    with t1:
        h_depo = st.session_state.data.get("hammadde_depo", {})
        if h_depo:
            h_list = []
            for k, v in h_depo.items():
                h_list.append({"MALZEME": k, "STOK": format_sayi(v['miktar'], v['birim']), "BİRİM": v['birim']})
            st.table(pd.DataFrame(h_list))
            with st.expander("📥 Stok Girişi"):
                s_m = st.selectbox("Malzeme", list(h_depo.keys()))
                s_mik = st.number_input("Miktar", min_value=0.001, format="%.3f")
                if st.button("Güncelle"):
                    st.session_state.data["hammadde_depo"][s_m]["miktar"] += s_mik
                    verileri_kaydet(st.session_state.data); st.rerun()
    with t2:
        m_depo = st.session_state.data.get("mamul_depo", [])
        if m_depo: 
            df_m = pd.DataFrame(m_depo)
            if "miktar" in df_m.columns:
                df_m["miktar"] = df_m["miktar"].apply(lambda x: format_sayi(x, "ADET"))
            st.dataframe(df_m, use_container_width=True)

elif menu == "📊 ARŞİV":
    st.header("📊 ALFA TECH Üretim Arşivi")
    arsiv = st.session_state.data.get("tamamlanan_siparisler", [])
    if arsiv: 
        df_a = pd.DataFrame(arsiv)
        for col in ["miktar", "uretilen"]:
            if col in df_a.columns:
                df_a[col] = df_a[col].apply(lambda x: format_sayi(x, "ADET"))
        st.dataframe(df_a, use_container_width=True)
