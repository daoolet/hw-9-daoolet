from fastapi import Cookie, FastAPI, Form, Request, Response, templating, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel

from jose import jwt

from sqlalchemy.orm import Session


from .database import SessionLocal, Base, engine
from .flowers_repository import FlowersRepository, Flower, FlowerCreate
from .purchases_repository import PurchasesRepository
from .users_repository import UsersRepository, User, UserCreate


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
Base.metadata.create_all(bind=engine)


flowers_repository = FlowersRepository()
purchases_repository = PurchasesRepository()
users_repository = UsersRepository()


@app.get("/")
def root():
    return Response("200 - OK", status_code=200)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------- SIGN UP

@app.get("/signup")
def get_signup():
    return Response("Registered - OK", status_code=200)

@app.post("/signup")
def post_sigup(
    email: str,
    full_name: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = users_repository.get_by_email(db, user_email=email)

    if user:
        raise HTTPException(status_code = 400, detail="User with this username already exists")
    
    new_user = UserCreate(email=email, full_name=full_name, password=password)
    answer = users_repository.save_user(db, user = new_user)

    return answer


# --------------- LOGIN

def create_access_token(user_id: str) -> str:
    body = {"user_id": user_id}
    token = jwt.encode(body, "kek", "HS256")
    return token

def decode_jwt(token: str) -> int:
    data = jwt.decode(token, "kek", "HS256")
    return data["user_id"]

@app.get("/login")
def get_login():
    return Response("Logged in - OK", status_code=200)

@app.post("/login")
def post_login(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)

):
    user = users_repository.get_by_email(db, user_email=data.username)
    if not user:
        return Response("Loggin Failed: Wrong email or password")

    if user.password == data.password:
        token = create_access_token(user.email)
 
    return {"access_token": token, "type": "bearer"}


# --------------- PROFILE

@app.get("/profile")
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    user = users_repository.get_by_id(db, user_id=user_id)
    return Response("Profile - OK", status_code= 200)


# --------------- FLOWERS

@app.get("/flowers")
def get_flowers(db: Session = Depends(get_db)):

    flowers = flowers_repository.get_all(db)
    return flowers

@app.post("/flowers")
def post_flowers(name: str, cost: int, count: int, db: Session = Depends(get_db)):
    
    new_flower = FlowerCreate(name=name, cost=cost, count=count)
    answer = flowers_repository.save_flower(db, new_flower)

    return answer

@app.patch("/flowers/{flower_id}")
def patch_flower(
    flower_id: int,
    name: str,
    cost: int,
    count: int,
    db: Session = Depends(get_db)
):

    new_flower = FlowerCreate(name=name, cost=cost, count=count)
    updated_flower = flowers_repository.update_flower(db, flower_id=flower_id, new_flower=new_flower)

    if not updated_flower:
        raise HTTPException(status_code = 400, detail="Update did not happen")
    
    return Response("Update - OK", status_code=200)

@app.delete("/flowers/{flower_id}")
def delete_flower(flower_id: int, db: Session = Depends(get_db)):
    deleted_flower = flowers_repository.delete_flower(db, flower_id=flower_id)

    if not deleted_flower:
        raise HTTPException(status_code = 400, detail="Deletion did not happen")
    
    return Response("Delete - OK", status_code=200)

# --------------- CART

@app.get("/cart/items")
def get_cart(db: Session = Depends(get_db)):
     
    cart_flowers = flowers_repository.get_all_cart_flowers(db)
    total_cost = sum(i.cost for i in cart_flowers)

    return {"cart_flowers": cart_flowers, "total_cost": total_cost}

@app.post("/cart/items")
def post_cart(flower_id: int, db: Session = Depends(get_db)):
    
    current_flower = flowers_repository.get_by_id(db, flower_id=flower_id)
    if not current_flower:
        raise HTTPException(status_code = 400, detail="Flower does not exists with this id")

    new_flower = FlowerCreate(name=current_flower.name, cost=current_flower.cost, count=current_flower.count)
    flowers_repository.save_cart_flower(db, new_flower)

    response = Response("Added to cart - OK", status_code=200)
    response.set_cookie("flower_id", flower_id)

    return response


# конец решения