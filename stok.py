import streamlit as st
import json
import os
import datetime
import pandas as pd

# 1. VERİ YÖNETİMİ VE DOSYA İŞLEMLERİ
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "depo": {},
        "urun_agaclari": {},
        "uretim_gecmisi": []
    }

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = verileri_yukle()

st.set_page_config(page_title="Akıllı Fabrika Yönetim Sistemi", layout="wide")

# 2. SOL MENÜ NAVİGASYONU
st.sidebar.title("🏭 Fabrika Yönetim Merkezi")
menu = st.sidebar.radio("İşlem Seçiniz:", 
    ["⚙️ Ürün Ağacı Yönetimi", "📦 Depo & Stok Girişi", "🛠️ Üretim Merkezi", "📊 Üretim Analizi"])

# --- BÖLÜM 1: ÜRÜN AĞACI (BOM) YÖNETİMİ ---
if menu == "⚙️ Ürün Ağacı Yönetimi":
    st.header("⚙️ Ürün Reçetesi (BOM) Yönetimi")
    tab1, tab2 = st.tabs(["➕ Yeni Malzeme Ekle", "✏️ Mevcut Reçeteleri Yönet"])
    
    with tab1:
        st.subheader("Reçeteye Yeni Parça Ekle")
        with st.form("bom_form"):
            c1, c2 = st.columns(2)
            y_urun = c1.text_input("Ana Ürün Adı (Örn: Masa)")
            y_malz = c2.text_input("Gereken Malzeme (Örn: Vida)")
            c3, c4 = st.columns(2)
            y_birim = c3.selectbox("Kullanılacak Birim", ["Adet", "mm", "cm", "Metre", "Gram", "Kg"])
            y_mik = c4.number_input("1 Ürün İçin Miktar", min_value=0.001, format="%.3f")
            
            if st.form_submit_button("Reçeteye Ekle"):
                if y_urun and y_malz:
                    if y_urun not in st.session_state.data["urun_agaclari"]:
                        st.session_state.data["urun_agaclari"][y_urun] = {}
                    st.session_state.data["urun_agaclari"][y_urun][y_malz] = {"miktar": y_mik, "birim": y_birim}
                    
                    # Malzeme depoda yoksa otomatik tanımla
                    if y_malz not in st.session_state.data["depo"]:
                        ana_b = "Metre" if y_birim in ["mm", "cm", "Metre"] else ("Kg" if y_birim in ["Gram", "Kg"] else "Adet")
                        st.session_state.data["depo"][y_malz] = {"miktar": 0.0, "birim": ana_b}
                    
                    verileri_kaydet(st.session_state.data)
                    st.success(f"✅ {y_urun} reçetesi güncellendi.")
                    st.rerun()

    with tab2:
        st.subheader("Kayıtlı Reçeteleri Düzenle veya Sil")
        if not st.session_state.data["urun_agaclari"]:
            st.info("Henüz kayıtlı bir ürün reçetesi bulunmuyor.")
        else:
            u_sec = st.selectbox("Düzenlenecek Ürünü Seçin", list(st.session_state.data["urun_agaclari"].keys()))
            if u_sec:
                malzemeler = st.session_state.data["urun_agaclari"][u_sec]
                guncel_recete = {}
                
                for m, d in malzemeler.items():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{m}**")
                    n_mik = col2.number_input("Miktar", value=float(d["miktar"]), key=f"e_m_{u_sec}_{m}", format="%.3f")
                    birimler = ["Adet", "mm", "cm", "Metre", "Gram", "Kg"]
                    n_bir = col3.selectbox("Birim", birimler, index=birimler.index(d["birim"]), key=f"e_b_{u_sec}_{m}")
                    
                    if col4.button("🗑️ Sil", key=f"del_{u_sec}_{m}"):
                        del st.session_state.data["urun_agaclari"][u_sec][m]
                        if not st.session_state.data["urun_agaclari"][u_sec]:
                            del st.session_state.data["urun_agaclari"][u_sec]
                        verileri_kaydet(st.session_state.data)
                        st.rerun()
                    guncel_recete[m] = {"miktar": n_mik, "birim": n_bir}
                
                st.divider()
                b1, b2 = st.columns(2)
                if b1.button("💾 Değişiklikleri Uygula ve Kaydet", use_container_width=True):
                    st.session_state.data["urun_agaclari"][u_sec] = guncel_recete
                    verileri_kaydet(st.session_state.data)
                    st.success("Değişiklikler kaydedildi!")
                    st.rerun()
                if b2.button(f"🚨 {u_sec} Ürününü Tamamen Sil", use_container_width=True):
                    del st.session_state.data["urun_agaclari"][u_sec]
                    verileri_kaydet(st.session_state.data)
                    st.rerun()

# --- BÖLÜM 2: DEPO VE STOK GİRİŞİ ---
elif menu == "📦 Depo & Stok Girişi":
    st.header("📦 Depo Stok Yönetimi")
    ara = st.text_input("🔍 Stokta Malzeme Ara (Yazdığınızda tablo filtrelenir)", key="depo_arama")
    
    # Filtreleme mantığı
    liste_verisi = []
    for k, v in st.session_state.data["depo"].items():
        if ara.lower() in k.lower():
            liste_verisi.append({"Malzeme": k, "Mevcut Miktar": v["miktar"], "Birim": v["birim"]})
    
    if ara:
        st.table(liste_verisi)
    else:
        st.info("Tüm listeyi görmek için arama kutusuna bir şey yazabilir veya aşağıdan stok ekleyebilirsiniz.")
        with st.expander("Tüm Depo Listesini Göster"):
            st.dataframe(pd.DataFrame(liste_verisi), use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("📥 Yeni Stok Girişi Yap"):
        if st.session_state.data["depo"]:
            s_m = st.selectbox("Malzeme Seç", list(st.session_state.data["depo"].keys()), key="stok_giris_sec")
            b_bilgi = st.session_state.data["depo"][s_m]["birim"]
            st.info(f"Seçilen malzemenin depo birimi: {b_bilgi}")
            g_m = st.number_input(f"Gelen Miktar ({b_bilgi})", min_value=0.0, format="%.3f", key="stok_giris_mik")
            if st.button("Stoğu Güncelle", use_container_width=True):
                st.session_state.data["depo"][s_m]["miktar"] += g_m
                verileri_kaydet(st.session_state.data)
                st.success(f"{s_m} stoğu güncellendi.")
                st.rerun()
        else:
            st.warning("Önce Ürün Ağacı kısmından malzeme tanımlamalısınız.")

# --- BÖLÜM 3: ÜRETİM MERKEZİ ---
elif menu == "🛠️ Üretim Merkezi":
    st.header("🛠️ Üretim Planlama ve Gerçekleştirme")
    u_list = list(st.session_state.data["urun_agaclari"].keys())
    
    if u_list:
        sec_u = st.selectbox("Üretilecek Ürünü Seçin", u_list)
        u_adet = st.number_input("Kaç Adet Üretilecek?", min_value=1)
        recete = st.session_state.data["urun_agaclari"][sec_u]
        
        yeterli = True
        dusulecek_liste = {}
        
        st.subheader("Stok Kontrolü")
        for m, d in recete.items():
            lazim = d["miktar"] * u_adet
            d_verisi = st.session_state.data["depo"][m]
            
            # Birim Dönüşüm Mantığı
            mik_dus = lazim
            if d["birim"] == "mm" and d_verisi["birim"] == "Metre": mik_dus = lazim / 1000
            elif d["birim"] == "cm" and d_verisi["birim"] == "Metre": mik_dus = lazim / 100
            elif d["birim"] == "Gram" and d_verisi["birim"] == "Kg": mik_dus = lazim / 1000
            
            dusulecek_liste[m] = mik_dus
            durum = "✅" if d_verisi["miktar"] >= mik_dus else "❌"
            if d_verisi["miktar"] < mik_dus: yeterli = False
            
            st.write(f"{durum} **{m}**: {lazim} {d['birim']} gerekiyor. (Depodan {mik_dus:.4f} {d_verisi['birim']} düşecek)")
        
        st.divider()
        if st.button("🚀 ÜRETİMİ BAŞLAT", use_container_width=True):
            if yeterli:
                for m, mik in dusulecek_liste.items():
                    st.session_state.data["depo"][m]["miktar"] -= mik
                
                # Geçmişe Kaydet
                log = {
                    "Tarih": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Ürün": sec_u,
                    "Miktar": u_adet
                }
                if "uretim_gecmisi" not in st.session_state.data:
                    st.session_state.data["uretim_gecmisi"] = []
                st.session_state.data["uretim_gecmisi"].append(log)
                
                verileri_kaydet(st.session_state.data)
                st.success(f"Başarıyla {u_adet} adet {sec_u} üretildi!")
                st.balloons()
                st.rerun()
            else:
                st.error("Stok yetersiz! Lütfen eksik malzemeleri tamamlayın.")
    else:
        st.warning("Üretim yapabilmek için önce Ürün Ağacı tanımlayın.")

# --- BÖLÜM 4: ÜRETİM ANALİZİ VE TARİH FİLTRESİ ---
elif menu == "📊 Üretim Analizi":
    st.header("📊 Üretim Geçmişi ve Analiz")
    gecmis = st.session_state.data.get("uretim_gecmisi", [])
    
    if gecmis:
        df = pd.DataFrame(gecmis)
        df['Tarih_Dt'] = pd.to_datetime(df['Tarih']).dt.date
        
        st.subheader("🔍 Tarih Aralığı Seçin")
        col_f1, col_f2 = st.columns(2)
        bas_tarih = col_f1.date_input("Başlangıç", df['Tarih_Dt'].min())
        bit_tarih = col_f2.date_input("Bitiş", df['Tarih_Dt'].max())
        
        # Filtreleme
        df_filtreli = df[(df['Tarih_Dt'] >= bas_tarih) & (df['Tarih_Dt'] <= bit_tarih)]
        
        if not df_filtreli.empty:
            c1, c2 = st.columns(2)
            c1.metric("Toplam Üretim İşlemi", len(df_filtreli))
            c2.metric("Toplam Üretilen Adet", int(df_filtreli['Miktar'].sum()))
            
            st.dataframe(df_filtreli.drop(columns=['Tarih_Dt']).sort_index(ascending=False), use_container_width=True, hide_index=True)
            
            st.subheader("📈 Ürün Bazlı Toplam Üretim")
            grafik_verisi = df_filtreli.groupby("Ürün")["Miktar"].sum()
            st.bar_chart(grafik_verisi)
        else:
            st.warning("Bu tarih aralığında veri bulunamadı.")
            
        st.divider()
        if st.button("🔴 Üretim Geçmişini Temizle"):
            st.session_state.data["uretim_gecmisi"] = []
            verileri_kaydet(st.session_state.data)
            st.rerun()
    else:
        st.info("Henüz bir üretim kaydı yapılmamış.")