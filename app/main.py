from fastapi import FastAPI, Request, Depends, HTTPException, status, APIRouter, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import Reservation as ReservationModel, Vehicule as VehiculeModel, Paiement as PaiementModel
from typing import Optional
import hashlib
import shutil
from typing import List
from passlib.context import CryptContext
from . import models
from app.database import engine, get_db_conn
import os
from app.models import Reservation

app = FastAPI()
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Path to the directory containing your templates
templates = Jinja2Templates(directory="templates")
# Correct path to your assets (static files)
app.mount("/assets", StaticFiles(directory="templates/assets"), name="assets")
app.include_router(router, prefix="/auth")  # Prefix added for better URL structure
models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    id: int  # Assuming your User model has an ID
    name: str
    lastname: str
    email: str
    password: str
    profile_pic_url: Optional[str]

    class Config:
        orm_mode = True

class PasswordUpdate(BaseModel):
    new_password: str

    class Config:
        orm_mode = True

class Reservation(BaseModel):
    dateDebut: str
    dateFin: str
    lieu: str
    utilisateur_id: int
    vehicule_id: int

    class Config:
        orm_mode = True

class Vehicule(BaseModel):
    v_id: int
    marque: str
    modele: str
    prix: float
    disponibilite: bool

    class Config:
        orm_mode = True

class Paiement(BaseModel):
    p_id: int
    montant: float
    date: str
    reservation_id: int

    class Config:
        orm_mode = True

#user informatin
def get_current_user(request: Request):
    user = request.session.get("user")
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.on_event("startup")
async def startup_db_conn():
    app.db_conn = get_db_conn()

@app.on_event("shutdown")
async def shutdown_db_conn():
    app.db_conn.close()

# registre user
@app.post("/sign_up")
async def sign_up(name: str = Form(...), lastname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_conn)):
    # Check if the user already exists
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    hashed_password = pwd_context.hash(password)
    new_user = models.Users(name=name, lastname=lastname, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"data": new_user}

@app.post("/add_user", response_class=RedirectResponse)
async def add_user(name: str = Form(...), lastname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_conn)):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    hashed_password = pwd_context.hash(password)
    new_user = models.Users(name=name, lastname=lastname, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/gestion_utilisateurs", status_code=status.HTTP_302_FOUND)


@app.get("/api/users", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_conn)):
    users = db.query(models.Users).offset(skip).limit(limit).all()
    return users

@app.delete("/api/users/{user_id}", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db_conn)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user

# log user
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_conn)):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    
    if not user or not pwd_context.verify(password, user.password):
        # Handle invalid login credentials
        error_message = "Invalid email or password"
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})
    
    # Login successful, set session and redirect
    request.session["user"] = {"name": user.name, "email": user.email}
    request.session["user_id"] = user.id
    return RedirectResponse(url="/user_account", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/user_account", response_class=HTMLResponse)
async def user_account(request: Request, db: Session = Depends(get_db_conn)):
    try:
        user = get_current_user(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    db_user = db.query(models.Users).filter(models.Users.email == user["email"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        "name": db_user.name,
        "lastname": db_user.lastname,
        "email": db_user.email,
        "profile_pic_url": db_user.profile_pic_url  # Replace with actual field name for profile picture URL
    }
    return templates.TemplateResponse("user_account.html", {
        "request": request, 
        "user": user_data
    })

@app.post("/user_account")
async def update_user_account(
    request: Request,
    editName: str = Form(...),
    editLastname: str = Form(...),
    editEmail: str = Form(...),
    editPassword: str = Form(None),
    editProfilePic: UploadFile = File(None),
    db: Session = Depends(get_db_conn)
):
    try:
        user = get_current_user(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    db_user = db.query(models.Users).filter(models.Users.email == user["email"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = editName
    db_user.lastname = editLastname
    db_user.email = editEmail
    
    if editPassword:
        db_user.hashed_password = pwd_context.hash(editPassword)
    
    if editProfilePic:
        try:
            # Example path where files are saved
            upload_dir = "assets/"
            os.makedirs(upload_dir, exist_ok=True)  # Ensure directory exists
            
            # Save the file to the upload directory
            profile_pic_path = os.path.join(upload_dir, editProfilePic.filename)
            with open(profile_pic_path, "wb") as buffer:
                shutil.copyfileobj(editProfilePic.file, buffer)
            
            # Update profile pic URL in the database
            db_user.profile_pic_url = profile_pic_path

        except Exception as e:
            # Handle any error that occurs during file upload
            return RedirectResponse(url="/user_account?message=Failed to upload profile picture.", status_code=302)
    
    # Commit changes to the database
    db.commit()
    
    # Redirect to user account page with success message
    return RedirectResponse(url="/user_account?message=Update successful!", status_code=302)

# verifie connection avant paiement
@app.get("/payment", response_class=HTMLResponse)
async def payment(request: Request):
    try:
        user = get_current_user(request)
        dateDebut = request.session.get('dateDebut')
        dateFin = request.session.get('dateFin')
        lieu = request.session.get('lieu')
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("payment.html", {"request": request,"dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu, "user": user})

@app.post("/payment")
async def submit_payment(
    request: Request,
    v_id: int = Form(...),
    cardNumber: str = Form(...),
    cardExpiry: str = Form(...),
    cardCVC: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db_conn)
):
    # Retrieve other data from the session or request
    dateDebut = request.session.get("dateDebut")
    dateFin = request.session.get("dateFin")
    lieu = request.session.get("lieu")
    user1_id = request.session.get("user_id")

    if not all([dateDebut, dateFin, lieu, user1_id]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incomplete session data")

    # Insert reservation into the database
    new_reservation = models.Reservation(
        dateDebut=dateDebut,
        dateFin=dateFin,
        lieu=lieu,
        utilisateur_id=user1_id,
        vehicule_id=v_id
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    # Retrieve the vehicle to get the price
    vehicule = db.query(models.Vehicule).filter(models.Vehicule.v_id == v_id).first()
    if not vehicule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Insert payment into the database
    new_paiement = models.Paiement(
        montant=vehicule.prix,
        date=dateDebut,
        reservation_id=new_reservation.r_id
    )
    db.add(new_paiement)
    db.commit()
    db.refresh(new_paiement)

    return templates.TemplateResponse("confirmation.html", {"request": request, "reservation": new_reservation})

# Other parts of your application and setup
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/search")
async def search(
    request: Request,
    dateDebut: str = Form(...),
    dateFin: str = Form(...),
    lieu: str = Form(...)
):
    if not dateDebut or not dateFin or not lieu:
        error_message = "All fields are required. Please fill in all the fields."
        return templates.TemplateResponse("index.html", {"request": request, "error_message": error_message})
    
    request.session['dateDebut'] = dateDebut
    request.session['dateFin'] = dateFin
    request.session['lieu'] = lieu
    return RedirectResponse(url="/car_listing", status_code=303)

@app.get("/car_listing")
async def car_listing(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    return templates.TemplateResponse("car_listing.html", {
        "request": request,
        "dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,
    })

@app.get("/convertible_detail")
async def convertible_detail(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    if not dateDebut or not dateFin or not lieu:
        error_message = "Date fields are required. Please fill in all the fields."
        return templates.TemplateResponse("convetible_detail.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("convetible_detail.html", {"request": request,"dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,})

@app.get("/family_detail", response_class=HTMLResponse)
async def family_detail(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    if not dateDebut or not dateFin or not lieu:
        error_message = "Date fields are required. Please fill in all the fields."
        return templates.TemplateResponse("familly_detail.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("familly_detail.html", {"request": request,"dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,})

@app.get("/SUV_detail", response_class=HTMLResponse)
async def suv_detail(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    if not dateDebut or not dateFin or not lieu:
        error_message = "Date fields are required. Please fill in all the fields."
        return templates.TemplateResponse("SUV_detail.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("SUV_detail.html", {
        "request": request,
        "dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,
    })

@app.get("/voiture_de_luxe", response_class=HTMLResponse)
async def voiture_de_luxe(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    if not dateDebut or not dateFin or not lieu:
        error_message = "Date fields are required. Please fill in all the fields."
        return templates.TemplateResponse("voiture_de_luxe.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("voiture_de_luxe.html", {"request": request,"dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,})

@app.get("/voiture_economy_detail", response_class=HTMLResponse)
async def voiture_economy_detail(request: Request):
    dateDebut = request.session.get('dateDebut')
    dateFin = request.session.get('dateFin')
    lieu = request.session.get('lieu')

    if not dateDebut or not dateFin or not lieu:
        error_message = "Date fields are required. Please fill in all the fields."
        return templates.TemplateResponse("voiture_economy_detail.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("voiture_economy_detail.html", {"request": request,"dateDebut": dateDebut,
        "dateFin": dateFin,
        "lieu": lieu,})

@app.get("/")
async def read_root(request: Request):
    context = {"request": request, "session": request.session}
    return templates.TemplateResponse("index.html", context)

@app.get("/about_us", response_class=HTMLResponse)
async def about_us(request: Request):
    return templates.TemplateResponse("about_us.html", {"request": request})

@app.get("/contact_us", response_class=HTMLResponse)
async def contact_us(request: Request):
    return templates.TemplateResponse("contact_us.html", {"request": request})


@app.get("/dashboard", response_class=RedirectResponse)
def dashboard(request: Request, db: Session = Depends(get_db_conn)):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
    
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/reservation", response_class=HTMLResponse)
async def get_reservations(request: Request, db: Session = Depends(get_db_conn)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    reservations = db.query(ReservationModel).filter(ReservationModel.utilisateur_id == user_id).all()
    reservation_details = []

    for reservation in reservations:
        vehicule = db.query(VehiculeModel).filter(VehiculeModel.v_id == reservation.vehicule_id).first()
        paiement = db.query(PaiementModel).filter(PaiementModel.reservation_id == reservation.r_id).first()
        reservation_details.append({
            "voiture": f"{vehicule.marque} {vehicule.modele}",
            "dateDebut": reservation.dateDebut,
            "dateFin": reservation.dateFin,
            "lieu": reservation.lieu,
            "prix": paiement.montant if paiement else "N/A",
            "statut": "Confirmé" if paiement else "En attente"
        })

    return templates.TemplateResponse("reservation.html", {"request": request, "reservations": reservation_details})


@app.get("/gestion_utilisateurs", response_class=HTMLResponse)
async def sign_up_admin(request: Request):
    return templates.TemplateResponse("gestion_utilisateurs.html", {"request": request})

@app.get("/gestion_voitures", response_class=HTMLResponse)
async def sign_up_admin(request: Request):
    return templates.TemplateResponse("gestion_voitures.html", {"request": request})

@app.get("/sign_up_admin", response_class=HTMLResponse)
async def sign_up_admin(request: Request):
    return templates.TemplateResponse("sign_up_admin.html", {"request": request})

@app.get("/sign_up", response_class=HTMLResponse)
async def sign_up(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

# Add SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)