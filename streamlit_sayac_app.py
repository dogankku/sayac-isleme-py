import streamlit as st
import pandas as pd
import json
import os
import io

# --- AYARLARIN YÖNETİMİ ---
CONFIG_FILE = 'sayac_ayarlari.json'

def ayarları_yukle():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "sifre": "1234",
        "set_degerleri": {
            "Genel": {"Isıtma": 0, "Soğutma": 24, "Kul. Su": 23}
        }
    }

def ayarları_kaydet(ayarlar):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=4)

def excel_oku_ultimate(file):
    """Farklı formatlardaki (HTML, CSV, XLS) dosyaları okumayı dener."""
    # 1. Deneme: Standart Excel
    try:
        file.seek(0)
        return pd.read_excel(file)
    except: pass

    # 2. Deneme: UTF-16 Tab Ayrılmış (Sistemlerin en çok kullandığı format)
    for enc in ['utf-16', 'utf-8-sig', 'cp1254', 'iso-8859-9']:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep='\t', encoding=enc, engine='python')
            if len(df.columns) > 2: return df
        except: continue

    # 3. Deneme: HTML Tablosu
    try:
        file.seek(0)
        df_list = pd.read_html(file)
        if df_list: return df_list[0]
    except: pass

    raise ValueError("Dosya formatı çözülemedi. Lütfen Excel'de açıp .xlsx olarak kaydedin.")

# Uygulama Başlatma
ayarlar = ayarları_yukle()

st.set_page_config(page_title="Site Sayaç Otomasyonu v4", layout="wide")
st.title("🏙️ Site Sayaç Yönetim Sistemi")

# --- ŞİFRE PANELİ ---
with st.sidebar:
    st.header("🔐 Yönetici")
    girilen_sifre = st.text_input("Şifre", type="password")

if girilen_sifre == ayarlar["sifre"]:
    tab1, tab2 = st.tabs(["📊 Çoklu Veri İşleme", "⚙️ Ayarlar"])
    
    with tab2:
        st.subheader("Kod Ayarları")
        yeni_set = ayarlar["set_degerleri"].copy()
        c1, c2, c3 = st.columns(3)
        yeni_set["Genel"]["Isıtma"] = c1.number_input("Isıtma Kod", value=ayarlar["set_degerleri"]["Genel"]["Isıtma"])
        yeni_set["Genel"]["Soğutma"] = c2.number_input("Soğutma Kod", value=ayarlar["set_degerleri"]["Genel"]["Soğutma"])
        yeni_
