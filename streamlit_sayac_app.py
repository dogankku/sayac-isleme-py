import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Gelişmiş Sayaç İşleme", layout="wide")

def parse_file(uploaded_file):
    try:
        # Esnek okuma mantığı (Önceki hatayı engellemek için)
        try:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep='\t', encoding='latin-1', on_bad_lines='skip')
        
        if df.shape[1] == 1:
            df = df.iloc[:, 0].str.split('\t', expand=True)
            
        headers = ['Tanımlama', 'Aygıt', 'Değer', 'Orta', 'Birincil adres', 
                   'İkincil adres', 'Üretim', 'Yapımcı', 'Aygıt durumu', 'Birim', 'Tarih']
        df.columns = headers[:df.shape[1]]
        return df, None
    except Exception as e:
        return None, str(e)

def transform_logic(df, rules):
    """
    rules: { '10_start': {'search1': 'replace1', 'search2': 'replace2'},
             'others':   {'search1': 'replace1', 'search2': 'replace2'} }
    """
    df_copy = df.copy()
    if 'Değer' not in df_copy.columns or 'Aygıt' not in df_copy.columns:
        return df_copy, 0

    count = 0
    def apply_rule(row):
        nonlocal count
        aygit = str(row['Aygıt']).strip()
        deger = str(row['Değer']).strip()
        
        # Sayaç tipini belirle
        target_rules = rules['10_start'] if aygit.startswith('10') else rules['others']
        
        if deger in target_rules and target_rules[deger] != "":
            count += 1
            return target_rules[deger]
        return row['Değer']

    df_copy['Değer'] = df_copy.apply(apply_rule, axis=1)
    return df_copy, count

def main():
    st.title("🏢 Özelleştirilebilir Sayaç Veri İşleme")
    
    # 1. DOSYA YÜKLEME
    uploaded_file = st.file_uploader("Dosyayı Seçin", type=['xls', 'xlsx', 'csv', 'txt'])
    
    if uploaded_file:
        df, err = parse_file(uploaded_file)
        if err:
            st.error(f"Dosya okuma hatası: {err}")
            return

        st.sidebar.header("🔄 Dönüşüm Ayarları")
        
        # 2. KULLANICI GİRİŞ PANELİ (DİNAMİK)
        with st.sidebar:
            st.subheader("10 ile Başlayan Sayaçlar")
            in10_s1 = st.text_input("Aranan Değer 1 (Tip 10)", "00")
            in10_r1 = st.text_input("Yeni Değer 1 (Tip 10)", "09")
            in10_s2 = st.text_input("Aranan Değer 2 (Tip 10)", "01")
            in10_r2 = st.text_input("Yeni Değer 2 (Tip 10)", "00")

            st.divider()

            st.subheader("Diğer Sayaçlar")
            oth_s1 = st.text_input("Aranan Değer 1 (Diğer)", "00")
            oth_r1 = st.text_input("Yeni Değer 1 (Diğer)", "09")
            oth_s2 = st.text_input("Aranan Değer 2 (Diğer)", "01")
            oth_r2 = st.text_input("Yeni Değer 2 (Diğer)", "00")

        rules = {
            '10_start': {in10_s1: in10_r1, in10_s2: in10_r2},
            'others': {oth_s1: oth_r1, oth_s2: oth_r2}
        }

        # 3. AYRIŞTIRMA VE İŞLEME
        isitma_mask = df['Tanımlama'].str.contains('ISITMA', case=False, na=False)
        isitma_df = df[isitma_mask].copy()
        
        sogutma_mask = (df['Tanımlama'].str.contains('SO', case=False, na=False) & 
                        df['Tanımlama'].str.contains('UTMA', case=False, na=False) & 
                        ~isitma_mask)
        sogutma_df = df[sogutma_mask].copy()

        # 4. SONUÇLARI GÖSTER
        tab1, tab2 = st.tabs(["🔥 Isıtma İşlemleri", "❄️ Soğutma İşlemleri"])

        with tab1:
            if not isitma_df.empty:
                processed_i, count_i = transform_logic(isitma_df, rules)
                st.success(f"Isıtma: {count_i} adet değer güncellendi.")
                st.dataframe(processed_i)
                
                output_i = BytesIO()
                with pd.ExcelWriter(output_i, engine='openpyxl') as w:
                    processed_i.to_excel(w, index=False)
                st.download_button("Isıtma Excel İndir", output_i.getvalue(), "Isitma_Guncel.xlsx")
            else:
                st.info("Isıtma verisi bulunamadı.")

        with tab2:
            if not sogutma_df.empty:
                processed_s, count_s = transform_logic(sogutma_df, rules)
                st.success(f"Soğutma: {count_s} adet değer güncellendi.")
                st.dataframe(processed_s)
                
                output_s = BytesIO()
                with pd.ExcelWriter(output_s, engine='openpyxl') as w:
                    processed_s.to_excel(w, index=False)
                st.download_button("Soğutma Excel İndir", output_s.getvalue(), "Sogutma_Guncel.xlsx")
            else:
                st.info("Soğutma verisi bulunamadı.")

if __name__ == '__main__':
    main()
