import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- ÖZEL DOSYA OKUYUCU (TÜRKÇE ve FORMAT DESTEKLİ) ---
def dosyayi_zorla_oku(file):
    # Dosya imlecini başa al
    file.seek(0)
    
    # 1. Yöntem: Gerçek Excel (XLSX - openpyxl)
    try:
        return pd.read_excel(file, engine='openpyxl')
    except:
        pass
        
    # 2. Yöntem: Eski Excel (XLS - xlrd)
    try:
        file.seek(0)
        return pd.read_excel(file, engine='xlrd')
    except:
        pass

    # 3. Yöntem: Metin/CSV (Türkçe Karakter CP1254)
    try:
        file.seek(0)
        return pd.read_csv(file, sep='\t', encoding='cp1254', on_bad_lines='skip')
    except:
        pass

    try:
        file.seek(0)
        return pd.read_csv(file, sep=None, engine='python', encoding='cp1254', on_bad_lines='skip')
    except:
        pass

    return None

# --- YARDIMCI FONKSİYON: METİN KONTROLÜ ---
def metin_icinde_var_mi(ana_metin, aranacaklar):
    """
    Metnin içinde 'sogutma', 'soğutma', 'cooling' gibi kelimelerden biri geçiyor mu bakar.
    Büyük/küçük harf ve Türkçe karakter duyarlılığını ortadan kaldırır.
    """
    if pd.isna(ana_metin): return False
    ana_metin = str(ana_metin).lower().replace('ğ', 'g').replace('ı', 'i')
    
    for kelime in aranacaklar:
        kelime = kelime.lower().replace('ğ', 'g').replace('ı', 'i')
        if kelime in ana_metin:
            return True
    return False

# --- ŞİFRE KONTROLÜ ---
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Güncelleme: 'Soğutma' ve 'Sogutma' farkı giderildi. Artık hepsi algılanır.")

    # --- AYARLAR (SOL MENÜ) ---
    st.sidebar.header("⚙️ Değer Değiştirme Kuralları")

    # 1. MINOL KURALLARI
    st.sidebar.subheader("Minol (1...) Kuralları")
    minol_isitma_eski = st.sidebar.number_input("Minol Isıtma: Eski", value=4)
    minol_isitma_yeni = st.sidebar.number_input("Minol Isıtma: Yeni", value=0)
    
    minol_sogutma_eski = st.sidebar.number_input("Minol Soğutma: Eski", value=8)
    minol_sogutma_yeni = st.sidebar.number_input("Minol Soğutma: Yeni", value=0)

    st.sidebar.markdown("---")
    st.sidebar.write("Minol Su Kuralları")
    minol_su_kural1_eski = st.sidebar.number_input("Minol Su (K1): Eski", value=0)
    minol_su_kural1_yeni = st.sidebar.number_input("Minol Su (K1): Yeni", value=2)
    minol_su_kural2_eski = st.sidebar.number_input("Minol Su (K2): Eski", value=1)
    minol_su_kural2_yeni = st.sidebar.number_input("Minol Su (K2): Yeni", value=23)

    # 2. DANFOS YENİ KURALLARI
    st.sidebar.subheader("Danfos Yeni (4...) Kuralları")
    danfos_yeni_eski = st.sidebar.number_input("D. Yeni Genel: Eski", value=0)
    danfos_yeni_yeni = st.sidebar.number_input("D. Yeni Genel: Yeni", value=23)

    # --- DOSYA YÜKLEME ---
    uploaded_files = st.file_uploader("Dosyaları Yükle", accept_multiple_files=True)

    if uploaded_files:
        tum_veriler = []
        
        for file in uploaded_files:
            df = dosyayi_zorla_oku(file)
            if df is not None:
                tum_veriler.append(df)
        
        if tum_veriler:
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            # Sütun İsimlerini Düzelt (İlk sütun Hizmet, İkincil Adres, Değer)
            first_col = main_df.columns[0]
            main_df.rename(columns={first_col: 'Hizmet_Tipi'}, inplace=True)
            
            # Sütun adlarını küçük harfe çevirerek bulmaya çalış (Hata önleyici)
            col_map = {c.lower(): c for c in main_df.columns}
            
            # Gerçek sütun isimlerini belirle
            col_hizmet = 'Hizmet_Tipi'
            col_adres = col_map.get('ikincil adres', col_map.get('i̇kincil adres', 'İkincil Adres'))
            col_deger = col_map.get('değer', col_map.get('deger', 'Değer'))

            # --- İŞLEM MANTIĞI ---
            def islem_yap(row):
                try:
                    hizmet = row[col_hizmet]
                    adres = str(row[col_adres])
                    deger = row[col_deger]
                except:
                    return 0 # Hatalı satır

                yeni_deger = deger

                # Marka Tespiti
                marka = "Diger"
                if adres.startswith('3'): marka = "Danfos"
                elif adres.startswith('1'): marka = "Minol"
                elif adres.startswith('4'): marka = "Danfos Yeni"

                # --- KURALLAR (GÜNCELLENDİ) ---
                
                # MINOL KURALLARI
                if marka == "Minol":
                    # Isıtma Kontrolü (isitma, ısitma, heating vb.)
                    if metin_icinde_var_mi(hizmet, ['isitma', 'ısıtma']):
                        if deger == minol_isitma_eski:
                            yeni_deger = minol_isitma_yeni
                    
                    # Soğutma Kontrolü (sogutma, soğutma, cooling vb.) - BURASI DÜZELTİLDİ
                    elif metin_icinde_var_mi(hizmet, ['sogutma', 'soğutma', 'cooling']):
                        if deger == minol_sogutma_eski:
                            yeni_deger = minol_sogutma_yeni
                            
                    # Su Kontrolü
                    elif metin_icinde_var_mi(hizmet, ['su', 'sicak', 'sıcak']):
                        if deger == minol_su_kural1_eski:
                            yeni_deger = minol_su_kural1_yeni
                        elif deger == minol_su_kural2_eski:
                            yeni_deger = minol_su_kural2_yeni
                
                # DANFOS YENİ KURALLARI
                elif marka == "Danfos Yeni":
                    if deger == danfos_yeni_eski:
                        yeni_deger = danfos_yeni_yeni

                return yeni_deger

            # İşlemi Uygula
            if col_adres in main_df.columns:
                main_df['Yeni_Deger'] = main_df.apply(islem_yap, axis=1)
                
                # Değerleri Güncelle
                main_df[col_deger] = main_df['Yeni_Deger']
                main_df.drop(columns=['Yeni_Deger'], inplace=True)
                
                st.success("✅ Veriler işlendi. Soğutma/Sogutma ayrımları kontrol edildi.")

                # --- İNDİRME VE AYRIŞTIRMA (GÜÇLENDİRİLDİ) ---
                def excel_indir(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                c1, c2, c3 = st.columns(3)
                
                # 1. ISITMA FİLTRESİ
                mask_isitma = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['isitma', 'ısıtma']))
                df_isitma = main_df[mask_isitma]
                c1.download_button("🔥 Isıtma İndir", excel_indir(df_isitma), "Isitma_Sonuc.xlsx")

                # 2. SOĞUTMA FİLTRESİ (Buradaki filtre de güçlendirildi)
                mask_sogutma = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['sogutma', 'soğutma', 'cooling']))
                df_sogutma = main_df[mask_sogutma]
                c2.download_button("❄️ Soğutma İndir", excel_indir(df_sogutma), "Sogutma_Sonuc.xlsx")

                # 3. SU FİLTRESİ
                mask_su = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['su', 'sicak', 'sıcak']))
                df_su = main_df[mask_su]
                c3.download_button("💧 Su İndir", excel_indir(df_su), "Su_Sonuc.xlsx")
                
                with st.expander("Sonuç Önizleme"):
                    st.dataframe(main_df.head(50))
            else:
                st.error("Sütun isimleri algılanamadı.")

else:
    st.warning("Şifre: 1234")
