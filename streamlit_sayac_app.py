import streamlit as st
import pandas as pd
import json
import os
import io

# --- AYARLARIN YÖNETİMİ ---
CONFIG_FILE = 'sayac_ayarlari.json'

def ayarları_yukle():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "sifre": "1234",
        "set_degerleri": {
            "Danfos": {"Isıtma": 0, "Soğutma": 24, "Kul. Su": 23},
            "Minol": {"Isıtma": 0, "Soğutma": 24, "Kul. Su": 23},
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
st.title("🏙️ 55 Katlı Site Sayaç Otomasyonu (2026 Formatı)")

# --- ŞİFRE PANELİ ---
with st.sidebar:
    st.header("🔐 Yönetici Girişi")
    girilen_sifre = st.text_input("Sistem Şifresi", type="password")

if girilen_sifre == ayarlar["sifre"]:
    st.success("Yönetici Erişimi Aktif")
    
    tab1, tab2 = st.tabs(["📊 Veri İşleme (Ham Veri -> 2026)", "⚙️ Set Değerlerini Ayarla"])
    
    with tab2:
        st.subheader("Bölümlere Göre Değer Tanımlama")
        yeni_set = ayarlar["set_degerleri"].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("Danfos Grubu (A Blok)")
            yeni_set["Danfos"]["Isıtma"] = st.number_input("Danfos Isıtma Değeri", value=ayarlar["set_degerleri"]["Danfos"]["Isıtma"])
            yeni_set["Danfos"]["Soğutma"] = st.number_input("Danfos Soğutma Değeri", value=ayarlar["set_degerleri"]["Danfos"]["Soğutma"])
            yeni_set["Danfos"]["Kul. Su"] = st.number_input("Danfos Kul. Su Değeri", value=ayarlar["set_degerleri"]["Danfos"]["Kul. Su"])
            
        with col2:
            st.info("Erişim Ayarları")
            yeni_sifre = st.text_input("Şifreyi Değiştir (Boş bırakırsanız aynı kalır)", type="password")

        if st.button("Tüm Ayarları Kaydet"):
            ayarlar["set_degerleri"] = yeni_set
            if yeni_sifre:
                ayarlar["sifre"] = yeni_sifre
            ayarları_kaydet(ayarlar)
            st.success("Ayarlar başarıyla güncellendi!")

    with tab1:
        st.subheader("📥 Sayaç Dosyasını İşle")
        uploaded_file = st.file_uploader("Sistemden alınan Excel dosyasını seçin", type=['xlsx', 'xls'])

        if uploaded_file:
            try:
                # Veriyi Oku
                df = pd.read_excel(uploaded_file)
                
                # Sütun isimlerindeki boşlukları temizle
                df.columns = [str(c).strip() for c in df.columns]
                
                # Görüntüdeki yapıyı tanıyalım: 
                # En sağdaki '########' sütununu 'Endeks' yapalım
                df.rename(columns={df.columns[-1]: 'Endeks'}, inplace=True)
                
                st.write("✅ Dosya başarıyla okundu. Sütunlar:", list(df.columns))
                st.dataframe(df.head(5))

                if st.button("🚀 Verileri Ayrıştır ve 3 Excel Oluştur"):
                    # Veri İşleme Mantığı
                    def filtrele_ve_hazirla(data, deger_kodu):
                        # 'Değer' sütunundaki koda göre filtrele (0, 23, 24 vb.)
                        filtreli = data[data['Değer'] == deger_kodu].copy()
                        # İstenen 2026 formatı için gereksiz sütunları atabilir veya düzenleyebiliriz
                        return filtreli

                    # Ayarlardan gelen değerlere göre ayır
                    isitma_kodu = ayarlar["set_degerleri"]["Danfos"]["Isıtma"]
                    sogutma_kodu = ayarlar["set_degerleri"]["Danfos"]["Soğutma"]
                    su_kodu = ayarlar["set_degerleri"]["Danfos"]["Kul. Su"]

                    df_isitma = filtrele_ve_hazirla(df, isitma_kodu)
                    df_sogutma = filtrele_ve_hazirla(df, sogutma_kodu)
                    df_su = filtrele_ve_hazirla(df, su_kodu)

                    # Excel İndirme Fonksiyonu
                    def to_excel(df_to_save):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_to_save.to_excel(writer, index=False, sheet_name='Sayfa1')
                        return output.getvalue()

                    st.divider()
                    st.subheader("📥 Hazırlanan Dosyaları İndir")
                    
                    c1, c2, c3 = st.columns(3)
                    
                    if not df_isitma.empty:
                        c1.download_button("🔥 Isıtma Exceli", to_excel(df_isitma), "Isitma_Listesi.xlsx")
                        c1.caption(f"{len(df_isitma)} kayıt bulundu.")
                    
                    if not df_sogutma.empty:
                        c2.download_button("❄️ Soğutma Exceli", to_excel(df_sogutma), "Sogutma_Listesi.xlsx")
                        c2.caption(f"{len(df_sogutma)} kayıt bulundu.")
                        
                    if not df_su.empty:
                        c3.download_button("💧 Kullanım Suyu Exceli", to_excel(df_su), "Kullanim_Suyu_Listesi.xlsx")
                        c3.caption(f"{len(df_su)} kayıt bulundu.")
                    
                    st.balloons()

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

else:
    st.warning("🔐 Lütfen işlem yapmak için geçerli yönetici şifresini giriniz.")
    st.info("Varsayılan şifre: 1234")
