import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- ŞİFRE KONTROLÜ ---
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Sistem eski (.xls) ve yeni (.xlsx) tüm dosyaları otomatik tanır.")

    # --- AYARLAR VE KURALLAR (SOL MENÜ) ---
    st.sidebar.header("⚙️ Değer Değiştirme Kuralları")

    # 1. MINOL KURALLARI
    st.sidebar.subheader("Minol (1...) Kuralları")
    # Notlarındaki "1 -> 0 olacak" gibi kuralları buradan ayarlayabilirsin
    minol_isitma_eski = st.sidebar.number_input("Minol Isıtma: Eski Değer", value=4)
    minol_isitma_yeni = st.sidebar.number_input("Minol Isıtma: Yeni Değer", value=0)
    
    minol_sogutma_eski = st.sidebar.number_input("Minol Soğutma: Eski Değer", value=8)
    minol_sogutma_yeni = st.sidebar.number_input("Minol Soğutma: Yeni Değer", value=0)

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
    uploaded_files = st.file_uploader("Dosyaları Yükle", accept_multiple_files=True, type=['xlsx', 'xls'])

    if uploaded_files:
        tum_veriler = []
        
        for file in uploaded_files:
            try:
                # --- DÜZELTME BURADA YAPILDI ---
                # Dosya ismini tamamen küçük harfe çevirip kontrol ediyoruz (.XLS ile .xls aynı sayılsın diye)
                filename_kucuk = file.name.lower()
                
                if filename_kucuk.endswith('.xls'):
                    # Eski Excel dosyaları (.XLS) için 'xlrd' motoru ŞARTTIR
                    df = pd.read_excel(file, engine='xlrd')
                elif filename_kucuk.endswith('.xlsx'):
                    # Yeni Excel dosyaları (.XLSX) için 'openpyxl' kullanılır
                    df = pd.read_excel(file, engine='openpyxl')
                else:
                    st.error(f"{file.name} formatı desteklenmiyor.")
                    continue

                tum_veriler.append(df)
                
            except Exception as e:
                st.error(f"❌ {file.name} dosyası okunamadı! Hata detayı: {e}")

        if tum_veriler:
            # Tüm verileri birleştir
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            # İlk sütun ismini standartlaştır (Isıtma/Soğutma yazan sütun)
            first_col = main_df.columns[0]
            main_df.rename(columns={first_col: 'Hizmet_Tipi'}, inplace=True)
            
            # Sütun isim kontrolü
            if 'İkincil Adres' not in main_df.columns or 'Değer' not in main_df.columns:
                st.error("HATA: Yüklenen dosyada 'İkincil Adres' veya 'Değer' sütunu bulunamadı. Lütfen Excel başlıklarını kontrol edin.")
            else:
                # --- İŞLEM MANTIĞI ---
                def islem_yap(row):
                    hizmet = str(row['Hizmet_Tipi']).lower()
                    adres = str(row['İkincil Adres'])
                    deger = row['Değer']
                    
                    yeni_deger = deger # Varsayılan: Değişme

                    # 1. Marka Tespiti (Adres başlangıcına göre)
                    marka = "Diger"
                    if adres.startswith('3'): marka = "Danfos"
                    elif adres.startswith('1'): marka = "Minol"
                    elif adres.startswith('4'): marka = "Danfos Yeni"

                    # 2. Kuralları Uygula
                    
                    # --- MINOL ---
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
                    
                    # --- DANFOS YENİ ---
                    elif marka == "Danfos Yeni":
                        if deger == danfos_yeni_eski:
                            yeni_deger = danfos_yeni_yeni

                    return yeni_deger

                # Fonksiyonu çalıştır
                main_df['Değer'] = main_df.apply(islem_yap, axis=1)
                st.success("✅ Tüm dosyalar birleştirildi ve kurallar uygulandı!")

                # --- İNDİRME İŞLEMİ ---
                def excel_indir(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                c1, c2, c3 = st.columns(3)
                
                # Isıtma İndir
                df_isitma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Isıtma", case=False, na=False)]
                c1.download_button("🔥 Isıtma İndir", excel_indir(df_isitma), "Isitma_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                # Soğutma İndir
                df_sogutma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Soğutma", case=False, na=False)]
                c2.download_button("❄️ Soğutma İndir", excel_indir(df_sogutma), "Sogutma_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                # Su İndir
                df_su = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Su", case=False, na=False)]
                c3.download_button("💧 Su İndir", excel_indir(df_su), "Su_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                with st.expander("Sonuç Önizleme"):
                    st.dataframe(main_df.head(50))

else:
    st.warning("Giriş yapmak için şifrenizi giriniz.")
