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
            try:
                return json.load(f)
            except:
                pass
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
    """Excel, HTML veya Metin tabanlı dosyaları okumayı dener."""
    try:
        file.seek(0)
        return pd.read_excel(file)
    except: pass

    for enc in ['utf-16', 'utf-16-sig', 'utf-8-sig', 'cp1254', 'iso-8859-9']:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep='\t', encoding=enc, engine='python')
            if len(df.columns) > 2: return df
        except: continue

    try:
        file.seek(0)
        df_list = pd.read_html(file)
        if df_list: return df_list[0]
    except: pass

    raise ValueError("Dosya formatı çözülemedi. Lütfen .xlsx olarak kaydedip yükleyin.")

# Uygulama Başlatma
ayarlar = ayarları_yukle()

st.set_page_config(page_title="Site Sayaç Otomasyonu v5", layout="wide")
st.title("🏙️ Site Sayaç Yönetim Sistemi")

# --- ŞİFRE PANELİ ---
with st.sidebar:
    st.header("🔐 Yönetici Girişi")
    girilen_sifre = st.text_input("Şifre", type="password")

if girilen_sifre == ayarlar["sifre"]:
    st.success("Yönetici Erişimi Aktif")
    tab1, tab2 = st.tabs(["📊 Çoklu Veri İşleme", "⚙️ Ayarlar"])
    
    with tab2:
        st.subheader("Kod Ayarları")
        # NameError'u önlemek için değişkeni burada tanımlıyoruz
        yeni_set = ayarlar["set_degerleri"].copy()
        
        c1, c2, c3 = st.columns(3)
        yeni_set["Genel"]["Isıtma"] = c1.number_input("Isıtma Kod", value=ayarlar["set_degerleri"]["Genel"]["Isıtma"])
        yeni_set["Genel"]["Soğutma"] = c2.number_input("Soğutma Kod", value=ayarlar["set_degerleri"]["Genel"]["Soğutma"])
        yeni_set["Genel"]["Kul. Su"] = c3.number_input("Kul. Su Kod", value=ayarlar["set_degerleri"]["Genel"]["Kul. Su"])
        
        yeni_sifre_girdisi = st.text_input("Yeni Şifre (Değiştirmek istemiyorsanız boş bırakın)", type="password")
        
        if st.button("Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            if yeni_sifre_girdisi:
                ayarlar["sifre"] = yeni_sifre_girdisi
            ayarları_kaydet(ayarlar)
            st.success("Ayarlar başarıyla kaydedildi!")

    with tab1:
        st.subheader("📥 Çoklu Dosya Yükleme")
        uploaded_files = st.file_uploader("XLS dosyalarını seçin", type=['xlsx', 'xls', 'csv'], accept_multiple_files=True)

        if uploaded_files:
            all_data = []
            for file in uploaded_files:
                try:
                    temp_df = excel_oku_ultimate(file)
                    temp_df.columns = [str(c).strip() for c in temp_df.columns]
                    temp_df.dropna(how='all', inplace=True)
                    
                    if 'Değer' not in temp_df.columns:
                        if len(temp_df.columns) >= 3:
                            temp_df.rename(columns={temp_df.columns[2]: 'Değer'}, inplace=True)
                    
                    temp_df.rename(columns={temp_df.columns[-1]: 'Endeks_Degeri'}, inplace=True)
                    all_data.append(temp_df)
                    st.write(f"✅ {file.name} yüklendi.")
                except Exception as e:
                    st.error(f"❌ {file.name} : {e}")

            if all_
