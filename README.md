# Car Rental Platform

Welcome to the **Car Rental Platform** built with **FastAPI**. This platform allows users to rent cars conveniently, view available vehicles, make reservations, and handle payments. The admin interface allows managing users, reservations, and car listings.

## Features

- **User Authentication**: Sign up, log in, and manage user profiles.
- **Car Listings**: Browse available cars with details such as model, price, and availability.
- **Reservation System**: Make car reservations by selecting rental dates and car preferences.
- **Payment Integration**: Process payments for reservations.
- **Admin Dashboard**: Manage car listings, users, and reservations from the admin interface.

## Technologies Used

- **Backend**: FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: HTML, Bootstrap, Jinja2 templates
- **Environment**: Python, Uvicorn

## Installation

To run the platform locally, follow these instructions:

### 1. Clone the repository
  ```bash
  git clone https://github.com/imad-chakour/car-rental-platform.git
  cd car-rental-platform

2. Set up the virtual environment
  On Windows:
    python -m venv venv
    venv\Scripts\activate

3. Install dependencies
    pip install -r requirements.txt

4. Configure the environment
    Create a .env file in the project root and configure the following environment variables:
      DATABASE_URL=postgresql://user:password@localhost/dbname
      SECRET_KEY=your-secret-key
      DEBUG=True

5. Run the application
    uvicorn main:app --reload
Visit the platform at http://127.0.0.1:8000.

## Endpoints
  GET /cars: Retrieve a list of available cars.
  POST /reserve: Make a reservation.
  POST /login: Log in as a user.
  POST /signup: Register a new user.
  GET /admin: Admin dashboard for managing users and reservations.
  Contributing
  We welcome contributions! To contribute:

## Fork the repository.
  Create a new branch (git checkout -b feature-branch).
  Make your changes.
  Commit your changes (git commit -am 'Add new feature').
  Push to your branch (git push origin feature-branch).
  Open a Pull Request.

## Acknowledgements
  FastAPI for its speed and simplicity in building APIs.
  SQLAlchemy for the ORM functionality.
  PostgreSQL for providing a robust relational database.
  Bootstrap for frontend styling.
  Uvicorn for serving the FastAPI app.
