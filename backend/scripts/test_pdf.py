import sys
sys.path.insert(0, '/root/InvoiceAuditAgent/backend')
from pypdf import PdfReader
import os

pdf_path = "/root/InvoiceAuditAgent/backend/uploads/5855e7b1-d9a5-4d50-9acd-4a2c967f90ec/extracted"

for f in os.listdir(pdf_path):
    if f.endswith('.pdf'):
        full_path = os.path.join(pdf_path, f)
        try:
            reader = PdfReader(full_path)
            print(f"File: {f}, Pages: {len(reader.pages)}")
            text = reader.pages[0].extract_text()
            print(f"  Text preview: {text[:100] if text else 'None'}")
        except Exception as e:
            print(f"File: {f}, Error: {e}")
