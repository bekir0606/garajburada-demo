import stripe
import sqlite3
from fastapi import APIRouter, Request, Header, HTTPException

router = APIRouter()
DB_PATH = "../database/database.db"
stripe.api_key = "sk_test_1234567890"  # test key

WEBHOOK_SECRET = "whsec_test_abc123"  # Test Webhook Secret

@router.post("/api/payment/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Webhook imzası doğrulanamadı")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        product_name = session["display_items"][0]["custom"]["name"]
        customer_email = session.get("customer_email", "N/A")

        # örnek: ürün adına göre veri işleme (gerçek sistemde session metadata kullanılmalı)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE Listings SET Status = 'approved' WHERE Title = ?", (product_name,))
        conn.commit()
        conn.close()
        print(f"✔️ İlan '{product_name}' onaylandı (ödeme alındı)")

    return {"status": "success"}
