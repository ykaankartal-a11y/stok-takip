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

def format_sayi(deger, birim="ADET"):
    try:
        if birim.upper() == "ADET": return f"{int(float(deger))}"
        return f"{float(deger):.2f}"
    except: return deger

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="ALFA TECH | ERP", layout="wide")

# --- GİRİŞ EKRANI ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #0078D7;'>ALFA TECH</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap"):
                if u.lower() == "admin" and p == "1234":
                    st.session_state.authenticated = True
                    st.rerun()
                else: st.error("Hatalı Giriş!")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("<h1 style='text-align: center; color: #0078D7;'>ALFA TECH</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("MENÜ", ["🛒 SİPARİŞ TAKİBİ", "🛠️ ÜRETİM KAYDI", "⚙️ ÜRÜN REÇETELERİ", "📦 DEPO DURUMU", "📊 ARŞİV"])

# --- YARDIMCI: STOK ANALİZİ ---
def stok_analizi(urun, hedef_miktar):
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    analiz_listesi = []
    tamam_mi = True
    for malz, detay in recete.items():
        gerekli = detay["miktar"] * hedef_miktar
        mevcut = st.session_state.data["hammadde_depo"].get(malz, {}).get("miktar", 0)
        eksik = max(0, gerekli - mevcut)
        if eksik > 0: tamam_mi = False
        analiz_listesi.append({
            "Malzeme": malz, "Gereken": format_sayi(gerekli, detay['birim']),
            "Mevcut": format_sayi(mevcut, detay['birim']), "Eksik": format_sayi(eksik, detay['birim']), "Birim": detay['birim']
        })
    return tamam_mi, analiz_listesi

# --- POP-UP PENCERELER ---
@st.dialog("➕ YENİ SİPARİŞ GİRİŞİ")
def yeni_siparis_penceresi():
    toplam = len(st.session_state.data["siparisler"]) + len(st.session_state.data["tamamlanan_siparisler"])
    otomatik_kod = f"SIP-{1001 + toplam}"
    st.write(f"Sipariş No: **{otomatik_kod}**")
    m_adi = st.text_input("Müşteri Adı")
    u_list = list(st.session_state.data.get("urun_agaclari", {}).keys())
    sec_u = st.selectbox("Ürün Seçin", u_list if u_list else ["Reçete Tanımlayın"])
    c1, c2 = st.columns(2)
    mik = c1.number_input("Miktar", min_value=1, step=1)
    term = c2.date_input("Termin")
    if st.button("💾 SİPARİŞİ OLUŞTUR", use_container_width=True):
        if m_adi:
            yeni = {"kod": otomatik_kod, "musteri": m_adi.upper(), "urun": sec_u, "miktar": int(mik), "uretilen": 0, "termin": str(term)}
            st.session_state.data["siparisler"].append(yeni)
            verileri_kaydet(st.session_state.data); st.rerun()

@st.dialog("🔍 SİPARİŞ VE STOK DETAYI")
def siparis_detay_penceresi(siparis):
    st.subheader(f"{siparis['kod']} - {siparis['musteri']}")
    st.write(f"📦 **Ürün:** {siparis['urun']} | 🎯 **Hedef:** {format_sayi(siparis['miktar'])}")
    tamam_mi, analiz = stok_analizi(siparis['urun'], siparis['miktar'])
    if not analiz: st.warning("⚠️ Bu ürün için tanımlanmış bir reçete bulunamadı.")
    else:
        st.write("### 📋 Hammadde İhtiyaç Analizi")
        st.table(pd.DataFrame(analiz))
        if tamam_mi: st.success("✅ Üretim için tüm hammaddeler depoda mevcut.")
        else: st.error("❌ Eksik hammaddeler var. Lütfen stok girişi yapın.")

# --- ANA MENÜ İÇERİKLERİ ---

if menu == "🛒 SİPARİŞ TAKİBİ":
    c_baslik, c_buton = st.columns([4, 1])
    with c_baslik: st.header("🛒 Aktif Siparişler")
    with c_buton:
        st.write("")
        if st.button("➕ YENİ SİPARİŞ", use_container_width=True, type="primary"): yeni_siparis_penceresi()
    st.markdown("---")
    if st.session_state.data["siparisler"]:
        for idx, s in enumerate(st.session_state.data["siparisler"]):
            stok_ok, _ = stok_analizi(s["urun"], s["miktar"])
            durum_color = "#28a745" if stok_ok else "#dc3545"
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
                with col1: st.markdown(f"<div style='border-left: 5px solid {durum_color}; padding-left: 10px; font-weight: bold;'>{s['kod']}</div>", unsafe_allow_html=True)
                with col2: st.write(f"👤 {s['musteri']}"); st.caption(f"📦 {s['urun']}")
                with col3: st.write(f"🎯 {format_sayi(s['uretilen'])} / {format_sayi(s['miktar'])}"); st.caption(f"📅 {s['termin']}")
                with col4:
                    if st.button("🔍 DETAY", key=f"detay_{idx}", use_container_width=True): siparis_detay_penceresi(s)
                with col5:
                    with st.expander("⚙️"):
                        if st.button("KAPAT", key=f"cl_{idx}", use_container_width=True):
                            s["bitis"] = str(datetime.date.today())
                            st.session_state.data["tamamlanan_siparisler"].append(s)
                            st.session_state.data["siparisler"].pop(idx)
                            verileri_kaydet(st.session_state.data); st.rerun()
            st.divider()

elif menu == "🛠️ ÜRETİM KAYDI":
    st.header("🛠️ Üretim Sonu Girişi")
    sips = st.session_state.data.get("siparisler", [])
    if sips:
        sip_secenekleri = {f"{s['kod']} - {s['musteri']}": s for s in sips}
        sec_etiket = st.selectbox("Sipariş Seçin:", list(sip_secenekleri.keys()))
        sec_sip = sip_secenekleri[sec_etiket]
        with st.form("uretim"):
            u_mik = st.number_input(f"{sec_sip['urun']} Üretilen Miktar", min_value=1, step=1)
            if st.form_submit_button("Üretimi Onayla"):
                tamam_mi, _ = stok_analizi(sec_sip['urun'], u_mik)
                if not tamam_mi: st.error("Stok yetersiz! Lütfen hammadde stoğunu kontrol edin.")
                else:
                    recete = st.session_state.data["urun_agaclari"].get(sec_sip['urun'], {})
                    for m, d in recete.items():
                        st.session_state.data["hammadde_depo"][m]["miktar"] -= (d["miktar"] * u_mik)
                    st.session_state.data["mamul_depo"].append({"tarih": str(datetime.date.today()), "kod": sec_sip['kod'], "urun": sec_sip['urun'], "miktar": int(u_mik)})
                    sec_sip["uretilen"] += int(u_mik)
                    verileri_kaydet(st.session_state.data); st.balloons(); st.rerun()

elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ ALFA TECH Reçete Editörü")
    with st.expander("🆕 YENİ ÜRÜN REÇETESİ TANIMLA", expanded=True):
        ana_urun = st.text_input("ÜRETİLECEK ANA ÜRÜN ADI").upper()
        if "rows" not in st.session_state: st.session_state.rows = 1
        for i in range(st.session_state.rows):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1: st.text_input(f"Hammadde {i+1}", key=f"h_ad_{i}", placeholder="Hammadde Adı").upper()
            with c2: st.number_input("Miktar", min_value=0.001, format="%.3f", key=f"h_mik_{i}")
            with c3: st.selectbox("Birim", ["ADET", "KG", "METRE", "GRAM"], key=f"h_birim_{i}")
        
        c_alt1, c_alt2 = st.columns([1, 4])
        with c_alt1:
            if st.button("➕ Satır Ekle"): 
                st.session_state.rows += 1
                st.rerun()
        with c_alt2:
            if st.button("💾 REÇETEYİ KAYDET", type="primary", use_container_width=True):
                if ana_urun:
                    yeni_recete = {}
                    for i in range(st.session_state.rows):
                        h_name = st.session_state[f"h_ad_{i}"].upper()
                        h_qty = st.session_state[f"h_mik_{i}"]
                        h_unit = st.session_state[f"h_birim_{i}"]
                        if h_name:
                            yeni_recete[h_name] = {"miktar": h_qty, "birim": h_unit}
                            if h_name not in st.session_state.data["hammadde_depo"]:
                                st.session_state.data["hammadde_depo"][h_name] = {"miktar": 0.0, "birim": h_unit}
                    st.session_state.data["urun_agaclari"][ana_urun] = yeni_recete
                    verileri_kaydet(st.session_state.data)
                    st.session_state.rows = 1
                    st.success(f"{ana_urun} Kaydedildi!"); st.rerun()
                else: st.error("Ürün adı giriniz!")

    st.markdown("---")
    if st.session_state.data["urun_agaclari"]:
        for urun, malz in st.session_state.data["urun_agaclari"].items():
            with st.expander(f"📖 {urun} Reçetesi"):
                st.table(pd.DataFrame([{"MALZEME": k, "MİKTAR": v["miktar"], "BİRİM": v["birim"]} for k, v in malz.items()]))
                if st.button(f"🗑️ {urun} Sil", key=f"del_{urun}"):
                    del st.session_state.data["urun_agaclari"][urun]
                    verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo")
    h_tab, m_tab = st.tabs(["🏗️ Hammadde", "🏬 Mamul"])
    with h_tab:
        h_depo = st.session_state.data.get("hammadde_depo", {})
        if h_depo:
            h_list = [{"MALZEME": k, "STOK": format_sayi(v['miktar'], v['birim']), "BİRİM": v['birim']} for k, v in h_depo.items()]
            st.table(pd.DataFrame(h_list))
            with st.expander("📥 Stok Girişi"):
                s_m = st.selectbox("Malzeme", list(h_depo.keys()))
                s_mik = st.number_input("Gelen Miktar", min_value=0.001, format="%.3f")
                if st.button("Depoya Ekle"):
                    st.session_state.data["hammadde_depo"][s_m]["miktar"] += s_mik
                    verileri_kaydet(st.session_state.data); st.rerun()
    with m_tab:
        st.dataframe(pd.DataFrame(st.session_state.data.get("mamul_depo", [])), use_container_width=True)

elif menu == "📊 ARŞİV":
    st.header("📊 Arşiv")
    st.dataframe(pd.DataFrame(st.session_state.data.get("tamamlanan_siparisler", [])), use_container_width=True)
