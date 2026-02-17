import streamlit as st
import pandas as pd
import json
import os

# --- AYARLARIN YÖNETİMİ ---
CONFIG_FILE = 'sayac_ayarlari.json'

def ayarları_yukle():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "sifre": "1234",
        "set_degerleri": {
            "Danfos": {"Isıtma": 0, "Soğutma": 0, "Kul. Su": 23},
            "Minol": {"Isıtma": 0, "Soğutma": 0, "Kul. Su": 23},
            "Danfos Yeni": {"Kul. Su": 23},
            "Danfos Minol Grup": {"Kul. Su": 23}
        }
    }

def ayarları_kaydet(ayarlar):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=4)

# Uygulama Başlatma
ayarlar = ayarları_yukle()

st.set_page_config(page_title="Site Sayaç Yönetim Sistemi", layout="wide")
st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu")

# --- ŞİFRE PANELİ ---
with st.sidebar:
    st.header("Yönetici Girişi")
    girilen_sifre = st.text_input("Sistem Şifresi", type="password")

if girilen_sifre == ayarlar["sifre"]:
    st.success("Yönetici Erişimi Aktif")
    
    # --- AYARLAR SEKİSİ ---
    tab1, tab2 = st.tabs(["📊 Veri İşleme", "⚙️ Set Değerlerini Ayarla"])
    
    with tab2:
        st.subheader("Bölümlere Göre Değer Tanımlama")
        yeni_set = ayarlar["set_degerleri"].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("Danfos Grubu")
            yeni_set["Danfos"]["Isıtma"] = st.number_input("Danfos Isıtma", value=ayarlar["set_degerleri"]["Danfos"]["Isıtma"])
            yeni_set["Danfos"]["Soğutma"] = st.number_input("Danfos Soğutma", value=ayarlar["set_degerleri"]["Danfos"]["Soğutma"])
            yeni_set["Danfos"]["Kul. Su"] = st.number_input("Danfos Kul. Su", value=ayarlar["set_degerleri"]["Danfos"]["Kul. Su"])
            
            st.info("Minol Grubu")
            yeni_set["Minol"]["Isıtma"] = st.number_input("Minol Isıtma", value=ayarlar["set_degerleri"]["Minol"]["Isıtma"])
            yeni_set["Minol"]["Soğutma"] = st.number_input("Minol Soğutma", value=ayarlar["set_degerleri"]["Minol"]["Soğutma"])
            yeni_set["Minol"]["Kul. Su"] = st.number_input("Minol Kul. Su", value=ayarlar["set_degerleri"]["Minol"]["Kul. Su"])

        with col2:
            st.info("Danfos Yeni Grubu")
            yeni_set["Danfos Yeni"]["Kul. Su"] = st.number_input("Danfos Yeni Kul. Su", value=ayarlar["set_degerleri"]["Danfos Yeni"]["Kul. Su"])
            
            st.info("Danfos Minol Grup")
            yeni_set["Danfos Minol Grup"]["Kul. Su"] = st.number_input("Grup Kul. Su", value=ayarlar["set_degerleri"]["Danfos Minol Grup"]["Kul. Su"])
            
            st.warning("Erişim Ayarları")
            yeni_sifre = st.text_input("Şifreyi Değiştir (Boş bırakırsanız aynı kalır)", type="password")

        if st.button("Tüm Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            if yeni_sifre:
                ayarlar["sifre"] = yeni_sifre
            ayarları_kaydet(ayarlar)
            st.success("Ayarlar sisteme kaydedildi ve kalıcı hale getirildi!")

    with tab1:
        st.subheader("Sayaç Dosyasını İşle")
        uploaded_file = st.file_uploader("Otomatik kaydedilen Excel dosyasını buraya yükleyin", type=['xlsx'])

        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            st.write("Ham Veri Önizleme:", df.head())

            if st.button("Verileri Ayrıştır ve 3 Excel Oluştur"):
                # İşlem Fonksiyonu
                def deger_ata(row):
                    grup = row['Grup'] # Sütun adınız 'Grup' olmalı
                    tip = row['Tip']   # Sütun adınız 'Tip' olmalı
                    
                    if grup in ayarlar["set_degerleri"]:
                        if tip in ayarlar["set_degerleri"][grup]:
                            return ayarlar["set_degerleri"][grup][tip]
                    return row['Deger'] # Eğer eşleşme yoksa eski değeri koru

                # Kuralları Uygula
                df['Yeni_Deger'] = df.apply(deger_ata, axis=1)

                # 3 Ayrı DataFrame Oluştur
                isitma = df[df['Tip'] == 'Isıtma']
                sogutma = df[df['Tip'] == 'Soğutma']
                kullanim_suyu = df[df['Tip'] == 'Kul. Su']

                # İndirme Butonları
                st.divider()
                st.subheader("📥 Hazırlanan Dosyaları İndir")
                
                c1, c2, c3 = st.columns(3)
                c1.download_button("Isıtma Excelini İndir", isitma.to_csv(index=False).encode('utf-8-sig'), "Isitma.csv", "text/csv")
                c2.download_button("Soğutma Excelini İndir", sogutma.to_csv(index=False).encode('utf-8-sig'), "Sogutma.csv", "text/csv")
                c3.download_button("Kullanım Suyu Excelini İndir", kullanim_suyu.to_csv(index=False).encode('utf-8-sig'), "Kullanim_Suyu.csv", "text/csv")
                
                st.balloons()

else:
    st.warning("🔐 Lütfen işlem yapmak için geçerli yönetici şifresini giriniz.")
