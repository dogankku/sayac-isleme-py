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
    """
    Hiçbir kütüphanenin tanıyamadığı o inatçı XLS dosyalarını okumak için 
    tüm teknikleri (Encoding, XML, HTML, TSV) sırayla dener.
    """
    # 1. Deneme: Standart Excel
    try:
        file.seek(0)
        return pd.read_excel(file)
    except: pass

    # 2. Deneme: UTF-16 veya UTF-8 Metin (Tab ayrılmış - Çok Yaygındır)
    for enc in ['utf-16', 'utf-8-sig', 'cp1254', 'utf-8', 'iso-8859-9']:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep='\t', encoding=enc, engine='python')
            if len(df.columns) > 2: return df
        except: continue

    # 3. Deneme: HTML Tablosu (Farklı encodingler ile)
    for enc in ['cp1254', 'utf-8', 'iso-8859-9']:
        try:
            file.seek(0)
            df_list = pd.read_html(file, encoding=enc)
            if df_list: return df_list[0]
        except: continue

    # 4. Deneme: Noktalı Virgüllü CSV (Türkçe Excel ayarları)
    for enc in ['cp1254', 'utf-8']:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding=enc, engine='python')
            if len(df.columns) > 2: return df
        except: continue

    raise ValueError("Sistem bu dosyanın iç yapısını çözemedi. Lütfen bu dosyayı bilgisayarınızda açıp 'Farklı Kaydet' diyerek 'Excel Çalışma Kitabı (.xlsx)' olarak kaydedip tekrar yükleyin.")

# --- UI BAŞLANGIÇ ---
ayarlar = ayarları_yukle()
st.set_page_config(page_title="Site Sayaç Otomasyonu v4", layout="wide")
st.title("🏙️ Site Sayaç Yönetim Sistemi (Ultimate)")

with st.sidebar:
    st.header("🔐 Yönetici")
    girilen_sifre = st.text_input("Şifre", type="password")

if girilen_sifre == ayarlar["sifre"]:
    tab1, tab2 = st.tabs(["📊 Çoklu Veri İşleme", "⚙️ Değer Ayarları"])
    
    with tab2:
        st.subheader("Kod Ayarları")
        yeni_set = ayarlar["set_degerleri"].copy()
        c1, c2, c3 = st.columns(3)
        yeni_set["Genel"]["Isıtma"] = c1.number_input("Isıtma Kod", value=ayarlar["set_degerleri"]["Genel"]["Isıtma"])
        yeni_set["Genel"]["Soğutma"] = c2.number_input("Soğutma Kod", value=ayarlar["set_degerleri"]["Genel"]["Soğutma"])
        yeni_set["Genel"]["Kul. Su"] = c3.number_input("Kul. Su Kod", value=ayarlar["set_degerleri"]["Genel"]["Kul. Su"])
        if st.button("Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            ayarları_kaydet(ayarlar)
            st.success("Kaydedildi!")

    with tab1:
        st.subheader("📥 Dosya Yükleme")
        uploaded_files = st.file_uploader("XLS dosyalarını seçin", type=['xlsx', 'xls', 'csv'], accept_multiple_files=True)

        if uploaded_files:
            all_data = []
            for file in uploaded_files:
                try:
                    temp_df = excel_oku_ultimate(file)
                    # Sütun isimlerini düzelt
                    temp_df.columns = [str(c).strip() for c in temp_df.columns]
                    # Boş satırları temizle
                    temp_df.dropna(how='all', inplace=True)
                    # Değer sütununu bulmaya çalış (Eğer 'Değer' yoksa 3. sütunu al)
                    if 'Değer' not in temp_df.columns:
                        temp_df.rename(columns={temp_df.columns[2]: 'Değer'}, inplace=True)
                    # En sağdaki sütun Endeks
                    temp_df.rename(columns={temp_df.columns[-1]: 'Endeks_Degeri'}, inplace=True)
                    
                    all_data.append(temp_df)
                    st.write(f"✅ {file.name} (Satır: {len(temp_df)})")
                except Exception as e:
                    st.error(f"❌ {file.name} : {e}")

            if all_data:
                df_combined = pd.concat(
