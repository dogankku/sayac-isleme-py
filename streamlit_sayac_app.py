import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- ÖZEL DOSYA OKUYUCU (TÜRKÇE DESTEKLİ) ---
def dosyayi_zorla_oku(file):
    hatalar = []
    
    # Dosya imlecini başa al
    file.seek(0)
    
    # 1. Yöntem: Gerçek Excel (XLS/XLSX)
    try:
        return pd.read_excel(file)
    except:
        pass # Hata verirse sessizce diğer yönteme geç
        
    # 2. Yöntem: HTML Tablo (Bazen Excel diye HTML kaydederler)
    try:
        file.seek(0)
        dfs = pd.read_html(file, encoding='cp1254') # Türkçe desteği
        if dfs: return dfs[0]
    except:
        pass

    # 3. Yöntem: Metin Dosyası (Sekme ile ayrılmış - Türkçe CP1254)
    # Hatanın asıl çözümü muhtemelen burası
    try:
        file.seek(0)
        # 'Tanımlama' gibi başlık satırlarını atlamak için skiprows kullanabiliriz
        # Ancak önce doğrudan okumayı deneyelim
        return pd.read_csv(file, sep='\t', encoding='cp1254', on_bad_lines='skip')
    except Exception as e:
        hatalar.append(f"Türkçe TSV okunamadı: {e}")

    # 4. Yöntem: Metin Dosyası (Genel - Türkçe CP1254)
    try:
        file.seek(0)
        return pd.read_csv(file, sep=None, engine='python', encoding='cp1254', on_bad_lines='skip')
    except Exception as e:
        hatalar.append(f"Genel CSV okunamadı: {e}")

    return None

# --- ŞİFRE KONTROLÜ ---
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Sistem artık Türkçe karakterli bozuk Excel dosyalarını da okuyabilir.")

    # --- AYARLAR (SOL MENÜ) ---
    st.sidebar.header("⚙️ Değer Değiştirme Kuralları")

    # 1. MINOL KURALLARI
    st.sidebar.subheader("Minol (1...) Kuralları")
    minol_isitma_eski = st.sidebar.number_input("Minol Isıtma: Eski", value=1)
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
        basarisizlar = []
        
        for file in uploaded_files:
            df = dosyayi_zorla_oku(file)
            
            if df is not None:
                tum_veriler.append(df)
            else:
                basarisizlar.append(file.name)
        
        if basarisizlar:
            st.error(f"Şu dosyalar okunamadı: {basarisizlar}")

        if tum_veriler:
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            # İlk sütun ismini 'Hizmet_Tipi' yap
            first_col = main_df.columns[0]
            main_df.rename(columns={first_col: 'Hizmet_Tipi'}, inplace=True)
            
            # Sütun kontrolü (Büyük/Küçük harf duyarlılığını kaldırmak için)
            mevcut_sutunlar = [c.lower() for c in main_df.columns]
            
            # Eğer dosya yapısı çok karışıksa burada hata verebilir, o yüzden esnek yapıyoruz
            # Amaç 'ikincil adres' ve 'değer' sütunlarını bulmak
            
            # --- İŞLEM MANTIĞI ---
            def islem_yap(row):
                # Satırdaki verileri güvenli şekilde al
                # Sütun isimleri tam tutmuyorsa diye row.values ile index bazlı da gidebiliriz ama
                # şimdilik sütun isimlerinin standart olduğunu varsayıyoruz.
                try:
                    # Sütun adlarını tam bilmediğimiz bozuk dosyalarda 
                    # genellikle 1. sütun Hizmet, 2. veya 3. sütun Adres, Son sütun Değer olur.
                    # Burada standart isimleri deniyoruz:
                    hizmet = str(row.get('Hizmet_Tipi', '')).lower()
                    adres = str(row.get('İkincil Adres', row.get('ikincil adres', '')))
                    deger = row.get('Değer', row.get('değer', 0))
                except:
                    return 0

                yeni_deger = deger

                # Marka Tespiti
                marka = "Diger"
                if adres.startswith('3'): marka = "Danfos"
                elif adres.startswith('1'): marka = "Minol"
                elif adres.startswith('4'): marka = "Danfos Yeni"

                # Kurallar
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
                elif marka == "Danfos Yeni":
                    if deger == danfos_yeni_eski:
                        yeni_deger = danfos_yeni_yeni

                return yeni_deger

            # Sadece gerekli sütunlar varsa işlemi yap
            if any("adres" in str(c).lower() for c in main_df.columns):
                main_df['İşlenmiş_Değer'] = main_df.apply(islem_yap, axis=1)
                
                # Orijinal 'Değer' sütununu bul ve güncelle
                for col in main_df.columns:
                    if str(col).lower() == 'değer':
                        main_df[col] = main_df['İşlenmiş_Değer']
                
                st.success("✅ Dosyalar başarıyla çözüldü ve işlendi!")

                # --- İNDİRME ---
                def excel_indir(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                c1, c2, c3 = st.columns(3)
                
                df_isitma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Isıtma", case=False, na=False)]
                c1.download_button("🔥 Isıtma İndir", excel_indir(df_isitma), "Isitma_Sonuc.xlsx")

                df_sogutma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Soğutma", case=False, na=False)]
                c2.download_button("❄️ Soğutma İndir", excel_indir(df_sogutma), "Sogutma_Sonuc.xlsx")

                df_su = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Su", case=False, na=False)]
                c3.download_button("💧 Su İndir", excel_indir(df_su), "Su_Sonuc.xlsx")
                
                with st.expander("Verileri Kontrol Et"):
                    st.dataframe(main_df.head(50))
            else:
                st.warning("Dosya okundu ama 'İkincil Adres' sütunu bulunamadı. Lütfen aşağıdaki tabloya bakıp sütun ismini kontrol edin.")
                st.write(main_df.head())

else:
    st.warning("Şifre: 1234")
