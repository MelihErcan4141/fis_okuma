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

Sen Türkçe ve Kuzey Kıbrıs fişlerini analiz eden bir muhasebe veri çıkarma sistemisin.

Aşağıdaki metin OCR ile bir fişten okunmuştur.

OCR hataları olabilir ama yalnızca metinde gerçekten bulunan bilgilere dayanmalısın.

Alanları şu kurallara göre çıkar:

- company:

  Genellikle fişin ilk satırlarında bulunan firma/işletme adıdır.

  LTD, AŞ, ŞTİ, MARKET, PETROL gibi ifadeler içerebilir.

- receipt_no:

  "FIS NO", "FİŞ NO", "FISNO" gibi ifadelerin yanında bulunan numaradır.

- date:

  GG-AA-YYYY, GG/AA/YYYY veya GG.AA.YYYY formatındaki işlem tarihidir.

- time:

  "SAAT" kelimesinin yanında bulunan HH:MM biçimindeki saattir.

- kdv:

  "KDV" kelimesine en yakın toplam vergi tutarıdır.

  Ürün satırlarındaki yüzde değerlerini (%00, %05 vb.) KDV tutarı sanma.

  KDV satırındaki para tutarını kullan.

- total:

  "TOPLAM", "TOP", "NAKIT", "NAKİT" gibi ödeme/toplam ifadelerine yakın olan

  müşterinin ödediği nihai tutardır.

Kurallar:
- Firma adını tercüme etme, yeniden yazma veya anlamını değiştirme.

  OCR metnindeki firma adını mümkün olduğunca aynen kullan.

- "TOPKDV", "TOP KDV" veya "TOPLAM KDV" ifadelerine yakın tutar

  toplam KDV tutarıdır.

- "TOPLAM", "GENEL TOPLAM" gibi ifadelerin yanındaki tutar

  müşterinin ödediği nihai toplamdır.

- KDV ile toplam tutarı birbirine karıştırma.

- Tahmin etme.

- Bulamadığın alanı null bırak.

- Para tutarlarını float olarak döndür.

- Yıldız, TL, virgül gibi karakterleri temizle.

- OCR'da "TOPLAM" yerine sadece "TOP" yazılmış olabilir.

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