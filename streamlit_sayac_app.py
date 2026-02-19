import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- ÖZEL DOSYA OKUYUCU ---
def dosyayi_zorla_oku(file):
    file.seek(0)
    try: return pd.read_excel(file, engine='openpyxl')
    except: pass
    try:
        file.seek(0)
        return pd.read_excel(file, engine='xlrd')
    except: pass
    try:
        file.seek(0)
        return pd.read_csv(file, sep='\t', encoding='cp1254', on_bad_lines='skip')
    except: pass
    try:
        file.seek(0)
        return pd.read_csv(file, sep=None, engine='python', encoding='cp1254', on_bad_lines='skip')
    except: pass
    return None

def metin_icinde_var_mi(ana_metin, aranacaklar):
    if pd.isna(ana_metin): return False
    ana_metin = str(ana_metin).lower().replace('ğ', 'g').replace('ı', 'i')
    for kelime in aranacaklar:
        kelime = kelime.lower().replace('ğ', 'g').replace('ı', 'i')
        if kelime in ana_metin: return True
    return False

# --- ŞİFRE KONTROLÜ ---
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Güncelleme: Danfos Yeni Isıtma sayaçlarındaki gereksiz alt satırları (sıcaklık, debi vb.) otomatik silme özelliği eklendi.")

    # --- AYARLAR (SOL MENÜ) ---
    st.sidebar.header("⚙️ Değer Değiştirme Kuralları")

    # 1. MINOL KURALLARI
    st.sidebar.subheader("Minol (1... veya 35...) Kuralları")
    minol_sifir_eski = st.sidebar.number_input("Minol 0 ise ne olsun? (Eski)", value=0)
    minol_sifir_yeni = st.sidebar.number_input("Minol 0 ise ne olsun? (Yeni)", value=9)
    minol_isitma_eski = st.sidebar.number_input("Minol Isıtma: Eski", value=4)
    minol_isitma_yeni = st.sidebar.number_input("Minol Isıtma: Yeni", value=0)
    minol_sogutma_eski = st.sidebar.number_input("Minol Soğutma: Eski", value=8)
    minol_sogutma_yeni = st.sidebar.number_input("Minol Soğutma: Yeni", value=0)

    st.sidebar.markdown("---")
    minol_su_kural1_eski = st.sidebar.number_input("Minol Su (K1): Eski", value=0)
    minol_su_kural1_yeni = st.sidebar.number_input("Minol Su (K1): Yeni", value=2)
    minol_su_kural2_eski = st.sidebar.number_input("Minol Su (K2): Eski", value=1)
    minol_su_kural2_yeni = st.sidebar.number_input("Minol Su (K2): Yeni", value=23)

    # 2. DANFOS YENİ KURALLARI
    st.sidebar.subheader("Danfos Yeni (4...) Kuralları")
    
    st.sidebar.write("🔥 Danfos Yeni Isıtma")
    # YENİ ÖZELLİK: Fazlalıkları silme butonu
    dy_isitma_fazlalik_sil = st.sidebar.checkbox("Aynı sayacın fazla satırlarını sil (Sadece 1. satırı tut)", value=True)
    
    dy_isitma_ozel_eski = st.sidebar.number_input("D. Yeni Isıtma Özel Kural (Eski)", value=12)
    dy_isitma_ozel_yeni = st.sidebar.number_input("D. Yeni Isıtma Özel Kural (Yeni)", value=13)

    st.sidebar.markdown("---")
    st.sidebar.write("❄️ Danfos Yeni Soğutma")
    dy_sogutma_sifir_eski = st.sidebar.number_input("D. Yeni Soğutma 0 Kuralı (Eski)", value=0)
    dy_sogutma_sifir_yeni = st.sidebar.number_input("D. Yeni Soğutma 0 Kuralı (Yeni)", value=9) 

    st.sidebar.markdown("---")
    st.sidebar.write("💧 Danfos Yeni Kullanım Suyu")
    dy_su_eski = st.sidebar.number_input("D. Yeni Su (Eski)", value=0)
    dy_su_yeni = st.sidebar.number_input("D. Yeni Su (Yeni)", value=23)

    # --- DOSYA YÜKLEME ---
    uploaded_files = st.file_uploader("Dosyaları Yükle", accept_multiple_files=True)

    if uploaded_files:
        tum_veriler = []
        for file in uploaded_files:
            df = dosyayi_zorla_oku(file)
            if df is not None: tum_veriler.append(df)
        
        if tum_veriler:
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            first_col = main_df.columns[0]
            main_df.rename(columns={first_col: 'Hizmet_Tipi'}, inplace=True)
            
            col_map = {c.lower(): c for c in main_df.columns}
            col_hizmet = 'Hizmet_Tipi'
            col_adres = col_map.get('ikincil adres', col_map.get('i̇kincil adres', 'İkincil Adres'))
            col_deger = col_map.get('değer', col_map.get('deger', 'Değer'))

            # Marka ataması yapalım ki kolay filtreleyelim
            def marka_bul(adres):
                adres = str(adres).strip()
                if adres.startswith('35'): return "Minol"
                if adres.startswith('1'): return "Minol"
                if adres.startswith('3'): return "Danfos"
                if adres.startswith('4'): return "Danfos Yeni"
                return "Diger"
                
            if col_adres in main_df.columns:
                main_df['Marka'] = main_df[col_adres].apply(marka_bul)

                # --- MÜKERRER SATIRLARI SİLME İŞLEMİ (Sadece Danfos Yeni Isıtma İçin) ---
                if dy_isitma_fazlalik_sil:
                    islem_oncesi_satir = len(main_df)
                    
                    # Danfos Yeni ve Isıtma olan satırları bul
                    mask_dy_isitma = (main_df['Marka'] == 'Danfos Yeni') & (main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['isitma', 'ısıtma'])))
                    
                    dy_isitma_df = main_df[mask_dy_isitma].copy()
                    diger_df = main_df[~mask_dy_isitma].copy()
                    
                    # İkincil adrese göre aynı olanların SADECE İLKİNİ tut, diğerlerini sil (Fazlalık 7-8 satır çöpe gider)
                    dy_isitma_tekil = dy_isitma_df.drop_duplicates(subset=[col_adres], keep='first')
                    
                    # Temizlenmiş veriyi ana listeye geri ekle
                    main_df = pd.concat([diger_df, dy_isitma_tekil], ignore_index=True)
                    
                    silinen_satir = islem_oncesi_satir - len(main_df)
                    if silinen_satir > 0:
                        st.warning(f"🧹 Danfos Yeni Isıtma sayaçlarından {silinen_satir} adet gereksiz/mükerrer teknik detay satırı başarıyla temizlendi!")

                # --- İŞLEM MANTIĞI (Değer Değiştirme) ---
                def islem_yap(row):
                    try:
                        hizmet = str(row[col_hizmet]).lower()
                        deger = row[col_deger]
                    except: return 0

                    try: deger_sayi = float(deger); sayi_mi = True
                    except: deger_sayi = deger; sayi_mi = False

                    yeni_deger = deger
                    marka = row['Marka']

                    if marka == "Minol":
                        if metin_icinde_var_mi(hizmet, ['isitma', 'ısıtma']):
                            if sayi_mi and deger_sayi == float(minol_isitma_eski): yeni_deger = minol_isitma_yeni
                            elif sayi_mi and deger_sayi == float(minol_sifir_eski): yeni_deger = minol_sifir_yeni
                        elif metin_icinde_var_mi(hizmet, ['sogutma', 'soğutma', 'cooling']):
                            if sayi_mi and deger_sayi == float(minol_sogutma_eski): yeni_deger = minol_sogutma_yeni
                            elif sayi_mi and deger_sayi == float(minol_sifir_eski): yeni_deger = minol_sifir_yeni
                        elif metin_icinde_var_mi(hizmet, ['su', 'sicak', 'sıcak', 'kullanım', 'kullanim']):
                            if sayi_mi and deger_sayi == float(minol_su_kural1_eski): yeni_deger = minol_su_kural1_yeni
                            elif sayi_mi and deger_sayi == float(minol_su_kural2_eski): yeni_deger = minol_su_kural2_yeni
                    
                    elif marka == "Danfos Yeni":
                        if metin_icinde_var_mi(hizmet, ['isitma', 'ısıtma']):
                            if sayi_mi and deger_sayi == float(dy_isitma_ozel_eski): yeni_deger = dy_isitma_ozel_yeni
                        elif metin_icinde_var_mi(hizmet, ['sogutma', 'soğutma', 'cooling']):
                            if sayi_mi and deger_sayi == float(dy_sogutma_sifir_eski): yeni_deger = dy_sogutma_sifir_yeni
                        elif metin_icinde_var_mi(hizmet, ['su', 'sicak', 'sıcak', 'kullanım', 'kullanim']):
                            if sayi_mi and deger_sayi == float(dy_su_eski): yeni_deger = dy_su_yeni

                    return yeni_deger

                main_df['Yeni_Deger'] = main_df.apply(islem_yap, axis=1)
                main_df[col_deger] = main_df['Yeni_Deger']
                main_df.drop(columns=['Yeni_Deger', 'Marka'], inplace=True) # Eklediğimiz geçici marka sütununu siliyoruz
                
                st.success("✅ Tüm kurallar uygulandı. Dosyalar indirmeye hazır!")

                def excel_indir(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                c1, c2, c3 = st.columns(3)
                mask_isitma = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['isitma', 'ısıtma']))
                c1.download_button("🔥 Isıtma İndir", excel_indir(main_df[mask_isitma]), "Isitma_Sonuc.xlsx")

                mask_sogutma = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['sogutma', 'soğutma', 'cooling']))
                c2.download_button("❄️ Soğutma İndir", excel_indir(main_df[mask_sogutma]), "Sogutma_Sonuc.xlsx")

                mask_su = main_df[col_hizmet].apply(lambda x: metin_icinde_var_mi(x, ['su', 'sicak', 'sıcak', 'kullanım', 'kullanim']))
                c3.download_button("💧 Su İndir", excel_indir(main_df[mask_su]), "Su_Sonuc.xlsx")
                
                with st.expander("Sonuç Önizleme"):
                    st.dataframe(main_df.head(50))
            else:
                st.error("Sütun isimleri algılanamadı.")

else:
    st.warning("Şifre: 1234")
