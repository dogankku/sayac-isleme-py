import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sayaç Yönetim Paneli", layout="wide")

# --- AKILLI DOSYA OKUYUCU FONKSİYONU ---
def dosyayi_zorla_oku(file):
    """
    Bu fonksiyon dosyanın uzantısına bakmaz.
    Sırasıyla tüm yöntemleri deneyerek dosyayı okumaya çalışır.
    """
    hatalar = []
    
    # Yöntem 1: Standart Excel (XLSX - openpyxl)
    try:
        file.seek(0)
        return pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        hatalar.append(f"XLSX okunamadı: {e}")
    
    # Yöntem 2: Eski Excel (XLS - xlrd)
    try:
        file.seek(0)
        return pd.read_excel(file, engine='xlrd')
    except Exception as e:
        hatalar.append(f"XLS okunamadı: {e}")

    # Yöntem 3: HTML Tablo (Excel görünümlü HTML - Sık karşılaşılır)
    try:
        file.seek(0)
        # read_html bir liste döndürür, ilk tabloyu alırız
        dfs = pd.read_html(file)
        if dfs:
            return dfs[0]
    except Exception as e:
        hatalar.append(f"HTML okunamadı: {e}")

    # Yöntem 4: CSV / Metin (Sekme ile ayrılmış)
    try:
        file.seek(0)
        return pd.read_csv(file, sep='\t', encoding='utf-8')
    except Exception as e:
        hatalar.append(f"TSV okunamadı: {e}")

    # Yöntem 5: CSV / Metin (Noktalı virgül veya Virgül)
    try:
        file.seek(0)
        return pd.read_csv(file, sep=None, engine='python', encoding='utf-8')
    except Exception as e:
        hatalar.append(f"CSV okunamadı: {e}")
        
    return None

# --- ŞİFRE KONTROLÜ ---
if st.sidebar.text_input("Sistem Şifresi", type="password") == "1234":
    
    st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")
    st.info("Sistem; Gerçek Excel, HTML veya Metin tabanlı tüm sayaç dosyalarını otomatik tanır.")

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
        basarisiz_dosyalar = []
        
        for file in uploaded_files:
            # Akıllı okuyucuyu çağır
            df = dosyayi_zorla_oku(file)
            
            if df is not None:
                tum_veriler.append(df)
            else:
                basarisiz_dosyalar.append(file.name)

        if basarisiz_dosyalar:
            st.error(f"Şu dosyalar hiçbir yöntemle okunamadı: {', '.join(basarisiz_dosyalar)}")

        if tum_veriler:
            # Tüm verileri birleştir
            main_df = pd.concat(tum_veriler, ignore_index=True)
            
            # Sütun İsimlerini Düzeltme (İlk sütun her zaman Hizmet Tipi olsun)
            first_col = main_df.columns[0]
            main_df.rename(columns={first_col: 'Hizmet_Tipi'}, inplace=True)
            
            # Sütun Kontrolü
            gerekli_sutunlar = ['İkincil Adres', 'Değer'] # Senin dosyalardaki sütun isimleri
            eksik_sutunlar = [col for col in gerekli_sutunlar if col not in main_df.columns]

            if eksik_sutunlar:
                st.error(f"HATA: Dosyalarda şu sütunlar bulunamadı: {eksik_sutunlar}. Excel başlıklarını kontrol ediniz.")
                st.write("Okunan dosyadaki sütunlar:", main_df.columns.tolist())
            else:
                # --- İŞLEM MANTIĞI ---
                def islem_yap(row):
                    try:
                        hizmet = str(row['Hizmet_Tipi']).lower()
                        adres = str(row['İkincil Adres'])
                        deger = row['Değer']
                    except:
                        return 0 # Hatalı satır varsa 0 döndür
                    
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

                main_df['Değer'] = main_df.apply(islem_yap, axis=1)
                st.success("✅ Veriler başarıyla işlendi!")

                # --- İNDİRME ---
                def excel_indir(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                c1, c2, c3 = st.columns(3)
                
                df_isitma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Isıtma", case=False, na=False)]
                c1.download_button("🔥 Isıtma İndir", excel_indir(df_isitma), "Isitma_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                df_sogutma = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Soğutma", case=False, na=False)]
                c2.download_button("❄️ Soğutma İndir", excel_indir(df_sogutma), "Sogutma_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                df_su = main_df[main_df['Hizmet_Tipi'].astype(str).str.contains("Su", case=False, na=False)]
                c3.download_button("💧 Su İndir", excel_indir(df_su), "Su_Sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                with st.expander("Sonuç Tablosunu Göster"):
                    st.dataframe(main_df.head(50))

else:
    st.warning("Şifre: 1234")
