import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter()

stripe.api_key = "sk_test_1234567890"  # Geliştirme için test key

@router.post("/api/payment/create-checkout-session")
async def create_checkout_session(request: Request):
    body = await request.json()
    price = body.get("price")
    title = body.get("title", "İlan Ücreti")
    if not price:
        raise HTTPException(status_code=400, detail="Fiyat zorunludur")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "try",
                    "product_data": {
                        "name": title,
                    },
                    "unit_amount": int(price) * 100,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
