from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import uuid
from typing import List, Optional, Dict, Any

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.grocery_delivery

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()

app = FastAPI(title="Grocery Delivery API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class User(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    address: str = ""
    phone: str = ""
    is_admin: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    address: str = ""
    phone: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    stock: int = 100

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: str
    stock: int = 100

class CartItem(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    id: str
    user_id: str
    items: List[Dict[str, Any]]
    subtotal: float
    service_fee: float
    transportation_fee: float
    total: float
    status: str
    created_at: datetime
    delivery_address: str

class OrderCreate(BaseModel):
    items: List[CartItem]
    delivery_address: str

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user

# Helper function to convert MongoDB document
def convert_mongo_doc(doc):
    if doc:
        doc.pop('_id', None)  # Remove MongoDB ObjectId
    return doc

def convert_mongo_docs(docs):
    return [convert_mongo_doc(doc) for doc in docs]

# Initialize sample products
@app.on_event("startup")
async def startup_event():
    # Check if products already exist
    existing_products = await db.products.count_documents({})
    if existing_products == 0:
        sample_products = [
            {
                "id": str(uuid.uuid4()),
                "name": "Fresh Bananas",
                "description": "Organic bananas perfect for smoothies and snacks",
                "price": 2.99,
                "category": "fruits",
                "image_url": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxmcnVpdHMlMjB2ZWdldGFibGVzfGVufDB8fHx8MTc1NTI1NDA4Mnww&ixlib=rb-4.1.0&q=85",
                "stock": 100
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mixed Vegetables",
                "description": "Fresh mixed vegetables for healthy cooking",
                "price": 4.99,
                "category": "vegetables",
                "image_url": "https://images.unsplash.com/photo-1579113800032-c38bd7635818?crop=entropy&cs=srgb&fm=jwt&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwyfHxmcmVzaCUyMGZvb2R8ZW58MHx8fHwxNzU1MjU0MDc2fDA&ixlib=rb-4.1.0&q=85",
                "stock": 100
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Chocolate Bars",
                "description": "Assorted chocolate bars for sweet cravings",
                "price": 3.49,
                "category": "snacks",
                "image_url": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxzbmFja3N8ZW58MHx8fHwxNzU1MjU0MDg3fDA&ixlib=rb-4.1.0&q=85",
                "stock": 100
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mixed Snacks",
                "description": "Variety pack of student-friendly snacks",
                "price": 5.99,
                "category": "snacks",
                "image_url": "https://images.unsplash.com/photo-1614735241165-6756e1df61ab?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxzbmFja3N8ZW58MHx8fHwxNzU1MjU0MDg3fDA&ixlib=rb-4.1.0&q=85",
                "stock": 100
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Fresh Bread",
                "description": "Freshly baked bread for daily meals",
                "price": 2.49,
                "category": "bakery",
                "image_url": "https://images.unsplash.com/photo-1601599964542-bbdfd6008d34?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwzfHxncm9jZXJ5JTIwcHJvZHVjdHN8ZW58MHx8fHwxNzU1MjU0MDcyfDA&ixlib=rb-4.1.0&q=85",
                "stock": 100
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Apple Display",
                "description": "Fresh crisp apples from local farms",
                "price": 3.99,
                "category": "fruits",
                "image_url": "https://images.unsplash.com/photo-1653222439694-f7f84f69edf6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHw0fHxmcnVpdHMlMjB2ZWdldGFibGVzfGVufDB8fHx8MTc1NTI1NDA4Mnww&ixlib=rb-4.1.0&q=85",
                "stock": 100
            }
        ]
        await db.products.insert_many(sample_products)

# Auth endpoints
@app.post("/api/register")
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "address": user.address,
        "phone": user.phone,
        "is_admin": False,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_data)
    return {"message": "User registered successfully"}

@app.post("/api/login")
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["email"]}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "is_admin": db_user["is_admin"]
        }
    }

# Product endpoints
@app.get("/api/products")
async def get_products(category: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if category and category != "all":
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.products.find(query).to_list(length=None)
    return convert_mongo_docs(products)

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return convert_mongo_doc(product)

@app.get("/api/categories")
async def get_categories():
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "count": 1, "_id": 0}}
    ]
    categories = await db.products.aggregate(pipeline).to_list(length=None)
    return categories

# Cart and Order endpoints
@app.post("/api/orders")
async def create_order(order: OrderCreate, current_user: dict = Depends(get_current_user)):
    # Calculate order totals
    subtotal = 0
    order_items = []
    
    for item in order.items:
        product = await db.products.find_one({"id": item.product_id})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        item_total = product["price"] * item.quantity
        subtotal += item_total
        
        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": item.quantity,
            "total": item_total
        })
    
    # Calculate fees
    service_fee = subtotal * 0.05  # 5% service fee
    transportation_fee = 2.99  # Fixed transportation fee
    total = subtotal + service_fee + transportation_fee
    
    # Create order
    order_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "items": order_items,
        "subtotal": round(subtotal, 2),
        "service_fee": round(service_fee, 2),
        "transportation_fee": round(transportation_fee, 2),
        "total": round(total, 2),
        "status": "pending",
        "created_at": datetime.utcnow(),
        "delivery_address": order.delivery_address
    }
    
    await db.orders.insert_one(order_data)
    return convert_mongo_doc(order_data)

@app.get("/api/orders")
async def get_user_orders(current_user: dict = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(length=None)
    return convert_mongo_docs(orders)

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id, "user_id": current_user["id"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return convert_mongo_doc(order)

# Mock payment endpoint
@app.post("/api/orders/{order_id}/pay")
async def pay_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id, "user_id": current_user["id"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")
    
    # Mock payment processing
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": "paid", "paid_at": datetime.utcnow()}}
    )
    
    return {"message": "Payment successful", "order_id": order_id}

# Admin endpoints
@app.get("/api/admin/orders")
async def get_all_orders(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    orders = await db.orders.find({}).sort("created_at", -1).to_list(length=None)
    return convert_mongo_docs(orders)

@app.put("/api/admin/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Order status updated"}

@app.post("/api/admin/products")
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    product_data = product.dict()
    product_data["id"] = str(uuid.uuid4())
    product_data["created_at"] = datetime.utcnow()
    
    await db.products.insert_one(product_data)
    return convert_mongo_doc(product_data)

@app.put("/api/admin/products/{product_id}")
async def update_product(product_id: str, product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.products.update_one(
        {"id": product_id},
        {"$set": {**product.dict(), "updated_at": datetime.utcnow()}}
    )
    return {"message": "Product updated"}

@app.delete("/api/admin/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.products.delete_one({"id": product_id})
    return {"message": "Product deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)