from typing import Optional

from ollama import chat
from pydantic import BaseModel


class ReceiptAIResult(BaseModel):
    company: Optional[str] = None
    receipt_no: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    kdv: Optional[float] = None
    total: Optional[float] = None


class LocalAIParser:
    def __init__(self, model_name="qwen3:4b"):
        self.model_name = model_name

    def parse(self, texts):
        ocr_text = "\n".join(texts)

        prompt = f"""

Sen Türkçe ve Kuzey Kıbrıs mali fişlerinden yapılandırılmış veri çıkaran

bir muhasebe veri çıkarma sistemisin.

Aşağıdaki metin PaddleOCR tarafından bir fişten satır sırası korunarak okunmuştur.

YALNIZCA OCR metninde bulunan bilgilere dayan.

Tahmin etme, yeni bilgi üretme ve firma adını düzeltmeye çalışma.

ÇIKARILACAK ALANLAR:

1. company

- company değeri OCR METNİNDE BULUNAN TEK BİR SATIR olmalıdır.

- Birden fazla OCR satırını birleştirerek firma adı oluşturma.

- Firma adını genişletme veya eksik gördüğün kısmı başka satırlardan tamamlama.

- Örneğin OCR'da ayrı satırlar halinde:

  MIGROS

  TICARET PERLA VISTA

  BEYKENT MIGROS MAGAZASI

  bulunuyorsa company için sadece gerçek firma adı satırını kullan.

  Satırları birleştirip yeni bir firma adı üretme.

- OCR'da şirket adı "TEKPA" şeklinde tek satırsa,

  company değerini daha uzun bir şirket adına dönüştürme.

- "E-ARSIV FATURA", "MALI DEGERI YOK" gibi belge başlıklarını
  company olarak kullanma.

- Fişi düzenleyen işletmenin/firmanın adıdır.

- Genellikle ilk satırlardadır.

- OCR metninde nasıl yazıyorsa mümkün olduğunca aynen kullan.

- Firma adını tercüme etme, yeniden yazma veya tamamlamaya çalışma.

2. receipt_no

- YALNIZCA fiş numarasını çıkar.

- Fiş numarası için öncelikle şu etiketleri ara:

  "FIS NO"

  "FİŞ NO"

  "Fis No"

  "FISNO"

- Bu etiketin yanında bulunan numarayı kullan.

- Baştaki sıfırları koru.

ÇOK ÖNEMLİ:

- "V.NO", "V NO", "VERGI NO", "VERGİ NO", "V.D.", "VD"

  ifadelerinin yanında bulunan numaralar VERGİ NUMARASIDIR.

- Vergi numarasını receipt_no olarak ASLA kullanma.

- Etiketsiz uzun numaraları receipt_no olarak kullanma.

Örnek:

OCR:

GIRNE V.D. V.NO : M$15509

00000015509

FIS NO: 0269

Doğru:

receipt_no = "0269"

Yanlış:

receipt_no = "00000015509"
3. date

- İşlem tarihidir.

- GG-AA-YYYY, GG/AA/YYYY veya GG.AA.YYYY formatında olabilir.

- OCR'daki mevcut formatı koru.

4. time

- "SAAT" veya "Saat" ifadesinin yanındaki işlem saatidir.

- Çıktıyı HH:MM formatında döndür.

- Örnek:

  "SAAT 18:17" -> "18:17"

  "SAAT : 19:03:24" -> "19:03"

5. total

TOPLAM DEĞERİNİ KDV'DEN ÖNCE BELİRLE.

- Nihai toplam, müşterinin ödediği toplam tutardır.

- Öncelikli etiketler:

  "TOPLAM"

  "GENEL TOPLAM"

  "TOP"

  "ÖDENECEK"

  "ÖDENECEK TUTAR"

- Etiketin hemen öncesindeki veya hemen sonrasındaki para tutarına bak.

- Ödeme yöntemi satırlarının yanındaki aynı tutar da toplamı doğrulayabilir:

  "NAKIT"

  "NAKİT"

  "KREDI KARTI"

  "KREDİ KARTI"

- "ARATOPLAM" nihai toplam değildir.

- Ürün satırlarındaki miktar, birim fiyat veya satır toplamlarını

  genel toplam olarak kullanma.

- Çarpım içeren satırlar ürün bilgisidir:

  "1,850 X 59,99"

  "0,680 X 39,99"

  "2 ADET X 65,00 TL"

  Bunları total olarak kullanma.

6. kdv

TOTAL DEĞERİNİ BELİRLEDİKTEN SONRA KDV'Yİ BUL.

- KDV etiketleri:

  "KDV"

  "TOPKDV"

  "TOP KDV"

  "TOPLAM KDV"

- KDV tutarı genellikle bu etiketin hemen öncesindeki

  veya hemen sonrasındaki para tutarıdır.

- KDV yüzdesini tutar sanma:

  "%00", "%05", "%10", "%20" gibi değerler KDV tutarı değildir.

- KDV tutarı total değerinden küçük olmalıdır.

- Bir KDV etiketinin iki yanında iki para tutarı varsa ve bunlardan biri

  daha önce belirlenen total değerine eşitse, total değerine eşit olmayan

  ve totalden küçük olan tutarı KDV olarak seç.

ÖRNEK:

OCR:

*12,85

KDV

*623,16

*623,16

TOP

NAKIT

Doğru:

kdv = 12.85

total = 623.16

ÖRNEK:

OCR:

*121,84

TOPKDV

*869,99

TOPLAM

*869,99

Doğru:

kdv = 121.84

total = 869.99

ÖRNEK:

OCR:

*1.800,00

KDV

*163,64

TOPLAM

*1.800,00

Doğru:

kdv = 163.64

total = 1800.00

PARA FORMATI KURALLARI:

Türkçe sayı biçimini doğru dönüştür:

"12,85" -> 12.85

"623,16" -> 623.16

"869,99" -> 869.99

"1.800,00" -> 1800.00

Virgülü silerek "12,85" değerini 1285 yapma.

Yıldız, TL ve benzeri sembolleri çıkar.

GÜVENLİK KURALLARI:

- Bilgiyi tahmin etme.

- Bulamadığın alanı null bırak.

- Aynı değeri sebepsiz şekilde hem KDV hem total olarak kullanma.

- Emin değilsen null döndürmek yanlış bir değer döndürmekten daha iyidir.

- Sadece istenen yapıdaki alanları döndür.

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

        return ReceiptAIResult.model_validate_json(content)