import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import CosmeticProduct

app = FastAPI(title="Cosmetics Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateProductRequest(CosmeticProduct):
    pass


class ProductResponse(CosmeticProduct):
    id: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Cosmetics Store Backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


@app.get("/schema")
def get_schema():
    # Expose available Pydantic schemas info (for tooling)
    return {
        "cosmeticproduct": {
            "fields": list(CosmeticProduct.model_fields.keys())
        }
    }


@app.get("/api/products", response_model=List[ProductResponse])
def list_products(category: Optional[str] = Query(default=None, description="Filter by category")):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict = {"category": category} if category else {}
    items = get_documents("cosmeticproduct", filter_dict=filter_dict)
    results: List[ProductResponse] = []
    for it in items:
        # Convert Mongo _id to string id
        it["id"] = str(it.pop("_id"))
        results.append(ProductResponse(**it))
    return results


@app.post("/api/products", status_code=201)
def create_product(payload: CreateProductRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    new_id = create_document("cosmeticproduct", payload)
    return {"id": new_id}


@app.get("/api/categories", response_model=List[str])
def list_categories():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        cats = db["cosmeticproduct"].distinct("category")
        cats = [c for c in cats if c]
        cats.sort()
        return cats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seed")
def seed_sample_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["cosmeticproduct"].count_documents({})
    if count > 0:
        return {"status": "ok", "message": "Products already exist", "count": count}

    samples = [
        {
            "title": "Velvet Matte Lipstick",
            "description": "Rich pigment, long-lasting matte finish",
            "price": 14.99,
            "category": "makeup",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1585218336020-3a9c1a66d0d8?q=80&w=1200&auto=format&fit=crop",
            "shopify_url": None,
            "brand": "GlowLab",
            "tags": ["lipstick", "matte"],
            "rating": 4.6,
        },
        {
            "title": "Hydrating Face Serum",
            "description": "Hyaluronic acid + Vitamin B5 for deep hydration",
            "price": 24.5,
            "category": "skincare",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?q=80&w=1200&auto=format&fit=crop",
            "shopify_url": None,
            "brand": "PureSkin",
            "tags": ["serum", "hydrating"],
            "rating": 4.8,
        },
        {
            "title": "Nourishing Hair Oil",
            "description": "Lightweight oil for shine and frizz control",
            "price": 18.0,
            "category": "haircare",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1604654894610-df63bc536371?q=80&w=1200&auto=format&fit=crop",
            "shopify_url": None,
            "brand": "SilkRoot",
            "tags": ["hair", "oil"],
            "rating": 4.5,
        },
        {
            "title": "Mineral Sunscreen SPF 50",
            "description": "Broad spectrum, reef-safe mineral sunscreen",
            "price": 19.99,
            "category": "skincare",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1610384104073-96d02d53c16f?q=80&w=1200&auto=format&fit=crop",
            "shopify_url": None,
            "brand": "SunVeil",
            "tags": ["sunscreen", "spf50"],
            "rating": 4.7,
        },
    ]
    for s in samples:
        create_document("cosmeticproduct", s)

    return {"status": "ok", "inserted": len(samples)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
