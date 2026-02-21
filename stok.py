import streamlit as st
import json
import os
import datetime
import pandas as pd

# 1. DOSYA VE VERİ YÖNETİMİ
VERI_DOSYASI = "stok_verileri.json"

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"depo": {}, "urun_agaclari": {}, "uretim_gecmisi": []}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# Her sayfa yenilendiğinde veriyi dosyadan tekrar oku (Senkronizasyon için önemli)
st.session_state.data = verileri_yukle()

st.set_page_config(page_title="Akıllı Fabrika", layout="wide")

# 2. MENÜ
st.sidebar.title("🏭 Yönetim Paneli")
menu = st.sidebar.radio("İşlem:", ["⚙️ Ürün Ağacı", "📦 Depo", "🛠️ Üretim", "📊 Analiz"])

# --- BÖLÜM 1: ÜRÜN AĞACI ---
if menu == "⚙️ Ürün Ağacı":
    st.header("⚙️ Ürün Reçeteleri")
    t1, t2 = st.tabs(["➕ Ekle", "✏️ Yönet"])
    
    with t1:
        with st.form("yeni_bom"):
            c1, c2 = st.columns(2)
            u_ad = c1.text_input("Ürün Adı")
            m_ad = c2.text_input("Malzeme Adı")
            c3, c4 = st.columns(2)
            birim = c3.selectbox("Birim", ["Adet", "mm", "cm", "Metre", "Gram", "Kg"])
            mik = c4.number_input("Miktar", min_value=0.001, format="%.3f")
            if st.form_submit_button("Kaydet"):
                if u_ad and m_ad:
                    if u_ad not in st.session_state.data["urun_agaclari"]:
                        st.session_state.data["urun_agaclari"][u_ad] = {}
                    st.session_state.data["urun_agaclari"][u_ad][m_ad] = {"miktar": mik, "birim": birim}
                    if m_ad not in st.session_state.data["depo"]:
                        # Ana depo birimini belirle
                        depo_birimi = "Metre" if birim in ["mm", "cm", "Metre"] else ("Kg" if birim in ["Gram", "Kg"] else "Adet")
                        st.session_state.data["depo"][m_ad] = {"miktar": 0.0, "birim": depo_birimi}
                    verileri_kaydet(st.session_state.data)
                    st.success("Reçete kaydedildi!")
                    st.rerun()

    with t2:
        if not st.session_state.data["urun_agaclari"]:
            st.info("Reçete bulunamadı.")
        else:
            u_sec = st.selectbox("Düzenle:", list(st.session_state.data["urun_agaclari"].keys()))
            if u_sec:
                temp_recete = {}
                for m, d in st.session_state.data["urun_agaclari"][u_sec].items():
                    c1, c2, c3, c4 = st.columns([2,1,1,1])
                    c1.write(f"**{m}**")
                    nm = c2.number_input("Mik", value=float(d["miktar"]), key=f"m_{u_sec}_{m}")
                    nb = c3.selectbox("Bir", ["Adet", "mm", "cm", "Metre", "Gram", "Kg"], index=["Adet", "mm", "cm", "Metre", "Gram", "Kg"].index(d["birim"]), key=f"b_{u_sec}_{m}")
                    if c4.button("🗑️", key=f"d_{u_sec}_{m}"):
                        del st.session_state.data["urun_agaclari"][u_sec][m]
                        if not st.session_state.data["urun_agaclari"][u_sec]: del st.session_state.data["urun_agaclari"][u_sec]
                        verileri_kaydet(st.session_state.data); st.rerun()
                    temp_recete[m] = {"miktar": nm, "birim": nb}
                
                if st.button("💾 Değişiklikleri Kaydet", use_container_width=True):
                    st.session_state.data["urun_agaclari"][u_sec] = temp_recete
                    verileri_kaydet(st.session_state.data); st.success("Güncellendi!"); st.rerun()

# --- BÖLÜM 2: DEPO ---
elif menu == "📦 Depo":
    st.header("📦 Stok Durumu")
    ara = st.text_input("🔍 Ara...")
    # Filtreli listeyi oluştur
    liste = [{"Malzeme": k, "Miktar": v["miktar"], "Birim": v["birim"]} for k, v in st.session_state.data["depo"].items() if ara.lower() in k.lower()]
    st.table(liste if ara else [])
    
    with st.expander("📥 Stok Ekle"):
        if st.session_state.data["depo"]:
            sm = st.selectbox("Malzeme", list(st.session_state.data["depo"].keys()))
            st.info(f"Birim: {st.session_state.data['depo'][sm]['birim']}")
            gm = st.number_input("Miktar", min_value=0.0)
            if st.button("Ekle"):
                st.session_state.data["depo"][sm]["miktar"] += gm
                verileri_kaydet(st.session_state.data); st.rerun()

# --- BÖLÜM 3: ÜRETİM ---
elif menu == "🛠️ Üretim":
    st.header("🛠️ Üretim İşlemi")
    reçeteler = list(st.session_state.data["urun_agaclari"].keys())
    
    if not reçeteler:
        st.warning("Üretim için önce 'Ürün Ağacı' tanımlamalısınız!")
    else:
        sec_u = st.selectbox("Üretilecek Ürün", reçeteler)
        adet = st.number_input("Adet", min_value=1)
        st.write("---")
        yeterli = True
        dus_list = {}
        
        for m, d in st.session_state.data["urun_agaclari"][sec_u].items():
            lazim = d["miktar"] * adet
            depo_v = st.session_state.data["depo"][m]
            
            # Dönüşüm
            m_dus = lazim
            if d["birim"] in ["mm", "Gram"] and depo_v["birim"] in ["Metre", "Kg"]: m_dus = lazim / 1000
            elif d["birim"] == "cm" and depo_v["birim"] == "Metre"]: m_dus = lazim / 100
            
            dus_list[m] = m_dus
            ok = depo_v["miktar"] >= m_dus
            if not ok: yeterli = False
            st.write(f"{'✅' if ok else '❌'} {m}: {lazim} {d['birim']} ({m_dus:.4f} {depo_v['birim']})")
        
        if st.button("🚀 ÜRETİMİ YAP", use_container_width=True) and yeterli:
            for m, mik in dus_list.items():
                st.session_state.data["depo"][m]["miktar"] -= mik
            
            log = {"Tarih": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Ürün": sec_u, "Miktar": adet}
            st.session_state.data["uretim_gecmisi"].append(log)
            verileri_kaydet(st.session_state.data)
            st.balloons(); st.success("Üretim Tamam!"); st.rerun()

# --- BÖLÜM 4: ANALİZ ---
elif menu == "📊 Analiz":
    st.header("📊 Üretim Analizi")
    df = pd.DataFrame(st.session_state.data["uretim_gecmisi"])
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.groupby("Ürün")["Miktar"].sum())
        if st.button("Geçmişi Sil"):
            st.session_state.data["uretim_gecmisi"] = []
            verileri_kaydet(st.session_state.data); st.rerun()
    else:
        st.info("Kayıt yok.")
