import sys
sys.path.insert(0, '/root/InvoiceAuditAgent/backend')
from app.services.ai_service import ai_service
import asyncio
import os

pdf_path = "/root/InvoiceAuditAgent/backend/uploads/5855e7b1-d9a5-4d50-9acd-4a2c967f90ec/extracted"

async def test():
    for f in sorted(os.listdir(pdf_path)):
        if f.endswith('.pdf'):
            full_path = os.path.join(pdf_path, f)
            print(f"\n=== Testing: {f} ===")
            try:
                result = await ai_service.extract_invoice_info(full_path)
                print(f"Invoice number: {result.get('invoice_number')}")
                print(f"Seller: {result.get('seller_name')}")
                print(f"Buyer: {result.get('buyer_name')}")
                print(f"Total: {result.get('total_amount')}")
                print(f"Source: {result.get('_source', 'unknown')}")
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(test())
