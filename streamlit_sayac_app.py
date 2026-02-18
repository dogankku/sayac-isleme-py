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

def excel_oku_super_esnek(file):
    """
    Sistemden gelen 'sahte' XLS dosyalarını (HTML veya Metin tabanlı) 
    okumak için 4 farklı yöntemi sırayla dener.
    """
    # Yöntem 1: Standart Excel (xlsx/xls)
    try:
        return pd.read_excel(file)
    except Exception:
        pass
    
    # Dosya imlecini başa sar (önceki okuma denemesi imleci sona götürmüş olabilir)
    file.seek(0)
    
    # Yöntem 2: HTML Tablo formatı (Sistem exports genelde budur)
    try:
        df_list = pd.read_html(file)
        if df_list:
            return df_list[0]
    except Exception:
        pass

    file.seek(0)
    
    # Yöntem 3: Tabla ayrılmış (TSV) veya Noktalı Virgüllü (CSV) metin
    try:
        # Önce Tab (\t), sonra Noktalı Virgül (;), sonra Virgül (,) dene
        for ayrac in ['\t', ';', ',']:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=ayrac, engine='python')
                if len(df.columns) > 1: # Eğer tek sütun değilse doğru ayraç bulunmuştur
                    return df
            except:
                continue
    except Exception:
        pass
        
    raise ValueError("Dosya formatı tanınamadı. Lütfen dosyayı Excel'de açıp 'Farklı Kaydet -> Excel Çalışma Kitabı' yapmayı deneyin.")

# Uygulama Başlatma
ayarlar = ayarları_yukle()

st.set_page_config(page_title="Site Sayaç Otomasyonu v3", layout="wide")
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
        yeni_set = ayarlar["set_degerleri"].copy()
        col1, col2, col3 = st.columns(3)
        with col1: yeni_set["Genel"]["Isıtma"] = st.number_input("Isıtma Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Isıtma"])
        with col2: yeni_set["Genel"]["Soğutma"] = st.number_input("Soğutma Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Soğutma"])
        with col3: yeni_set["Genel"]["Kul. Su"] = st.number_input("Kullanım Suyu Kod Değeri", value=ayarlar["set_degerleri"]["Genel"]["Kul. Su"])
        if st.button("Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            ayarları_kaydet(ayarlar)
            st.success("Kaydedildi!")

    with tab1:
        st.subheader("📥 Çoklu Dosya Yükleme")
        uploaded_files = st.file_uploader("4 adet XLS dosyasını seçin", type=['xlsx', 'xls', 'csv'], accept_multiple_files=True)

        if uploaded_files:
            all_data = []
            for file in uploaded_files:
                try:
                    temp_df = excel_oku_super_esnek(file)
                    # Sütun isimlerini temizle (str ve strip)
                    temp_df.columns = [str(c).strip() for c in temp_df.columns]
                    # En sağdaki sütun değerdir
                    temp_df.rename(columns={temp_df.columns[-1]: 'Endeks_Degeri'}, inplace=True)
                    all_data.append(temp_df)
                    st.write(f"✅ {file.name} başarıyla yüklendi.")
                except Exception as e:
                    st.error(f"❌ {file.name} işlenemedi: {e}")

            if all_data:
                df_combined = pd.concat(all_data, ignore_index=True)
                st.write("📊 Toplam Veri Sayısı:", len(df_combined))
                st.dataframe(df_combined.head(3))

                if st.button("🚀 2026 Formatında Dosyaları Hazırla"):
                    i_kod = ayarlar["set_degerleri"]["Genel"]["Isıtma"]
                    s_kod = ayarlar["set_degerleri"]["Genel"]["Soğutma"]
                    k_kod = ayarlar["set_degerleri"]["Genel"]["Kul. Su"]

                    # Sütun isimlerinde 'Değer' sütununu bul (Resimde 'Değer' yazıyordu)
                    # Eğer sütun adı farklıysa (örn: 'Value') burayı ona göre eşleştiririz
                    target_col = 'Değer' if 'Değer' in df_combined.columns else df_combined.columns[2]

                    df_isitma = df_combined[df_combined[target_col].astype(str).str.contains(str(i_kod))]
                    df_sogutma = df_combined[df_combined[target_col].astype(str).str.contains(str(s_kod))]
                    df_su = df_combined[df_combined[target_col].astype(str).str.contains(str(k_kod))]

                    def to_excel(df_to_save):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_to_save.to_excel(writer, index=False)
                        return output.getvalue()

                    st.divider()
                    c1, c2, c3 = st.columns(3)
                    if not df_isitma.empty: c1.download_button("🔥 Isıtma", to_excel(df_isitma), "Isitma.xlsx")
                    if not df_sogutma.empty: c2.download_button("❄️ Soğutma", to_excel(df_sogutma), "Sogutma.xlsx")
                    if not df_su.empty: c3.download_button("💧 Kullanım Suyu", to_excel(df_su), "Su.xlsx")
                    st.balloons()
else:
    st.warning("🔐 Yönetici şifresi gerekli.")
