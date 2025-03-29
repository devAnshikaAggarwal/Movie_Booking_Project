# Movie Booking System

## Overview
The **Movie Booking System** is a Python-based project that allows users to book movie tickets online. It utilizes MySQL for data storage, APIs to fetch movie and theater details, and an email service for booking confirmations. The project is structured using Object-Oriented Programming (OOP) principles.

## Features
### User Features
- **User Registration & Login**
- **View Available Movies & Theaters**
- **Book Tickets**
- **View and Cancel Bookings**
- **Make Payments for Bookings**
- **Receive Email Confirmation for Bookings**

### Admin Features
- **View All Bookings**
- **View All Payments**
- **Cancel Any Booking**

## Technologies Used
- **Python**
- **MySQL** (Database)
- **APIs** (Fetch Movies & Theaters Data)
- **SMTP (Email Service)**
- **Object-Oriented Programming (OOP)**

## Installation & Setup
### Prerequisites
- Install **Python 3.x**
- Install **MySQL Server**
- Install Required Python Packages:
  ```sh
  pip install mysql-connector-python requests smtplib
  ```

### Database Setup
1. Create a MySQL Database:
   ```sql
   CREATE DATABASE movie_project;
   ```
2. Create Required Tables:
   ```sql
   CREATE TABLE users
   
   CREATE TABLE movies 

   CREATE TABLE theaters 

   CREATE TABLE bookings 

   CREATE TABLE payments 

### Running the Application
1. Update `db_config` in `movie_booking.py` with your MySQL credentials.
2. Set up your email credentials for SMTP services.
3. Run the script:
   ```sh
   python movie_booking.py
   ```
4. Follow the menu instructions to interact with the system.

## API Integration
The system fetches movies and theater details from external APIs:
- **Movies API:** `http://demo5472131.mockable.io/movies`
- **Theaters API:** `http://demo5472131.mockable.io/theatres`

## Future Improvements
- Implement **password encryption** for better security.
- Add **seat selection** for a better booking experience.
- Enhance **UI with a web framework** (e.g., Flask or Django).
- Implement **payment gateway integration**.
