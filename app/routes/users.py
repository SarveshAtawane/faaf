from fastapi import APIRouter, HTTPException, status
from typing import List
from ..db.mongo import db
from ..models.user import UserCreate, UserOut, UserLogin
from ..config import settings
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(user.password)
    data = user.dict()
    data['password'] = hashed
    result = await db.users.insert_one(data)
    return UserOut(id=str(result.inserted_id), name=user.name, email=user.email)

@router.post("/login", response_model=UserOut)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user.get('password', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return UserOut(id=str(db_user['_id']), name=db_user['name'], email=db_user['email'])

@router.get("/", response_model=List[UserOut])
async def list_users():
    users = []
    cursor = db.users.find()
    async for u in cursor:
        users.append(UserOut(id=str(u['_id']), name=u['name'], email=u['email']))
    return users
