#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sayac Veri Isleme Programi - Streamlit Versiyonu
55 Katli 2 Bloklu Site - Isitma ve Sogutma Sayaclari
"""

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
    Hem gerçek Excel hem de Tab-delimited (tek sütuna sıkışmış) 
    dosyaları okuyup sütunlara ayırır.
    """
    try:
        # Önce dosyayı standart Excel olarak açmayı dene
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except Exception:
            # Eğer 'Not a zip file' hatası alırsak, dosya muhtemelen Tab-delimited metindir
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep='\t', encoding='utf-16', on_bad_lines='skip')
            
            # Eğer utf-16 başarısız olursa utf-8 veya latin-1 dene
            if df.empty or df.shape[1] < 2:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t', encoding='latin-1', on_bad_lines='skip')

        # Eğer veri tek bir sütunda toplanmışsa (sekme ile ayrılmış ama tek sütun görünüyor)
        if df.shape[1] == 1:
            first_col = df.iloc[:, 0].astype(str)
            df = first_col.str.split('\t', expand=True)

        # Sütun adlarını sabitle
        headers = ['Tanımlama', 'Aygıt', 'Değer', 'Orta', 'Birincil adres', 
                   'İkincil adres', 'Üretim', 'Yapımcı', 'Aygıt durumu', 'Birim', 'Tarih']
        
        # Sütun sayısına göre başlıkları ata
        df.columns = headers[:len(df.columns)]
        
        return df, None
        
    except Exception as e:
        return None, f"Okuma Hatası: {str(e)}"

def verileri_ayir(df):
    """
    Isitma ve sogutma verilerini ayirir
    """
    try:
        if 'Tanımlama' not in df.columns:
            return None, None, "'Tanımlama' sütunu bulunamadı!"

        # Isıtma verilerini filtrele
        isitma_mask = df['Tanımlama'].str.contains('ISITMA', case=False, na=False)
        isitma_df = df[isitma_mask].copy()

        # Soğutma verilerini filtrele (SO...UTMA içerenler)
        sogutma_mask = (
            df['Tanımlama'].str.contains('SO', case=False, na=False) & 
            df['Tanımlama'].str.contains('UTMA', case=False, na=False) &
            ~isitma_mask
        )
        sogutma_df = df[sogutma_mask].copy()
        
        return isitma_df, sogutma_df, None
        
    except Exception as e:
        return None, None, str(e)

def degerleri_donustur(df, deger_sutunu='Değer'):
    """
    00 -> 09, 01 -> 00 donusumu yapar
    """
    try:
        df_copy = df.copy()

        def transform(val):
            val_str = str(val).strip()
            if val_str == '00' or val_str == '0':
                return '09'
            elif val_str == '01' or val_str == '1':
                return '00'
            return val
        
        if deger_sutunu in df_copy.columns:
            onceki = df_copy[deger_sutunu].copy()
            df_copy[deger_sutunu] = df_copy[deger_sutunu].apply(transform)
            degisen = (onceki != df_copy[deger_sutunu]).sum()
            return df_copy, degisen, None
        else:
            return df_copy, 0, f"'{deger_sutunu}' bulunamadı"
            
    except Exception as e:
        return df, 0, str(e)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def main():
    st.title("🏢 Sayaç Veri İşleme Programı")
    st.info("XLSX, XLS veya Tab-Delimited dosyalarınızı buraya yükleyebilirsiniz.")

    uploaded_file = st.file_uploader("Dosya Seçin", type=['xls', 'xlsx', 'csv', 'txt'])

    if uploaded_file:
        df, error = parse_excel_file(uploaded_file)
        
        if error:
            st.error(f"❌ {error}")
            return

        st.success(f"✅ {len(df)} satır veri yüklendi.")
        
        # Veri İşleme
        isitma_df, sogutma_df, err = verileri_ayir(df)
        
        if err:
            st.error(err)
            return

        # Görselleştirme ve Dönüşüm
        col1, col2 = st.columns(2)
        
        # ISITMA BÖLÜMÜ
        with col1:
            st.subheader("🔥 Isıtma")
            if not isitma_df.empty:
                i_df, count, _ = degerleri_donustur(isitma_df)
                st.write(f"Değiştirilen: {count}")
                st.dataframe(i_df.head(10))
                st.download_button("Isıtma Excel İndir", to_excel(i_df), f"Isitma_{datetime.now().day}.xlsx")
            else:
                st.warning("Isıtma verisi bulunamadı.")

        # SOĞUTMA BÖLÜMÜ
        with col2:
            st.subheader("❄️ Soğutma")
            if not sogutma_df.empty:
                s_df, count, _ = degerleri_donustur(sogutma_df)
                st.write(f"Değiştirilen: {count}")
                st.dataframe(s_df.head(10))
                st.download_button("Soğutma Excel İndir", to_excel(s_df), f"Sogutma_{datetime.now().day}.xlsx")
            else:
                st.warning("Soğutma verisi bulunamadı.")

if __name__ == '__main__':
    main()
