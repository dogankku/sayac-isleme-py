import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sayaç Veri İşleme Merkezi", layout="wide")

# --- KURALLAR TABLOSU (GÖRÜNTÜLEME İÇİN) ---
# Senin belirttiğin kuralları burada bir veri seti olarak tanımlıyoruz
kurallar_data = [
    {"Marka": "Danfos (3...)", "Hizmet": "Isıtma/Soğutma", "Eski Değer": 0, "Yeni Değer": 0, "Açıklama": "Değişiklik yok"},
    {"Marka": "Minol (1...)",  "Hizmet": "Isıtma",         "Eski Değer": 4, "Yeni Değer": 0, "Açıklama": "4 değeri 0 yapılır"},
    {"Marka": "Minol (1...)",  "Hizmet": "Soğutma",        "Eski Değer": 8, "Yeni Değer": 0, "Açıklama": "8 değeri 0 yapılır"},
    {"Marka": "Minol (1...)",  "Hizmet": "Kullanım Suyu",  "Eski Değer": 0, "Yeni Değer": 2, "Açıklama": "0 değeri 2 yapılır"},
    {"Marka": "Minol (1...)",  "Hizmet": "Kullanım Suyu",  "Eski Değer": 1, "Yeni Değer": 23,"Açıklama": "1 değeri 23 yapılır"},
    {"Marka": "Danfos Yeni (4...)", "Hizmet": "Genel",     "Eski Değer": 0, "Yeni Değer": 23,"Açıklama": "0 değeri 23 yapılır"},
]
df_kurallar = pd.DataFrame(kurallar_data)

# --- BAŞLIK VE TABLO GÖSTERİMİ ---
st.title("📊 Sayaç Otomasyon Sistemi")
st.info("Aşağıdaki kurallar, yüklenen dosyalara otomatik olarak uygulanacaktır:")
st.table(df_kurallar)

# --- DOSYA YÜKLEME ---
uploaded_files = st.file_uploader("Excel Dosyalarını Yükleyin (Çoklu seçim yapabilirsiniz)", 
                                  accept_multiple_files=True, type=['xlsx'])

if uploaded_files:
    tum_veriler = []
    
    for file in uploaded_files:
        # Exceli oku
        df = pd.read_excel(file)
        
        # Sütun İsimlerini Kontrol Et (Hata önleme)
        # 1. Sütunun Hizmet Tipi, 'İkincil Adres'in Sayaç No, 'Değer'in okuma olduğunu varsayıyoruz.
        # İlk sütunun ismini standartlaştıralım:
        first_col_name = df.columns[0]
        df.rename(columns={first_col_name: 'Hizmet_Tipi'}, inplace=True)
        
        # Eğer sütun isimleri farklı gelirse diye standartlaştırma (Gerekirse burayı senin dosyana göre düzeltiriz)
        # Kodun çalışması için dosyamızda 'İkincil Adres' ve 'Değer' sütunları olmalı.
        
        tum_veriler.append(df)

    if tum_veriler:
        # Tüm dosyaları alt alta birleştir
        main_df = pd.concat(tum_veriler, ignore_index=True)
        
        # --- ANA MANTIK VE DÖNÜŞTÜRME ---
        def kurallari_uygula(row):
            # İkincil Adres'i string'e çevirip ilk hanesine bak
            ikincil_adres = str(row.get('İkincil Adres', '')) # Sütun adı 'İkincil Adres' olmalı
            hizmet = str(row.get('Hizmet_Tipi', '')).lower()
            deger = row.get('Değer', 0) # Sütun adı 'Değer' olmalı

            # 1. MARKA BELİRLEME
            marka = "Bilinmiyor"
            if ikincil_adres.startswith('3'):
                marka = "Danfos"
            elif ikincil_adres.startswith('1'):
                marka = "Minol"
            elif ikincil_adres.startswith('4'):
                marka = "Danfos Yeni"

            # 2. KURALLARI UYGULA
            yeni_deger = deger # Varsayılan olarak eski değer kalsın

            # --- MINOL KURALLARI ---
            if marka == "Minol":
                if "ısıtma" in hizmet and deger == 4:
                    yeni_deger = 0
                elif "soğutma" in hizmet and deger == 8:
                    yeni_deger = 0
                elif ("su" in hizmet or "sıcak" in hizmet) and deger == 0: # Kullanım suyu varyasyonları
                    yeni_deger = 2
                elif ("su" in hizmet or "sıcak" in hizmet) and deger == 1:
                    yeni_deger = 23
            
            # --- DANFOS YENİ KURALLARI ---
            elif marka == "Danfos Yeni":
                if deger == 0:
                    yeni_deger = 23
            
            # --- DANFOS (ESKİ) KURALLARI ---
            elif marka == "Danfos":
                # "Isıtma soğutma kısmında 0 değeri 0 kalacak" (Zaten varsayılan bu, dokunmuyoruz)
                pass

            return yeni_deger

        # İşlemi Başlat
        if 'İkincil Adres' in main_df.columns and 'Değer' in main_df.columns:
            main_df['Değer'] = main_df.apply(kurallari_uygula, axis=1)
            st.success("✅ Tüm kurallar başarıyla uygulandı!")
            
            # --- AYRIŞTIRMA VE İNDİRME ---
            def excel_indir(dataframe):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dataframe.to_excel(writer, index=False)
                return output.getvalue()

            col1, col2, col3 = st.columns(3)

            # 1. Isıtma Dosyası
            df_isitma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Isıtma", case=False, na=False)]
            col1.download_button("🔥 Isıtma Exceli", excel_indir(df_isitma), "Isitma_Duzenlenmis.xlsx")

            # 2. Soğutma Dosyası
            df_sogutma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Soğutma", case=False, na=False)]
            col2.download_button("❄️ Soğutma Exceli", excel_indir(df_sogutma), "Sogutma_Duzenlenmis.xlsx")

            # 3. Kullanım Suyu Dosyası
            # 'Su' kelimesi geçenleri al (Kullanım Suyu, Sıcak Su vb.)
            df_su = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Su", case=False, na=False)]
            col3.download_button("💧 Kullanım Suyu Exceli", excel_indir(df_su), "Kullanim_Suyu_Duzenlenmis.xlsx")
            
            # Önizleme (Opsiyonel)
            with st.expander("İşlenmiş Veriyi Önizle"):
                st.dataframe(main_df.head(20))

        else:
            st.error("Hata: Yüklenen dosyalarda 'İkincil Adres' veya 'Değer' sütunu bulunamadı. Lütfen sütun isimlerini kontrol edin.")
