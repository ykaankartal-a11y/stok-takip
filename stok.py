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
        return f"{float(deger):.3f}" # Hassas tartım için 3 hane
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

# --- GELİŞMİŞ MALİYET HESAPLAYICI ---
def siparis_maliyet_ozeti(siparis):
    urun = siparis['urun']
    sip_miktar = siparis['miktar']
    recete = st.session_state.data["urun_agaclari"].get(urun, {})
    
    toplam_hammadde_maliyeti = 0
    analiz_listesi = []
    tamam_mi = True
    
    for malz, detay in recete.items():
        birim_gereksinim = detay["miktar"] # Örn: 0.1 kg
        toplam_gereksinim = birim_gereksinim * sip_miktar # Örn: 0.1 * 100 = 10 kg
        
        depo_verisi = st.session_state.data["hammadde_depo"].get(malz, {"miktar": 0.0, "fiyat": 0.0, "birim": "Birim Yok"})
        mevcut_stok = depo_verisi["miktar"]
        kg_birim_fiyat = depo_verisi.get("fiyat", 0.0) # Senin girdiğin KG fiyatı
        
        # Maliyet Hesabı: (Ürün başı miktar * Toplam Sipariş) * Hammadde Birim Fiyatı
        satir_maliyeti = toplam_gereksinim * kg_birim_fiyat
        toplam_hammadde_maliyeti += satir_maliyeti
        
        eksik = max(0, toplam_gereksinim - mevcut_stok)
        if eksik > 0: tamam_mi = False
        
        analiz_listesi.append({
            "MALZEME": malz,
            "GEREKEN": format_sayi(toplam_gereksinim, detay['birim']),
            "MEVCUT": format_sayi(mevcut_stok, detay['birim']),
            "BİRİM FİYAT": f"{kg_birim_fiyat:.2f} ₺",
            "SATIR MALİYETİ": f"{satir_maliyeti:.2f} ₺"
        })
    
    toplam_gider = toplam_hammadde_maliyeti + siparis.get('iscilik', 0)
    satis_fiyatı = siparis.get('satis_fiyati', 0)
    kar = satis_fiyatı - toplam_gider
    kar_orani = (kar / satis_fiyatı * 100) if satis_fiyatı > 0 else 0
    
    return {
        "tamam_mi": tamam_mi,
        "analiz": analiz_listesi,
        "hammadde_maliyeti": toplam_hammadde_maliyeti,
        "toplam_gider": toplam_gider,
        "kar": kar,
        "kar_orani": kar_orani
    }

# --- POP-UP PENCERELER ---
@st.dialog("➕ YENİ SİPARİŞ GİRİŞİ")
def yeni_siparis_penceresi():
    otomatik_kod = f"SIP-{1001 + len(st.session_state.data['siparisler']) + len(st.session_state.data['tamamlanan_siparisler'])}"
    st.write(f"Sipariş No: **{otomatik_kod}**")
    m_adi = st.text_input("Müşteri Adı").upper()
    u_list = list(st.session_state.data.get("urun_agaclari", {}).keys())
    sec_u = st.selectbox("Ürün Seçin", u_list if u_list else ["Reçete Tanımlayın"])
    
    c1, c2 = st.columns(2)
    mik = c1.number_input("Sipariş Adedi", min_value=1, value=1)
    term = c2.date_input("Teslim Tarihi")
    
    st.markdown("---")
    st.write("💰 **FİNANSAL GİRİŞ**")
    c3, c4 = st.columns(2)
    satis = c3.number_input("Toplam Satış Bedeli (₺)", min_value=0.0)
    iscilik = c4.number_input("Toplam İşçilik Maliyeti (₺)", min_value=0.0)
    
    if st.button("💾 SİPARİŞİ KAYDET", use_container_width=True, type="primary"):
        if m_adi and sec_u != "Reçete Tanımlayın":
            yeni = {
                "kod": otomatik_kod, "musteri": m_adi, "urun": sec_u, 
                "miktar": int(mik), "uretilen": 0, "termin": str(term), 
                "satis_fiyati": satis, "iscilik": iscilik, "not": ""
            }
            st.session_state.data["siparisler"].append(yeni)
            verileri_kaydet(st.session_state.data); st.rerun()

@st.dialog("🔍 ANALİZ VE MALİYET DETAYI")
def siparis_detay_penceresi(siparis):
    res = siparis_maliyet_ozeti(siparis)
    st.subheader(f"📊 {siparis['kod']} Kâr/Zarar Analizi")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Maliyet", f"{res['toplam_gider']:.2f} ₺")
    m2.metric("Beklenen Kâr", f"{res['kar']:.2f} ₺", delta=f"%{res['kar_orani']:.1f}")
    m3.metric("Satış Fiyatı", f"{siparis['satis_fiyati']:.2f} ₺")
    
    st.write("### 📋 Detaylı Hammadde Kırılımı")
    st.table(pd.DataFrame(res['analiz']))
    
    st.write(f"👷 **Sabit İşçilik Gideri:** {siparis.get('iscilik', 0):.2f} ₺")
    if res['tamam_mi']: st.success("✅ Stoklar yeterli.")
    else: st.error("❌ Eksik hammadde var!")

# --- ANA EKRANLAR ---
if menu == "🛒 SİPARİŞ TAKİBİ":
    c_bas, c_but = st.columns([4, 1])
    with c_bas: st.header("🛒 Aktif Üretim Emirleri")
    with c_but: 
        if st.button("➕ YENİ SİPARİŞ", type="primary", use_container_width=True): yeni_siparis_penceresi()
    
    st.markdown("---")
    
    for idx, s in enumerate(st.session_state.data["siparisler"]):
        res = siparis_maliyet_ozeti(s)
        durum_renk = "#2e7d32" if res['tamam_mi'] else "#c62828"
        bg_renk = "#f1f8e9" if res['tamam_mi'] else "#fff5f5"
        
        st.markdown(f"""
            <div style="background-color: {bg_renk}; border-left: 10px solid {durum_renk}; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: #333;">{s['kod']} | {s['musteri']}</span>
                    <span style="background-color: {durum_renk}; color: white; padding: 2px 10px; border-radius: 15px; font-size: 0.8rem;">
                        {'STOK UYGUN' if res['tamam_mi'] else 'STOK YETERSİZ'}
                    </span>
                </div>
                <div style="display: flex; gap: 30px; margin-top: 15px;">
                    <div><b>Ürün:</b> {s['urun']}</div>
                    <div><b>İlerleme:</b> {s['uretilen']} / {s['miktar']}</div>
                    <div><b>Kâr Tahmini:</b> {res['kar']:.2f} ₺</div>
                    <div><b>Termin:</b> {s['termin']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, _ = st.columns([1, 1, 1, 4])
        if c1.button("🔍 ANALİZ", key=f"an_{idx}"): siparis_detay_penceresi(s)
        if c2.button("🛠️ ÜRET", key=f"ur_{idx}"): st.info("Üretim menüsünü kullanın.")
        if c3.button("🏁 KAPAT", key=f"kp_{idx}"): 
            if st.button(f"Onayla: {s['kod']}", key=f"onay_{idx}"):
                s["bitis"] = str(datetime.date.today())
                st.session_state.data["tamamlanan_siparisler"].append(s)
                st.session_state.data["siparisler"].pop(idx)
                verileri_kaydet(st.session_state.data); st.rerun()

elif menu == "🛠️ ÜRETİM KAYDI":
    st.header("🛠️ Üretim Onayı")
    sips = st.session_state.data.get("siparisler", [])
    if sips:
        sec_etiket = st.selectbox("Sipariş Seçin:", [f"{s['kod']} - {s['musteri']}" for s in sips])
        sec_sip = next(s for s in sips if f"{s['kod']} - {s['musteri']}" == sec_etiket)
        
        with st.form("uretim_form"):
            u_mik = st.number_input("Üretilen Miktar", min_value=1, value=1)
            if st.form_submit_button("ÜRETİMİ KAYDET"):
                res = siparis_maliyet_ozeti(sec_sip)
                if not res['tamam_mi']: st.error("Stok yetersiz!")
                else:
                    recete = st.session_state.data["urun_agaclari"].get(sec_sip['urun'], {})
                    for m, d in recete.items():
                        st.session_state.data["hammadde_depo"][m]["miktar"] -= (d["miktar"] * u_mik)
                    sec_sip["uretilen"] += u_mik
                    st.session_state.data["mamul_depo"].append({"tarih": str(datetime.date.today()), "kod": sec_sip['kod'], "urun": sec_sip['urun'], "miktar": u_mik})
                    verileri_kaydet(st.session_state.data); st.balloons(); st.rerun()

elif menu == "⚙️ ÜRÜN REÇETELERİ":
    st.header("⚙️ Reçete Editörü")
    with st.expander("🆕 YENİ REÇETE TANIMLA"):
        ana_urun = st.text_input("Ana Ürün Adı").upper()
        if "rows" not in st.session_state: st.session_state.rows = 1
        for i in range(st.session_state.rows):
            c1, c2, c3 = st.columns([3, 2, 2])
            st.text_input(f"Hammadde {i+1}", key=f"h_ad_{i}").upper()
            st.number_input("Birim Kullanım Miktarı", key=f"h_mik_{i}", format="%.4f", step=0.0001)
            st.selectbox("Birim", ["ADET", "KG", "METRE", "LT"], key=f"h_birim_{i}")
        if st.button("➕ Satır Ekle"): st.session_state.rows += 1; st.rerun()
        if st.button("💾 REÇETEYİ KAYDET", type="primary"):
            yeni_recete = {}
            for i in range(st.session_state.rows):
                name = st.session_state[f"h_ad_{i}"].upper()
                if name:
                    yeni_recete[name] = {"miktar": st.session_state[f"h_mik_{i}"], "birim": st.session_state[f"h_birim_{i}"]}
                    if name not in st.session_state.data["hammadde_depo"]:
                        st.session_state.data["hammadde_depo"][name] = {"miktar": 0.0, "birim": st.session_state[f"h_birim_{i}"], "fiyat": 0.0}
            st.session_state.data["urun_agaclari"][ana_urun] = yeni_recete
            verileri_kaydet(st.session_state.data); st.session_state.rows = 1; st.rerun()

elif menu == "📦 DEPO DURUMU":
    st.header("📦 Depo ve Maliyet Yönetimi")
    h_tab, m_tab = st.tabs(["🏗️ Hammadde", "🏬 Mamul"])
    with h_tab:
        h_depo = st.session_state.data["hammadde_depo"]
        if h_depo:
            df_h = pd.DataFrame([{"MALZEME": k, "STOK": format_sayi(v['miktar'],v['birim']), "BİRİM": v['birim'], "BİRİM FİYAT": f"{v.get('fiyat',0):.2f} ₺"} for k, v in h_depo.items()])
            st.table(df_h)
            with st.expander("📥 Stok Girişi ve Fiyat Güncelle"):
                s_m = st.selectbox("Malzeme Seçin", list(h_depo.keys()))
                c1, c2 = st.columns(2)
                gelen = c1.number_input("Gelen Miktar", min_value=0.0, format="%.3f")
                yeni_fiyat = c2.number_input("Birim Alış Fiyatı (1 Birim Kaç ₺?)", min_value=0.0, help="Örn: 1 KG fiyatını girin.")
                if st.button("Depoya İşle"):
                    h_depo[s_m]["miktar"] += gelen
                    h_depo[s_m]["fiyat"] = yeni_fiyat
                    verileri_kaydet(st.session_state.data); st.rerun()
