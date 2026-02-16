#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Sayfa yapılandırması
st.set_page_config(
    page_title="Sayaç Veri İşleme",
    page_icon="🏢",
    layout="wide"
)

def parse_excel_file(uploaded_file):
    """
    Kodlamayı (encoding) otomatik algılamaya çalışan geliştirilmiş okuyucu.
    """
    df = None
    try:
        # 1. Deneme: Gerçek Excel (XLSX) formatı
        try:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except:
            # 2. Deneme: UTF-8 Tab-delimited (Yaygın format)
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t', encoding='utf-8', on_bad_lines='skip')
            except:
                # 3. Deneme: ANSI / Latin-1 (Eski Windows yazılımları için)
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep='\t', encoding='latin-1', on_bad_lines='skip')
                except:
                    # 4. Deneme: UTF-16 (Hata aldığın ama BOM gerektirmeyen hali)
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep='\t', encoding='utf-16', errors='ignore')

        if df is None or df.empty:
            return None, "Dosya içeriği okunamadı veya boş."

        # Eğer veri tek bir sütuna sıkışmışsa sütunlara ayır
        if df.shape[1] == 1:
            first_col_name = df.columns[0]
            # Sütun başlığını da veriye dahil et (Bazen başlık ilk satırda kaybolur)
            combined_data = pd.concat([pd.Series([first_col_name]), df.iloc[:, 0].astype(str)], ignore_index=True)
            df = combined_data.str.split('\t', expand=True)

        # Standart başlıkları uygula
        headers = ['Tanımlama', 'Aygıt', 'Değer', 'Orta', 'Birincil adres', 
                   'İkincil adres', 'Üretim', 'Yapımcı', 'Aygıt durumu', 'Birim', 'Tarih']
        
        # DataFrame sütun sayılarını eşitle
        current_cols = df.shape[1]
        df.columns = headers[:current_cols]
        
        return df, None
        
    except Exception as e:
        return None, f"Sistem Hatası: {str(e)}"

def verileri_ayir(df):
    try:
        if 'Tanımlama' not in df.columns:
            return None, None, "Sütunlar ayrıştırılamadı. Lütfen dosya formatını kontrol edin."

        # Isıtma ve Soğutma filtreleri
        isitma_mask = df['Tanımlama'].str.contains('ISITMA', case=False, na=False)
        isitma_df = df[isitma_mask].copy()

        sogutma_mask = (
            df['Tanımlama'].str.contains('SO', case=False, na=False) & 
            df['Tanımlama'].str.contains('UTMA', case=False, na=False) &
            ~isitma_mask
        )
        sogutma_df = df[sogutma_mask].copy()
        
        return isitma_df, sogutma_df, None
    except Exception as e:
        return None, None, str(e)

def degerleri_donustur(df):
    """ 00->09, 01->00 dönüşümü """
    if df.empty or 'Değer' not in df.columns:
        return df, 0
    
    df_copy = df.copy()
    onceki = df_copy['Değer'].astype(str).str.strip()
    
    def transform(x):
        x = str(x).strip()
        if x in ['00', '0']: return '09'
        if x in ['01', '1']: return '00'
        return x

    df_copy['Değer'] = onceki.apply(transform)
    degisen = (onceki != df_copy['Değer']).sum()
    return df_copy, degisen

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def main():
    st.title("🏢 Sayaç Veri İşleme (Versiyon 2.1)")
    st.markdown("Hatalı karakter ve formatlar temizlendi.")

    uploaded_file = st.file_uploader("Dosyanızı buraya sürükleyin", type=['xls', 'xlsx', 'csv', 'txt'])

    if uploaded_file:
        df, error = parse_excel_file(uploaded_file)
        
        if error:
            st.error(f"❌ {error}")
            return

        st.success(f"✅ Veri başarıyla çözüldü ({len(df)} satır).")
        
        isitma_df, sogutma_df, err = verileri_ayir(df)
        
        if err:
            st.warning(err)
            st.dataframe(df.head()) # Sütunları görmesi için ham veriyi göster
            return

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Isıtma Verileri")
            processed_i, count_i = degerleri_donustur(isitma_df)
            st.metric("Değiştirilen Satır", count_i)
            st.dataframe(processed_i, use_container_width=True)
            if not processed_i.empty:
                st.download_button("Isıtma Excelini İndir", to_excel(processed_i), "Isitma_Sonuc.xlsx")

        with col2:
            st.subheader("❄️ Soğutma Verileri")
            processed_s, count_s = degerleri_donustur(sogutma_df)
            st.metric("Değiştirilen Satır", count_s)
            st.dataframe(processed_s, use_container_width=True)
            if not processed_s.empty:
                st.download_button("Soğutma Excelini İndir", to_excel(processed_s), "Sogutma_Sonuc.xlsx")

if __name__ == '__main__':
    main()
