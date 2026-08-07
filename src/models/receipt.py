class Receipt:
    def __init__(
        self,
        company=None,
        receipt_no=None,
        date=None,
        time=None,
        kdv=None,
        total=None
    ):
        self.company = company
        self.receipt_no = receipt_no
        self.date = date
        self.time = time
        self.kdv = kdv
        self.total = total

    def __str__(self):
        return (
            f"Firma: {self.company}\n"
            f"Fiş No: {self.receipt_no}\n"
            f"Tarih: {self.date}\n"
            f"Saat: {self.time}\n"
            f"KDV: {self.kdv}\n"
            f"Toplam: {self.total}"
        )