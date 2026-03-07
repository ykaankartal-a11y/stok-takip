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

def format_sayi(deger, birim="ADET"):
    try:
        if birim.upper() == "ADET": return f"{int(float(deger))}"
        return f"{float(deger):.3f}"
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

# --- MALİYET HESAPLAYICI ---
def siparis_maliyet_ozeti(siparis):
    urun = siparis['urun']
    sip_miktar = siparis['miktar']
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    toplam_hammadde_maliyeti = 0
    analiz_listesi = []
    tamam_mi = True
    
    for malz, detay in recete.items():
        birim_gereksinim = detay["miktar"]
        toplam_gereksinim = birim_gereksinim * sip_miktar
        depo_verisi = st.session_state.data["hammadde_depo"].get(malz, {"miktar": 0.0, "fiyat": 0.0, "birim": "ADET"})
        mevcut_stok = depo_verisi["miktar"]
        birim_fiyat = depo_verisi.get("fiyat", 0.0)
        
        satir_maliyeti = toplam_gereksinim * birim_fiyat
        toplam_hammadde_maliyeti += satir_maliyeti
        if toplam_gereksinim > mevcut_stok: tamam_mi = False
        
        analiz_listesi.append({
            "MALZEME": malz, "GEREKEN": format_sayi(toplam_gereksinim, detay['birim']),
            "MEVCUT": format_sayi(mevcut_stok, detay['birim']), "BİRİM FİYAT": f"{birim_fiyat:.2f} ₺",
            "TOPLAM": f"{satir_maliyeti:.2f} ₺"
        })
    
    toplam_gider = toplam_hammadde_maliyeti + siparis.get('iscilik', 0)
    kar = siparis.get('satis_fiyati', 0) - toplam_gider
    kar_orani = (kar / siparis.get('satis_fiyati', 1) * 100) if siparis.get('satis_fiyati', 0) > 0 else 0
    return {"tamam_mi": tamam_mi, "analiz": analiz_listesi, "kar": kar, "kar_orani": kar_orani, "toplam_gider": toplam_gider}

# --- DIALOG PENCERELERİ ---
@st.dialog("➕ YENİ SİPARİŞ")
def yeni_siparis_penceresi():
    kod = f"SIP-{1001 + len(st.session_state.data['siparisler']) + len(st.session_state.data['tamamlanan_siparisler'])}"
    st.subheader(f"No: {kod}")
    m_adi = st.text_input("Müşteri").upper()
    u_list = list(st.session_state.data["urun_agaclari"].keys())
    sec_u = st.selectbox("Ürün", u_list if u_list else ["Reçete Yok"])
    c1, c2 = st.columns(2)
    mik = c1.number_input("Adet", min_value=1, value=1)
    term = c2.date_input("Termin")
    c3, c4 = st.columns(2)
    satis = c3.number_input("Satış Fiyatı (₺)", min_value=0.0)
    iscilik = c4.number_input("İşçilik (₺)", min_value=0.0)
    if st.button("KAYDET", type="primary", use_container_width=True):
        st.session_state.data["siparisler"].append({
            "kod": kod, "musteri": m_adi, "urun": sec_u, "miktar": int(mik), 
            "uretilen": 0, "termin": str(term), "satis_fiyati": satis, "iscilik": iscilik, "not": ""
        })
        verileri_kaydet(st.session_state.data); st.rerun()

@st.dialog("🔍 ANALİZ")
def siparis_detay_penceresi(siparis):
    res = siparis_maliyet_ozeti(siparis)
    st.metric("Beklenen Net Kâr", f"{res['kar']:.2f} ₺", f"%{res['kar_orani']:.1f}")
    st.write("### Hammadde Detayları")
    st.table(pd.DataFrame(res['analiz']))
    st.info(f"İşçilik Gideri: {siparis['iscilik']:.2f} ₺")

@st.dialog("🏁 SİPARİŞİ KAPAT")
def siparis_kapat_penceresi(siparis, index):
    st.subheader(f"{siparis['kod']} Arşive Gönderiliyor")
    not_alani = st.text_area("Sipariş Notu (Örn: Zamanında teslim edildi)")
    if st.button("İŞLEMİ TAMAMLA", type="primary", use_container_width=True):
        siparis["bitis"] = str(datetime.date.today())
        siparis["not"] = not_alani if not_alani else "Not yok."
        st.session_state.data["tamamlanan_siparisler"].append(siparis)
        st.session_state.data["siparisler"].pop(index)
        verileri_kaydet(st.session_state.data); st.rerun()

# --- MENÜLER ---
if menu == "🛒 SİPARİŞ TAKİBİ":
    c1, c2 = st.columns([4,1])
    c1.header("🛒 Aktif Siparişler")
    if c2.button("➕ YENİ", type="primary", use_container_width=True): yeni_siparis_penceresi()
    
    for idx, s in enumerate(st.session_state.data["siparisler"]):
        res = siparis_maliyet_ozeti(s)
        renk = "#2e7d32" if res['tamam_mi'] else "#c62828"
        with st.container():
            st.markdown(f"""
                <div style="border-left: 8px solid {renk}; background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{s['kod']} | {s['musteri']}</b>
                        <span>📅 {s['termin']}</span>
                    </div>
                    <div style="font-size: 0.9rem; margin-top: 5px;">📦 {s['urun']} | 🎯 {s['uretilen']}/{s['miktar']} | 💰 Kâr: {res['kar']:.2f} ₺</div>
                </div>
            """, unsafe_allow_html=True)
            ca, cb, cc, _ = st.columns([1,1,1,4])
            if ca.button("🔍 ANALİZ", key=f"an_{idx}"): siparis_detay_penceresi(s)
            if cb.button("🛠️ ÜRET", key=f"ur_{idx}"): st.info("Üretim menüsüne geçin.")
            if cc.button("🏁 KAPAT", key=f"kp_{idx}"): siparis_kapat_penceresi(s, idx)
            st.divider()

elif menu == "🛠️ ÜRETİM KAYDI":
    st.header("🛠️ Üretim Onayı")
    sips = st.session_state.data["siparisler"]
    if sips:
        sec = st.selectbox("Sipariş:", [f"{s['kod']} - {s['musteri']}" for s in sips])
        sip = next(s for s in sips if f"{s['kod']} - {s['musteri']}" == sec)
        u_mik = st.number_input("Miktar", min_value=1, value=1)
        if st.button("ÜRETİMİ KAYDET", type="primary"):
            res = siparis_maliyet_ozeti(sip)
            if not res['tamam_mi']: st.error("Stok Yetersiz!")
            else:
                recete = st.session_state.data["urun_agaclari"][sip['urun']]
                for m, d in recete.items():
                    st.session_state.data["hammadde_depo"][m]["miktar"] -= (d["miktar"] * u_mik)
                sip["uretilen"] += u_mik
                st.session_state.data["mamul_depo"].append({"tarih": str(datetime.date.today()), "kod": sip['kod'], "urun": sip['urun'], "miktar": u_mik})
                verileri_kaydet(st.session_state.data); st.balloons(); st.rerun()

elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ Reçete Editörü")
    with st.expander("🆕 YENİ REÇETE"):
        ana = st.text_input("Ürün Adı").upper()
        if "rows" not in st.session_state: st.session_state.rows = 1
        for i in range(st.session_state.rows):
            c1, c2, c3 = st.columns([3,2,1])
            st.text_input(f"Hammadde {i+1}", key=f"h_ad_{i}").upper()
            st.number_input("Miktar", key=f"h_mik_{i}", format="%.4f")
            st.selectbox("Birim", ["ADET", "KG", "METRE"], key=f"h_birim_{i}")
        if st.button("➕ Satır"): st.session_state.rows += 1; st.rerun()
        if st.button("💾 KAYDET", type="primary"):
            recete = {}
            for i in range(st.session_state.rows):
                name = st.session_state[f"h_ad_{i}"].upper()
                if name:
                    recete[name] = {"miktar": st.session_state[f"h_mik_{i}"], "birim": st.session_state[f"h_birim_{i}"]}
                    if name not in st.session_state.data["hammadde_depo"]:
                        st.session_state.data["hammadde_depo"][name] = {"miktar": 0.0, "birim": st.session_state[f"h_birim_{i}"], "fiyat": 0.0}
            st.session_state.data["urun_agaclari"][ana] = recete
            verileri_kaydet(st.session_state.data); st.session_state.rows = 1; st.rerun()

elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo")
    h_tab, m_tab = st.tabs(["Hammadde", "Mamul"])
    with h_tab:
        h_depo = st.session_state.data["hammadde_depo"]
        if h_depo:
            st.table(pd.DataFrame([{"MALZEME": k, "STOK": format_sayi(v['miktar'],v['birim']), "FİYAT": f"{v.get('fiyat',0):.2f} ₺"} for k, v in h_depo.items()]))
            with st.expander("📥 Stok/Fiyat Girişi"):
                sel = st.selectbox("Malzeme", list(h_depo.keys()))
                gelen = st.number_input("Miktar", min_value=0.0)
                fiy = st.number_input("Birim Fiyat (₺)", min_value=0.0)
                if st.button("GÜNCELLE"):
                    h_depo[sel]["miktar"] += gelen
                    h_depo[sel]["fiyat"] = fiy
                    verileri_kaydet(st.session_state.data); st.rerun()
    with m_tab:
        if st.session_state.data["mamul_depo"]: st.dataframe(pd.DataFrame(st.session_state.data["mamul_depo"]), use_container_width=True)

elif menu == "📊 ARŞİV":
    st.header("📊 Tamamlananlar")
    if st.session_state.data["tamamlanan_siparisler"]:
        for idx, a in enumerate(st.session_state.data["tamamlanan_siparisler"]):
            with st.expander(f"📁 {a['kod']} - {a['musteri']}"):
                st.write(f"Ürün: {a['urun']} | Kâr: {a.get('satis_fiyati',0) - a.get('iscilik',0):.2f} ₺")
                st.info(f"Not: {a.get('not','')}")
