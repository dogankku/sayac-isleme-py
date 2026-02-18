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

def excel_oku_guvenli(file):
    """Excel format hatalarını önlemek için farklı motorları dener."""
    try:
        # Modern Excel (.xlsx) denemesi
        return pd.read_excel(file, engine='openpyxl')
    except:
        try:
            # Eski Excel (.xls) denemesi
            return pd.read_excel(file, engine='xlrd')
        except:
            # CSV veya diğer formatlar için fallback
            return pd.read_csv(file, sep=None, engine='python')

# Uygulama Başlatma
ayarlar = ayarları_yukle()

st.set_page_config(page_title="Site Sayaç Otomasyonu v2", layout="wide")
st.title("🏙️ 55 Katlı Site Sayaç Yönetim Sistemi")

# --- ŞİFRE PANELİ ---
with st.sidebar:
    st.header("🔐 Yönetici Girişi")
    girilen_sifre = st.text_input("Sistem Şifresi", type="password")

if girilen_sifre == ayarlar["sifre"]:
    st.success("Yönetici Erişimi Aktif")
    
    tab1, tab2 = st.tabs(["📊 Çoklu Veri İşleme", "⚙️ Değer Ayarları"])
    
    with tab2:
        st.subheader("Sistem Eşleştirme Kodları")
        st.info("Sistemden gelen 'Değer' sütunundaki rakamların ne anlama geldiğini buradan güncelleyebilirsiniz.")
        
        yeni_set = ayarlar["set_degerleri"].copy()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            yeni_set["Genel"]["Isıtma"] = st.number_input("Isıtma Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Isıtma"])
        with col2:
            yeni_set["Genel"]["Soğutma"] = st.number_input("Soğutma Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Soğutma"])
        with col3:
            yeni_set["Genel"]["Kul. Su"] = st.number_input("Kullanım Suyu Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Kul. Su"])
            
        st.divider()
        yeni_sifre = st.text_input("Yeni Yönetici Şifresi (Değiştirmek istemiyorsanız boş bırakın)", type="password")

        if st.button("Tüm Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            if yeni_sifre:
                ayarlar["sifre"] = yeni_sifre
            ayarları_kaydet(ayarlar)
            st.success("Ayarlar kalıcı olarak kaydedildi!")

    with tab1:
        st.subheader("📥 Çoklu Dosya Yükleme")
        # --- ÇOKLU DOSYA YÜKLEME ---
        uploaded_files = st.file_uploader(
            "Sistemden aldığınız 4 dosyayı aynı anda seçin veya sürükleyin", 
            type=['xlsx', 'xls', 'csv'], 
            accept_multiple_files=True
        )

        if uploaded_files:
            all_data = []
            st.write(f"📁 {len(uploaded_files)} dosya yüklendi.")
            
            for file in uploaded_files:
                try:
                    temp_df = excel_oku_guvenli(file)
                    # Sütun isimlerini temizle
                    temp_df.columns = [str(c).strip() for c in temp_df.columns]
                    # En sağdaki endeks sütununu adlandır
                    temp_df.rename(columns={temp_df.columns[-1]: 'Endeks_Degeri'}, inplace=True)
                    all_data.append(temp_df)
                except Exception as e:
                    st.error(f"{file.name} okunurken hata oluştu: {e}")

            if all_data:
                # Tüm dosyaları tek bir tabloda birleştir
                df_combined = pd.concat(all_data, ignore_index=True)
                st.write("✅ Tüm dosyalar birleştirildi. Toplam Satır:", len(df_combined))
                st.dataframe(df_combined.head(5))

                if st.button("🚀 2026 Formatında Ayrıştır ve Hazırla"):
                    # Ayarlardaki kodlara göre filtreleme
                    i_kod = ayarlar["set_degerleri"]["Genel"]["Isıtma"]
                    s_kod = ayarlar["set_degerleri"]["Genel"]["Soğutma"]
                    k_kod = ayarlar["set_degerleri"]["Genel"]["Kul. Su"]

                    # Filtreleme (Değer sütununa göre)
                    # Not: Sütun adınızın 'Değer' olduğundan emin olun (Resimdeki gibi)
                    df_isitma = df_combined[df_combined['Değer'] == i_kod]
                    df_sogutma = df_combined[df_combined['Değer'] == s_kod]
                    df_su = df_combined[df_combined['Değer'] == k_kod]

                    # Excel indirme fonksiyonu
                    def to_excel(df_to_save):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_to_save.to_excel(writer, index=False, sheet_name='Veri')
                        return output.getvalue()

                    st.divider()
                    st.subheader("📥 Hazırlanan Dosyaları İndir")
                    
                    c1, c2, c3 = st.columns(3)
                    
                    if not df_isitma.empty:
                        c1.download_button("🔥 Isıtma Listesi", to_excel(df_isitma), "Isitma_Son_2026.xlsx")
                        c1.info(f"{len(df_isitma)} Sayaç")
                    
                    if not df_sogutma.empty:
                        c2.download_button("❄️ Soğutma Listesi", to_excel(df_sogutma), "Sogutma_Son_2026.xlsx")
                        c2.info(f"{len(df_sogutma)} Sayaç")
                        
                    if not df_su.empty:
                        c3.download_button("💧 Kullanım Suyu Listesi", to_excel(df_su), "Kullanim_Suyu_Son_2026.xlsx")
                        c3.info(f"{len(df_su)} Sayaç")
                    
                    st.balloons()

else:
    st.warning("🔐 Lütfen işlem yapmak için geçerli yönetici şifresini giriniz.")
