import httpx
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def register_user(data):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?email=eq.{data.email}",
            headers=headers
        )
        if response.json():
            return {"error": "Email already registered"}

        payload = {
            "email": data.email,
            "password": hash_password(data.password),
            "full_name": data.full_name
        }
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            headers=headers,
            json=payload
        )
        return {"message": "User registered successfully"}

async def login_user(data):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?email=eq.{data.email}",
            headers=headers
        )
        users = response.json()
        if not users:
            return {"error": "Invalid email or password"}

        user = users[0]
        if not verify_password(data.password, user["password"]):
            return {"error": "Invalid email or password"}

        return {
            "message": "Login successful",
            "user": {
                "email": user["email"],
                "full_name": user["full_name"]
            }
        }
