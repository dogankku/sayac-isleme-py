
SAYAÇ VERİ İŞLEME PROGRAMI v2.0
55 Katlı 2 Bloklu Site - Isıtma ve Soğutma Sayaçları

Özellikler:

- Tab-delimited XLS/XLSX dosyalarını okur
- Isıtma ve soğutma verilerini ayrı dosyalara ayırır
- Değer dönüşümü yapar (00→09, 01→00)
  “””

import pandas as pd
import os
import subprocess
from datetime import datetime

def xls_to_xlsx(xls_path, output_dir=’/home/claude’):
“”“XLS dosyasını XLSX formatına dönüştürür”””
print(f”🔄 XLS → XLSX dönüşümü yapılıyor…”)

```
try:
    cmd = [
        'soffice', '--headless', '--convert-to', 'xlsx',
        '--outdir', output_dir, xls_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Çıktı dosya adını oluştur
    base_name = os.path.basename(xls_path)
    xlsx_name = base_name.rsplit('.', 1)[0] + '.xlsx'
    xlsx_path = os.path.join(output_dir, xlsx_name)
    
    if os.path.exists(xlsx_path):
        print(f"✅ Dönüştürme başarılı: {xlsx_path}")
        return xlsx_path
    else:
        print("❌ Dönüştürme başarısız!")
        return None
        
except Exception as e:
    print(f"❌ Hata: {e}")
    return None
```

def dosya_oku(dosya_yolu):
“””
Tab-delimited Excel dosyasını okur ve düzgün DataFrame’e dönüştürür

```
Args:
    dosya_yolu: Excel dosyasının yolu
    
Returns:
    DataFrame veya None
"""
try:
    print(f"\n📂 Dosya okunuyor: {dosya_yolu}")
    
    # XLS ise önce XLSX'e dönüştür
    if dosya_yolu.lower().endswith('.xls'):
        xlsx_path = xls_to_xlsx(dosya_yolu)
        if xlsx_path:
            dosya_yolu = xlsx_path
        else:
            return None
    
    # Excel dosyasını oku
    df_raw = pd.read_excel(dosya_yolu, engine='openpyxl')
    
    # İlk sütundaki tab-delimited veriyi ayır
    first_col = df_raw.iloc[:, 0]
    split_data = first_col.str.split('\t', expand=True)
    
    # Sütun adlarını belirle
    headers = ['Tanımlama', 'Aygıt', 'Değer', 'Orta', 'Birincil adres', 
               'İkincil adres', 'Üretim', 'Yapımcı', 'Aygıt durumu', 'Birim', 'Tarih']
    
    df = split_data.copy()
    df.columns = headers[:len(df.columns)]
    
    print(f"✅ Dosya başarıyla okundu! Toplam {len(df)} satır var.")
    print(f"📋 Sütunlar: {list(df.columns)}")
    
    return df
    
except Exception as e:
    print(f"❌ Hata: Dosya okunamadı - {e}")
    return None
```

def verileri_ayir(df):
“””
Isıtma ve soğutma verilerini ayırır

```
Args:
    df: Ana DataFrame
    
Returns:
    (isitma_df, sogutma_df) tuple
"""
try:
    print("\n🔄 Veriler ayrılıyor...")
    
    # Isıtma verilerini filtrele (ISITMA kelimesini ara)
    isitma_mask = df['Tanımlama'].str.contains('ISITMA', case=False, na=False)
    isitma_df = df[isitma_mask].copy()
    
    # Soğutma verilerini filtrele (unicode karakterli soğutma kelimesi)
    # "SO�UTMA" veya "SOĞUTMA" veya "SOGUTMA"
    sogutma_mask = (
        df['Tanımlama'].str.contains('SO', case=False, na=False) & 
        df['Tanımlama'].str.contains('UTMA', case=False, na=False) &
        ~isitma_mask  # ISITMA olmayanlar
    )
    sogutma_df = df[sogutma_mask].copy()
    
    print(f"✅ Isıtma kayıtları: {len(isitma_df)}")
    print(f"✅ Soğutma kayıtları: {len(sogutma_df)}")
    
    return isitma_df, sogutma_df
    
except Exception as e:
    print(f"❌ Hata: Veriler ayrılamadı - {e}")
    return None, None
```

def degerleri_donustur(df, deger_sutunu=‘Değer’):
“””
Değer sütunundaki verileri dönüştürür
00 → 09
01 → 00

```
Args:
    df: İşlenecek DataFrame
    deger_sutunu: Değer sütununun adı
    
Returns:
    Dönüştürülmüş DataFrame
"""
try:
    df_copy = df.copy()
    
    def deger_donustur_func(deger):
        """Tek bir değeri dönüştürür"""
        if pd.isna(deger):
            return deger
        
        deger_str = str(deger).strip()
        
        # Dönüşüm kuralları
        if deger_str == '00':
            return '09'
        elif deger_str == '01':
            return '00'
        else:
            return deger
    
    # Değer sütununu dönüştür
    if deger_sutunu in df_copy.columns:
        onceki = df_copy[deger_sutunu].copy()
        df_copy[deger_sutunu] = df_copy[deger_sutunu].apply(deger_donustur_func)
        
        # Kaç değer değişti
        degisen = (onceki != df_copy[deger_sutunu]).sum()
        return df_copy, degisen
    else:
        print(f"⚠️  '{deger_sutunu}' sütunu bulunamadı!")
        return df_copy, 0
        
except Exception as e:
    print(f"❌ Hata: Değerler dönüştürülemedi - {e}")
    return df, 0
```

def dosyalari_kaydet(isitma_df, sogutma_df, cikti_klasoru=’/mnt/user-data/outputs’):
“””
İşlenmiş verileri ayrı Excel dosyalarına kaydeder

```
Args:
    isitma_df: Isıtma verileri
    sogutma_df: Soğutma verileri
    cikti_klasoru: Çıktı klasörü
"""
try:
    os.makedirs(cikti_klasoru, exist_ok=True)
    
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    kayit_listesi = []
    
    print(f"\n💾 Dosyalar kaydediliyor...")
    
    # Isıtma dosyası
    if isitma_df is not None and len(isitma_df) > 0:
        isitma_dosya = os.path.join(cikti_klasoru, f'A_Blok_Isitma_{zaman_damgasi}.xlsx')
        isitma_df.to_excel(isitma_dosya, index=False, engine='openpyxl')
        print(f"  ✅ Isıtma: {os.path.basename(isitma_dosya)} ({len(isitma_df)} kayıt)")
        kayit_listesi.append(isitma_dosya)
    
    # Soğutma dosyası
    if sogutma_df is not None and len(sogutma_df) > 0:
        sogutma_dosya = os.path.join(cikti_klasoru, f'A_Blok_Sogutma_{zaman_damgasi}.xlsx')
        sogutma_df.to_excel(sogutma_dosya, index=False, engine='openpyxl')
        print(f"  ✅ Soğutma: {os.path.basename(sogutma_dosya)} ({len(sogutma_df)} kayıt)")
        kayit_listesi.append(sogutma_dosya)
    
    return kayit_listesi
    
except Exception as e:
    print(f"❌ Hata: Dosyalar kaydedilemedi - {e}")
    return []
```

def main():
“”“Ana fonksiyon”””

```
print("=" * 80)
print("🏢 SAYAÇ VERİ İŞLEME PROGRAMI v2.0")
print("=" * 80)

# Dosya yolu
dosya_yolu = '/mnt/user-data/uploads/a_blok_ısıtma.XLS'

# 1. Dosyayı oku
df = dosya_oku(dosya_yolu)
if df is None:
    print("\n❌ Program sonlandırıldı: Dosya okunamadı!")
    return

# 2. Verileri ayır
isitma_df, sogutma_df = verileri_ayir(df)
if isitma_df is None and sogutma_df is None:
    print("\n❌ Program sonlandırıldı: Veriler ayrılamadı!")
    return

# 3. Değerleri dönüştür
print("\n🔄 Değerler dönüştürülüyor (00→09, 01→00)...")

if isitma_df is not None and len(isitma_df) > 0:
    isitma_df, isitma_degisen = degerleri_donustur(isitma_df)
    print(f"  📊 Isıtma: {isitma_degisen} değer değiştirildi")

if sogutma_df is not None and len(sogutma_df) > 0:
    sogutma_df, sogutma_degisen = degerleri_donustur(sogutma_df)
    print(f"  📊 Soğutma: {sogutma_degisen} değer değiştirildi")

# 4. Dosyaları kaydet
kayit_listesi = dosyalari_kaydet(isitma_df, sogutma_df)

if kayit_listesi:
    print("\n" + "=" * 80)
    print("🎉 TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI!")
    print("=" * 80)
    print(f"\n📁 {len(kayit_listesi)} dosya oluşturuldu:")
    for dosya in kayit_listesi:
        print(f"  • {os.path.basename(dosya)}")
else:
    print("\n⚠️  Dosya kaydedilemedi!")
```

if **name** == ‘**main**’:
main()
