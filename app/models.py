from app.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    profile_pic_url = Column(String)
    is_admin = Column(Boolean, default=False)

    reservations = relationship("Reservation", back_populates="user")

class Vehicule(Base):
    __tablename__ = "vehicule"
    
    v_id = Column(Integer, primary_key=True, nullable=False)
    marque = Column(String, nullable=False)
    modele = Column(String, nullable=False)
    prix = Column(Float, nullable=False)
    disponibilite = Column(Boolean, default=True)
    categorie = Column(String, nullable=False)
    # One-to-Many relationship with Reservation
    reservations = relationship("Reservation", back_populates="vehicule")

class Reservation(Base):
    __tablename__ = "reservation"

    r_id = Column(Integer, primary_key=True, nullable=False)
    dateDebut = Column(String, nullable=False)
    dateFin = Column(String, nullable=False)
    lieu = Column(String, nullable=False)
    utilisateur_id = Column(Integer, ForeignKey("users.id"))
    vehicule_id = Column(Integer, ForeignKey("vehicule.v_id"))

    # Many-to-One relationship with Users
    user = relationship("Users", back_populates="reservations")

    # Many-to-One relationship with Vehicule
    vehicule = relationship("Vehicule", back_populates="reservations")

    # One-to-Many relationship with Paiement
    paiements = relationship("Paiement", back_populates="reservation")

class Paiement(Base):
    __tablename__ = "paiement"

    p_id = Column(Integer, primary_key=True, nullable=False)
    montant = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    reservation_id = Column(Integer, ForeignKey("reservation.r_id"))

    # Many-to-One relationship with Reservation
    reservation = relationship("Reservation", back_populates="paiements")
