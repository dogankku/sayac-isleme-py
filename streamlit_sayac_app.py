import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- ŞİFRE KONTROLÜ ---
# Soldaki menüyü açıp şifreyi girince ekran gelir
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Eski tip (.xls) ve yeni tip (.xlsx) dosyaları yükleyebilirsiniz.")

    # --- AYARLAR VE KURALLAR (SOL MENÜ) ---
    st.sidebar.header("⚙️ Değer Değiştirme Kuralları")
    st.sidebar.warning("Buradaki değerleri değiştirdiğinizde çıktılar anında güncellenir.")

    # 1. MINOL KURALLARI
    st.sidebar.subheader("Minol (1...) Kuralları")
    minol_isitma_eski = st.sidebar.number_input("Minol Isıtma: Hangi değer değişsin?", value=4)
    minol_isitma_yeni = st.sidebar.number_input("Minol Isıtma: Yerine ne yazılsın?", value=0)
    
    st.sidebar.markdown("---")
    minol_sogutma_eski = st.sidebar.number_input("Minol Soğutma: Hangi değer değişsin?", value=8)
    minol_sogutma_yeni = st.sidebar.number_input("Minol Soğutma: Yerine ne yazılsın?", value=0)

    st.sidebar.markdown("---")
    st.sidebar.write("Minol Su Kuralları (2 Kademeli)")
    # Kural 1
    minol_su_kural1_eski = st.sidebar.number_input("Minol Su (Kural 1): Eski", value=0)
    minol_su_kural1_yeni = st.sidebar.number_input("Minol Su (Kural 1): Yeni", value=2)
    # Kural 2
    minol_su_kural2_eski = st.sidebar.number_input("Minol Su (Kural 2): Eski", value=1)
    minol_su_kural2_yeni = st.sidebar.number_input("Minol Su (Kural 2): Yeni", value=23)

    # 2. DANFOS YENİ KURALLARI
    st.sidebar.subheader("Danfos Yeni (4...) Kuralları")
    danfos_yeni_eski = st.sidebar.number_input("D. Yeni Genel: Eski Değer", value=0)
    danfos_yeni_yeni = st.sidebar.number_input("D. Yeni Genel: Yeni Değer", value=23)

    # --- DOSYA YÜKLEME ---
    # .xls ve .xlsx desteği eklendi
    uploaded_files = st.file_uploader("Sayaç Dosyalarını Yükle (Çoklu Seçim)", 
                                      accept_multiple_files=True, 
                                      type=['xlsx', 'xls'])

    if uploaded_files:
        tum_veriler = []
        
        for file in uploaded_files:
            try:
                # Dosya uzantısına göre okuma motorunu seç
                if file.name.endswith('.xls'):
                    df = pd.read_excel(file, engine='xlrd')
                else:
                    df = pd.read_excel(file, engine='openpyxl')
                
                tum_veriler.append(df)
            except Exception as e:
                st.error(f"{file.name} dosyası okunurken hata oluştu: {e}")

        if tum_veriler:
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            # Sütun İsimlerini Standartlaştır (1. Sütun Hizmet, İkincil Adres, Değer)
            # Kodun çalışması için sütun isimlerini dosyadan alıp değişkene atıyoruz
            col_hizmet = main_df.columns[0] # İlk sütunun adı ne olursa olsun "Hizmet" kabul et
            col_adres = 'İkincil Adres'     # Excelde bu isimle olmalı
            col_deger = 'Değer'             # Excelde bu isimle olmalı

            # Sütun kontrolü
            if col_adres not in main_df.columns or col_deger not in main_df.columns:
                st.error(f"Excel dosyasında '{col_adres}' ve '{col_deger}' sütun başlıkları bulunamadı!")
                st.stop()

            # --- İŞLEM FONKSİYONU ---
            def islem_yap(row):
                hizmet = str(row[col_hizmet]).lower()
                adres = str(row[col_adres])
                deger = row[col_deger]
                
                # Marka Tespiti
                marka = "Diger"
                if adres.startswith('3'): marka = "Danfos"
                elif adres.startswith('1'): marka = "Minol"
                elif adres.startswith('4'): marka = "Danfos Yeni"

                # Kuralları Uygula
                yeni_deger = deger

                # MINOL KURALLARI
                if marka == "Minol":
                    if "ısıtma" in hizmet and deger == minol_isitma_eski:
                        yeni_deger = minol_isitma_yeni
                    elif "soğutma" in hizmet and deger == minol_sogutma_eski:
                        yeni_deger = minol_sogutma_yeni
                    elif ("su" in hizmet or "sıcak" in hizmet):
                        if deger == minol_su_kural1_eski:
                            yeni_deger = minol_su_kural1_yeni
                        elif deger == minol_su_kural2_eski:
                            yeni_deger = minol_su_kural2_yeni
                
                # DANFOS YENİ KURALLARI
                elif marka == "Danfos Yeni":
                    if deger == danfos_yeni_eski:
                        yeni_deger = danfos_yeni_yeni
                
                # DANFOS (ESKİ) - Değişiklik yok (0 kalır)
                
                return yeni_deger

            # Hesaplamayı Başlat
            main_df['İşlenmiş Değer'] = main_df.apply(islem_yap, axis=1)
            
            # Orijinal Değer sütununu güncelle
            main_df[col_deger] = main_df['İşlenmiş Değer']
            main_df.drop(columns=['İşlenmiş Değer'], inplace=True)
            
            st.success("✅ Veriler işlendi ve kurallar uygulandı.")

            # --- DOSYALARI AYIR VE İNDİR ---
            def excel_yap(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                return output.getvalue()

            c1, c2, c3 = st.columns(3)

            # 1. ISITMA
            df_isitma = main_df[main_df[col_hizmet].astype(str).str.contains("Isıtma", case=False, na=False)]
            c1.download_button("🔥 Isıtma Dosyasını İndir", excel_yap(df_isitma), "Isitma_Sonuc.xlsx")

            # 2. SOĞUTMA
            df_sogutma = main_df[main_df[col_hizmet].astype(str).str.contains("Soğutma", case=False, na=False)]
            c2.download_button("❄️ Soğutma Dosyasını İndir", excel_yap(df_sogutma), "Sogutma_Sonuc.xlsx")

            # 3. KULLANIM SUYU
            df_su = main_df[main_df[col_hizmet].astype(str).str.contains("Su", case=False, na=False)]
            c3.download_button("💧 Kul. Suyu Dosyasını İndir", excel_yap(df_su), "Su_Sonuc.xlsx")
            
            with st.expander("Veri Önizleme"):
                st.dataframe(main_df.head(50))

else:
    st.warning("Giriş yapmak için şifrenizi giriniz.")
