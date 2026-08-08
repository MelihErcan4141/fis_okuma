from typing import Optional

from ollama import chat
from pydantic import BaseModel
from services.ai_cache import AICache


class ReceiptAIResult(BaseModel):
    company: Optional[str] = None
    receipt_no: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    kdv: Optional[float] = None
    total: Optional[float] = None


class LocalAIParser:
    PROMPT_VERSION = "v1"
    def __init__(
    self,
    model_name="qwen3:4b"
    ):
      self.model_name = model_name

      self.cache = AICache()

      self.cache_hits = 0
      self.cache_misses = 0

    def parse(self, texts):
        cached_result = self.cache.load(
            self.model_name,
            self.PROMPT_VERSION,
            texts
        )

        if cached_result is not None:
            self.cache_hits += 1

            return ReceiptAIResult.model_validate(
                cached_result
            )

        self.cache_misses += 1

        ocr_text = "\n".join(texts)

        prompt = f"""
+Türkçe ve Kuzey Kıbrıs mali fiş OCR metninden şu alanları çıkar:
 
-Sen Türkçe ve Kuzey Kıbrıs mali fişlerinden yapılandırılmış veri çıkaran
+company, receipt_no, date, time, kdv, total.
 
-bir muhasebe veri çıkarma sistemisin.
+Yalnızca OCR metnindeki bilgileri kullan. Tahmin etme.
 
-Aşağıdaki metin PaddleOCR tarafından bir fişten satır sırası korunarak okunmuştur.
+Bulamadığın veya emin olmadığın alanı null bırak.
 
-YALNIZCA OCR metninde bulunan bilgilere dayan.
+KURALLAR:
 
-Tahmin etme, yeni bilgi üretme ve firma adını düzeltmeye çalışma.
...skipping...
 
-Sen Türkçe ve Kuzey Kıbrıs mali fişlerinden yapılandırılmış veri çıkaran
+company, receipt_no, date, time, kdv, total.
 
-bir muhasebe veri çıkarma sistemisin.
+Yalnızca OCR metnindeki bilgileri kullan. Tahmin etme.
 
-Aşağıdaki metin PaddleOCR tarafından bir fişten satır sırası korunarak okunmuştur.
+Bulamadığın veya emin olmadığın alanı null bırak.
 
-YALNIZCA OCR metninde bulunan bilgilere dayan.
+KURALLAR:
 
-Tahmin etme, yeni bilgi üretme ve firma adını düzeltmeye çalışma.
+company:
 
-ÇIKARILACAK ALANLAR:
+- Fişi düzenleyen işletmenin adıdır.
 
-1. company
+- OCR'da bulunan TEK BİR SATIRI kullan.
 
-- company değeri OCR METNİNDE BULUNAN TEK BİR SATIR olmalıdır.
+- Birden fazla satırı birleştirme.
 
-- Birden fazla OCR satırını birleştirerek firma adı oluşturma.
+- Firma adını düzeltme, genişletme veya tamamlama.
 
-- Firma adını genişletme veya eksik gördüğün kısmı başka satırlardan tamamlama.
-
-- Örneğin OCR'da ayrı satırlar halinde:
-
-  MIGROS
-
-  TICARET PERLA VISTA
-
-  BEYKENT MIGROS MAGAZASI
-
-  bulunuyorsa company için sadece gerçek firma adı satırını kullan.
-
-  Satırları birleştirip yeni bir firma adı üretme.
-
-- OCR'da şirket adı "TEKPA" şeklinde tek satırsa,
-
-  company değerini daha uzun bir şirket adına dönüştürme.
-
-- "E-ARSIV FATURA", "MALI DEGERI YOK" gibi belge başlıklarını
-  company olarak kullanma.
-
-- Fişi düzenleyen işletmenin/firmanın adıdır.
-
-- Genellikle ilk satırlardadır.
-
-- OCR metninde nasıl yazıyorsa mümkün olduğunca aynen kullan.
-
-- Firma adını tercüme etme, yeniden yazma veya tamamlamaya çalışma.
-
-2. receipt_no
-
-- YALNIZCA fiş numarasını çıkar.
-
-- Fiş numarası için öncelikle şu etiketleri ara:
-
-  "FIS NO"
-
-  "FİŞ NO"
-
-  "Fis No"
-
-  "FISNO"
-
-- Bu etiketin yanında bulunan numarayı kullan.
-
-- Baştaki sıfırları koru.
-
-ÇOK ÖNEMLİ:
+- "E-ARSIV FATURA", "MALI DEGERI YOK" gibi belge başlıklarını kullanma.
 
+receipt_no:
+- Yalnızca fiş numarasını çıkar.
+- Öncelikle "FIS NO", "FİŞ NO", "Fis No", "FISNO" etiketini ara.
+- Etiketle AYNI SATIRDA bulunan numarayı receipt_no yap.
+- Baştaki sıfırları mutlaka koru.
+- Örnek: "FIS NO: 0269" -> receipt_no = "0269"
 - "V.NO", "V NO", "VERGI NO", "VERGİ NO", "V.D.", "VD"
-
-  ifadelerinin yanında bulunan numaralar VERGİ NUMARASIDIR.
-
-- Vergi numarasını receipt_no olarak ASLA kullanma.
-
+  yanındaki numaralar vergi numarasıdır; ASLA receipt_no yapma.
 - Etiketsiz uzun numaraları receipt_no olarak kullanma.
 
-Örnek:
-
-OCR:
-
-GIRNE V.D. V.NO : M$15509
-
-00000015509
-
-FIS NO: 0269
-
-Doğru:
-
-receipt_no = "0269"
 
-Yanlış:
+date:
 
-receipt_no = "00000015509"
-3. date
+- İşlem tarihini çıkar.
 
-- İşlem tarihidir.
+- GG-AA-YYYY, GG/AA/YYYY veya GG.AA.YYYY olabilir.
 
-- GG-AA-YYYY, GG/AA/YYYY veya GG.AA.YYYY formatında olabilir.
+- OCR formatını koru.
 
-- OCR'daki mevcut formatı koru.
+time:
 
-4. time
+- "SAAT" veya "Saat" yanındaki işlem saatini çıkar.
 
-- "SAAT" veya "Saat" ifadesinin yanındaki işlem saatidir.
+- HH:MM döndür. Saniye varsa çıkar.
 
-- Çıktıyı HH:MM formatında döndür.
+total:
 
-- Örnek:
+- OCR bazen ondalık ayracını yanlış okuyabilir ve toplamı
+  olduğundan 10 veya 100 kat küçük gösterebilir.
 
-  "SAAT 18:17" -> "18:17"
+- Örneğin OCR'da "1.7" görülse bile fişte toplam bağlamı,
+  ödeme satırı veya diğer tutarlar bunun "170.00" olduğunu
+  açıkça destekliyorsa total = 170.00 seçilebilir.
 
-  "SAAT : 19:03:24" -> "19:03"
+- Bu düzeltmeyi yalnızca güçlü fiş bağlamı varsa yap.
+  Emin değilsen null döndür.
 
-5. total
+- KDV değeri totalden büyük görünüyorsa total değerinde
+  10x veya 100x OCR ölçek hatası ihtimalini kontrol et.
+  
+- "TOP", "TOPLAM", "GENEL TOPLAM", "ÖDENECEK" etiketlerinin
+  hemen öncesindeki veya hemen sonrasındaki para tutarını kontrol et.
 
-TOPLAM DEĞERİNİ KDV'DEN ÖNCE BELİRLE.
+- Toplam etiketten önce gelebilir.
+  Örnek:
+    *623,16
+    TOP
+    NAKIT
+  -> total = 623.16
 
-- Nihai toplam, müşterinin ödediği toplam tutardır.
+- Aynı para tutarı TOP/TOPLAM çevresinde ve NAKIT/KREDI KARTI
+  çevresinde tekrar ediyorsa bu değer total için güçlü adaydır.
 
-- Öncelikli etiketler:
+- "ARATOPLAM" değerini nihai total olarak kullanma.
 
-  "TOPLAM"
+- Önce total değerini belirle.
 
-  "GENEL TOPLAM"
+- Nihai ödenen tutardır.
 
-  "TOP"
+- "TOPLAM", "GENEL TOPLAM", "TOP", "ÖDENECEK",
 
-  "ÖDENECEK"
+  "ÖDENECEK TUTAR" etiketlerinin hemen yakınındaki tutarı kullan.
 
-  "ÖDENECEK TUTAR"
+- "NAKIT", "NAKİT", "KREDI KARTI", "KREDİ KARTI"
 
-- Etiketin hemen öncesindeki veya hemen sonrasındaki para tutarına bak.
-
-- Ödeme yöntemi satırlarının yanındaki aynı tutar da toplamı doğrulayabilir:
-
-  "NAKIT"
-
-  "NAKİT"
-
-  "KREDI KARTI"
-
-  "KREDİ KARTI"
+  satırları toplamı doğrulayabilir.
 
 - "ARATOPLAM" nihai toplam değildir.
 
-- Ürün satırlarındaki miktar, birim fiyat veya satır toplamlarını
-
-  genel toplam olarak kullanma.
-
-- Çarpım içeren satırlar ürün bilgisidir:
-
-  "1,850 X 59,99"
-
-  "0,680 X 39,99"
-
-  "2 ADET X 65,00 TL"
-
-  Bunları total olarak kullanma.
+- Ürün fiyatlarını ve "X" içeren çarpım satırlarını total olarak kullanma.
+- KDV etiketinin çevresinde iki para tutarı varsa ve bunlardan biri
+  total adayı olarak tekrar ediyorsa, tekrar eden büyük değer total,
+  diğer küçük değer KDV olabilir.
 
-6. kdv
-
-TOTAL DEĞERİNİ BELİRLEDİKTEN SONRA KDV'Yİ BUL.
-
-- KDV etiketleri:
-
-  "KDV"
-
-  "TOPKDV"
-
-  "TOP KDV"
-
-  "TOPLAM KDV"
-
-- KDV tutarı genellikle bu etiketin hemen öncesindeki
-
-  veya hemen sonrasındaki para tutarıdır.
-
-- KDV yüzdesini tutar sanma:
-
-  "%00", "%05", "%10", "%20" gibi değerler KDV tutarı değildir.
-
-- KDV tutarı total değerinden küçük olmalıdır.
-
-- Bir KDV etiketinin iki yanında iki para tutarı varsa ve bunlardan biri
-
-  daha önce belirlenen total değerine eşitse, total değerine eşit olmayan
-
-  ve totalden küçük olan tutarı KDV olarak seç.
-
-ÖRNEK:
-
-OCR:
-
-*12,85
-
-KDV
-
-*623,16
-
-*623,16
-
-TOP
-
-NAKIT
-
-Doğru:
-
-kdv = 12.85
-
-total = 623.16
-
-ÖRNEK:
-
-OCR:
-
-*121,84
-
-TOPKDV
-
-*869,99
-
-TOPLAM
-
-*869,99
-
-Doğru:
-
-kdv = 121.84
-
-total = 869.99
-
-ÖRNEK:
-
-OCR:
-
-*1.800,00
-
-KDV
-
-*163,64
-
-TOPLAM
-
-*1.800,00
+Örnek:
+  *12,85
+  KDV
+  *623,16
+  *623,16
+  TOP
+  NAKIT
 
-Doğru:
+Sonuç:
+  kdv = 12.85
+  total = 623.16
+kdv:
 
-kdv = 163.64
+- Total belirlendikten sonra KDV'yi bul.
 
-total = 1800.00
+- "KDV", "TOPKDV", "TOP KDV", "TOPLAM KDV"
 
-PARA FORMATI KURALLARI:
+  etiketlerinin hemen yakınındaki KDV tutarını kullan.
 
-Türkçe sayı biçimini doğru dönüştür:
+- %00, %05, %10, %20 gibi oranları KDV tutarı sanma.
 
-"12,85" -> 12.85
+- KDV totalden küçük olmalıdır.
 
-"623,16" -> 623.16
+- KDV etiketinin iki yanında tutar varsa ve biri total ise,
 
-"869,99" -> 869.99
+  diğer totalden küçük tutarı KDV olarak seç.
 
-"1.800,00" -> 1800.00
+Para:
 
-Virgülü silerek "12,85" değerini 1285 yapma.
+- Türkçe para biçimini sayıya doğru çevir.
 
-Yıldız, TL ve benzeri sembolleri çıkar.
+- 12,85 -> 12.85
 
-GÜVENLİK KURALLARI:
+- 1.800,00 -> 1800.00
 
-- Bilgiyi tahmin etme.
+- Yıldız ve TL gibi sembolleri çıkar.
 
-- Bulamadığın alanı null bırak.
+ÖNEMLİ:
 
-- Aynı değeri sebepsiz şekilde hem KDV hem total olarak kullanma.
+- Aynı değeri sebepsiz yere hem kdv hem total yapma.
 
-- Emin değilsen null döndürmek yanlış bir değer döndürmekten daha iyidir.
+- Emin değilsen null döndür.
 
-- Sadece istenen yapıdaki alanları döndür.
+- Yalnızca istenen yapıdaki alanları döndür.
 
 OCR METNİ:
{ocr_text}
"""

        response = chat(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format=ReceiptAIResult.model_json_schema(),
            think=False,
            options={
                "temperature": 0
            }
        )

        content = response.message.content

        if not content or not content.strip():
              raise RuntimeError(
                  "Local AI boş cevap döndürdü. "
                  "Ollama/Qwen3 cevabı üretilemedi."
              )

        result = ReceiptAIResult.model_validate_json(
            content
        )

        self.cache.save(
            self.model_name,
            self.PROMPT_VERSION,
            texts,
            result.model_dump()
        )

        return result