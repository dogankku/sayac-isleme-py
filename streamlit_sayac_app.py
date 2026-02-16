#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sayac Veri Isleme Programi - Streamlit Versiyonu
55 Katli 2 Bloklu Site - Isitma ve Sogutma Sayaclari

Ozellikler:
- Tab-delimited XLS/XLSX dosyalarini okur
- Isitma ve sogutma verilerini ayri dosyalara ayirir
- Deger donusumu yapar (00->09, 01->00)
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
    Tab-delimited Excel dosyasini okur ve DataFrame’e donusturur
    """
    try:
        # Excel dosyasını oku
        df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # İlk sütundaki tab-delimited veriyi ayır
        first_col = df_raw.iloc[:, 0]
        split_data = first_col.str.split('\t', expand=True)
        
        # Sütun adlarını belirle
        headers = ['Tanımlama', 'Aygıt', 'Değer', 'Orta', 'Birincil adres', 
                   'İkincil adres', 'Üretim', 'Yapımcı', 'Aygıt durumu', 'Birim', 'Tarih']
        
        df = split_data.copy()
        df.columns = headers[:len(df.columns)]
        
        return df, None
        
    except Exception as e:
        return None, str(e)

def verileri_ayir(df):
    """
    Isitma ve sogutma verilerini ayirir
    """
    try:
        # Isıtma verilerini filtrele
        isitma_mask = df['Tanımlama'].str.contains('ISITMA', case=False, na=False)
        isitma_df = df[isitma_mask].copy()

        # Soğutma verilerini filtrele
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
    Deger sutunundaki verileri donusturur
    00 -> 09
    01 -> 00
    """
    try:
        df_copy = df.copy()

        def deger_donustur_func(deger):
            if pd.isna(deger):
                return deger
            
            deger_str = str(deger).strip()
            
            if deger_str == '00':
                return '09'
            elif deger_str == '01':
                return '00'
            else:
                return deger
        
        if deger_sutunu in df_copy.columns:
            onceki = df_copy[deger_sutunu].copy()
            df_copy[deger_sutunu] = df_copy[deger_sutunu].apply(deger_donustur_func)
            
            degisen = (onceki != df_copy[deger_sutunu]).sum()
            return df_copy, degisen, None
        else:
            return df_copy, 0, f"'{deger_sutunu}' sutunu bulunamadi!"
            
    except Exception as e:
        return df, 0, str(e)

def to_excel(df):
    """
    DataFrame’i Excel dosyasina donusturur (bellekte)
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def main():
    st.title("🏢 Sayaç Veri İşleme Programı")
    st.markdown("---")

    # Sidebar bilgileri
    with st.sidebar:
        st.header("ℹ️ Bilgi")
        st.info("""
        **Program Özellikleri:**
        - XLS/XLSX dosyalarını okur
        - Isıtma ve soğutma verilerini ayırır
        - Değer dönüşümü yapar:
          - 00 → 09
          - 01 → 00
        """)
        
        st.markdown("---")
        st.markdown("**Versiyon:** 2.0 Streamlit")

    # Dosya yükleme
    st.header("📁 1. Dosya Yükleme")
    uploaded_file = st.file_uploader(
        "Excel dosyanızı yükleyin (XLS veya XLSX)",
        type=['xls', 'xlsx'],
        help="Sayaç verilerini içeren Excel dosyanızı seçin"
    )

    if uploaded_file is not None:
        # Dosya bilgileri
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dosya Adı", uploaded_file.name)
        with col2:
            st.metric("Dosya Boyutu", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Dosya Tipi", uploaded_file.type.split('/')[-1].upper())
        
        st.markdown("---")
        
        # Dosyayı işle
        with st.spinner("Dosya okunuyor..."):
            df, error = parse_excel_file(uploaded_file)
        
        if error:
            st.error(f"❌ Hata: {error}")
            return
        
        st.success(f"✅ Dosya başarıyla okundu! Toplam {len(df)} satır var.")
        
        # Ham veriyi göster
        with st.expander("🔍 Ham Veriyi Görüntüle"):
            st.dataframe(df.head(20), use_container_width=True)
        
        st.markdown("---")
        
        # Verileri ayır
        st.header("📊 2. Veri Ayrıştırma")
        
        with st.spinner("Veriler ayrılıyor..."):
            isitma_df, sogutma_df, error = verileri_ayir(df)
        
        if error:
            st.error(f"❌ Hata: {error}")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔥 Isıtma Kayıtları", len(isitma_df))
        with col2:
            st.metric("❄️ Soğutma Kayıtları", len(sogutma_df))
        
        st.markdown("---")
        
        # Değer dönüşümü
        st.header("🔄 3. Değer Dönüşümü")
        donusum_yap = st.checkbox("Değer dönüşümünü uygula (00→09, 01→00)", value=True)
        
        if donusum_yap:
            isitma_degisen = 0
            sogutma_degisen = 0
            
            if len(isitma_df) > 0:
                isitma_df, isitma_degisen, error = degerleri_donustur(isitma_df)
            
            if len(sogutma_df) > 0:
                sogutma_df, sogutma_degisen, error = degerleri_donustur(sogutma_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Isıtma: {isitma_degisen} değer değiştirildi")
            with col2:
                st.success(f"✅ Soğutma: {sogutma_degisen} değer değiştirildi")
        
        st.markdown("---")
        
        # Sonuçları görüntüleme
        st.header("📋 4. Sonuçlar")
        tab1, tab2 = st.tabs(["🔥 Isıtma Verileri", "❄️ Soğutma Verileri"])
        
        with tab1:
            if len(isitma_df) > 0:
                st.dataframe(isitma_df, use_container_width=True)
            else:
                st.info("ℹ️ Isıtma verisi bulunamadı.")
        
        with tab2:
            if len(sogutma_df) > 0:
                st.dataframe(sogutma_df, use_container_width=True)
            else:
                st.info("ℹ️ Soğutma verisi bulunamadı.")
        
        st.markdown("---")
        
        # İndirme butonları
        st.header("💾 5. Dosyaları İndir")
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        col1, col2 = st.columns(2)
        
        with col1:
            if len(isitma_df) > 0:
                st.download_button(
                    label="📥 Isıtma Dosyasını İndir",
                    data=to_excel(isitma_df),
                    file_name=f"Isitma_{zaman_damgasi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col2:
            if len(sogutma_df) > 0:
                st.download_button(
                    label="📥 Soğutma Dosyasını İndir",
                    data=to_excel(sogutma_df),
                    file_name=f"Sogutma_{zaman_damgasi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

if __name__ == '__main__':
    main()
