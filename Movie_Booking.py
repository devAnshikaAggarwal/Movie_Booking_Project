import mysql.connector
import requests
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration for MySQL and external services.
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "1234", 
    "database": "movie_project"
}

# For email credentials, load them from environment variables or a secure source
EMAIL_ADDRESS = "SENDER_EMAIL"
EMAIL_PASSWORD = "svfu jxbk kcrm fyzn"


class Database:
    """Database helper class to handle connections and queries."""

    def __init__(self, config):
        try:
            self.conn = mysql.connector.connect(**config)
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as err:
            print("Error connecting to database:", err)
            raise

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except mysql.connector.Error as err:
            print("Database query error:", err)
            self.conn.rollback()
            return None

    def fetchall(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.cursor.close()
        self.conn.close()


class EmailService:
    """Service to handle sending emails."""
    @staticmethod
    def send_email(recipient, subject, message):
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
            server.quit()
            print("Email sent successfully to", recipient)
        except Exception as e:
            print("Failed to send email:", e)


class UserService:
    def __init__(self, db: Database):
        self.db = db

    def signup(self):
        name = input("Enter your name: ")
        email = input("Enter your email: ")
        password = input("Enter a password: ")
        try:
            self.db.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, password)
            )
            print("Signup successful! Please log in.")
        except mysql.connector.IntegrityError:
            print("Email already exists. Try logging in.")

    def login(self):
        email = input("Enter email: ")
        password = input("Enter password: ")
        user = self.db.fetchone(
            "SELECT id, name, email FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        if user:
            print(f"Welcome {user['name']}!")
            return user
        else:
            print("Invalid credentials. Please try again.")
            return None


class MovieService:
    API_URL = "http://demo5472131.mockable.io/movies"

    def __init__(self, db: Database):
        self.db = db

    def fetch_movies(self):
        try:
            response = requests.get(MovieService.API_URL)
            response.raise_for_status()
            movies = response.json().get("movies", [])
            for movie in movies:
                # Convert list of showtimes into a comma-separated string.
                showtimes = ",".join(movie.get("showtimes", []))
                self.db.execute(
                    """INSERT INTO movies (id, title, duration, genre, showtimes)
                       VALUES (%s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE title=%s, duration=%s, genre=%s, showtimes=%s""",
                    (movie['id'], movie['title'], movie['duration'], movie['genre'], showtimes,
                     movie['title'], movie['duration'], movie['genre'], showtimes)
                )
            print("Movies fetched and updated successfully.")
        except requests.RequestException as e:
            print("Failed to fetch movies:", e)

    def show_movies(self):
        movies = self.db.fetchall(
            "SELECT id, title, duration, genre, showtimes FROM movies")
        if movies:
            print("\nAvailable Movies:")
            for movie in movies:
                print(f"ID: {movie['id']}, Title: {movie['title']}, Duration: {movie['duration']} mins, "
                      f"Genre: {movie['genre']}, Showtimes: {movie['showtimes']}")
        else:
            print("No movies available.")


class TheatreService:
    API_URL = "http://demo5472131.mockable.io/theatres"

    def __init__(self, db: Database):
        self.db = db

    def fetch_theaters(self):
        try:
            response = requests.get(TheatreService.API_URL)
            response.raise_for_status()
            theaters = response.json().get("theaters", [])
            for theater in theaters:
                self.db.execute(
                    """INSERT INTO theaters (id, name, location, total_seats)
                       VALUES (%s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE name=%s, location=%s, total_seats=%s""",
                    (theater['id'], theater['name'], theater['location'], theater['total_seats'],
                     theater['name'], theater['location'], theater['total_seats'])
                )
            print("Theaters fetched and updated successfully.")
        except requests.RequestException as e:
            print("Failed to fetch theaters:", e)

    def show_theaters(self):
        theaters = self.db.fetchall(
            "SELECT id, name, location, total_seats FROM theaters")
        if theaters:
            print("\nAvailable Theaters:")
            for theater in theaters:
                print(f"ID: {theater['id']}, Name: {theater['name']}, Location: {theater['location']}, "
                      f"Total Seats: {theater['total_seats']}")
        else:
            print("No theaters available.")


class BookingService:
    def __init__(self, db: Database):
        self.db = db

    def book_ticket(self, user_id, user_email):
        # Show available movies and theaters before booking.
        movie_id = input("Enter the Movie ID you want to book: ")
        theater_id = input("Enter the Theatre ID: ")
        showtime = input("Enter preferred showtime: ")
        seats = input("Enter number of seats to book: ")

        # Check available seats in theater before booking:
        theater = self.db.fetchone(
            "SELECT total_seats FROM theaters WHERE id = %s", (theater_id,))
        if not theater:
            print("Invalid Theatre ID!")
            return
        # Convert seats to integer (since seats is stored as text in bookings)
        try:
            seats_int = int(seats)
        except ValueError:
            print("Invalid seats value.")
            return
        if seats_int > theater['total_seats']:
            print("Not enough seats available.")
            return

        # Insert a new booking with current timestamp as booking_date
        self.db.execute(
            """INSERT INTO bookings (user_id, movie_id, theater_id, showtime, seats, booking_date)
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (user_id, movie_id, theater_id, showtime, seats)
        )
        booking_cursor = self.db.cursor
        booking_id = booking_cursor.lastrowid
        print(f"Booking successful! Your Booking ID is: {booking_id}")

        # Update theater seat availability (subtract booked seats)
        self.db.execute(
            "UPDATE theaters SET total_seats = total_seats - %s WHERE id = %s",
            (seats_int, theater_id)
        )

        # Send confirmation email
        EmailService.send_email(
            user_email,
            "Booking Confirmation",
            f"Your booking (ID: {booking_id}) for movie ID {movie_id} at theater ID {theater_id} on {showtime} "
            f"for {seats} seats has been successfully recorded."
        )
        return booking_id

    def show_bookings(self, user_id):
        query = ("""SELECT b.id as booking_id, m.title, t.name as theatre, b.showtime, b.seats, b.booking_date 
                    FROM bookings b
                    JOIN movies m ON b.movie_id = m.id
                    JOIN theaters t ON b.theater_id = t.id
                    WHERE b.user_id = %s""")
        bookings = self.db.fetchall(query, (user_id,))
        if bookings:
            print("\nYour Bookings:")
            for booking in bookings:
                print(f"Booking ID: {booking['booking_id']}, Movie: {booking['title']}, Theatre: {booking['theatre']}, "
                      f"Showtime: {booking['showtime']}, Seats: {booking['seats']}, "
                      f"Booking Date: {booking['booking_date']}")
        else:
            print("No bookings found.")

    def cancel_booking(self, user_id):
        booking_id = input("Enter Booking ID to cancel: ")
        # Check if booking exists and belongs to user
        booking = self.db.fetchone(
            "SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        if booking:
            # Delete the booking and refund seats
            self.db.execute(
                "DELETE FROM bookings WHERE id = %s", (booking_id,))
            try:
                seats_int = int(booking['seats'])
            except ValueError:
                seats_int = 0
            self.db.execute("UPDATE theaters SET total_seats = total_seats + %s WHERE id = %s",
                            (seats_int, booking['theater_id']))
            print("Booking cancelled successfully.")
            # Send cancellation email
            user_email = self.db.fetchone(
                "SELECT email FROM users WHERE id = %s", (user_id,))
            if user_email:
                EmailService.send_email(
                    user_email['email'],
                    "Booking Cancellation",
                    f"Your booking (ID: {booking_id}) has been cancelled."
                )
        else:
            print("Invalid booking ID or unauthorized cancellation.")


class PaymentService:
    def __init__(self, db: Database):
        self.db = db

    def initiate_payment(self, booking_id):
        amount = float(input("Enter payment amount: "))
        status = 'pending'
        self.db.execute(
            "INSERT INTO payments (booking_id, amount, status, payment_date) VALUES (%s, %s, %s, NOW())",
            (booking_id, amount, status)
        )
        print("Payment initiated. Status: pending")
        return self.process_payment(booking_id)

    def process_payment(self, booking_id):
        # Simulate payment processing with a random outcome.
        new_status = random.choice(['confirmed', 'cancelled'])
        self.db.execute(
            "UPDATE payments SET status = %s WHERE booking_id = %s",
            (new_status, booking_id)
        )
        booking = self.db.fetchone(
            "SELECT * FROM bookings WHERE id = %s", (booking_id,))
        if new_status == 'confirmed':
            print("Payment successful! Booking confirmed.")
        else:
            print("Payment failed! Booking cancelled.")
            if booking:
                self.db.execute(
                    "DELETE FROM bookings WHERE id = %s", (booking_id,))
                try:
                    seats_int = int(booking['seats'])
                except ValueError:
                    seats_int = 0
                self.db.execute(
                    "UPDATE theaters SET total_seats = total_seats + %s WHERE id = %s",
                    (seats_int, booking['theater_id'])
                )
        return new_status


class AdminPanel:
    def __init__(self, db: Database):
        self.db = db

    def view_bookings(self):
        bookings = self.db.fetchall("SELECT * FROM bookings")
        print("\nAll Booking Details:")
        for booking in bookings:
            print(booking)

    def view_payments(self):
        payments = self.db.fetchall("SELECT * FROM payments")
        print("\nAll Payment Details:")
        for payment in payments:
            print(payment)

    def cancel_booking(self):
        booking_id = input("Enter Booking ID to cancel: ")
        booking = self.db.fetchone(
            "SELECT * FROM bookings WHERE id = %s", (booking_id,))
        if booking:
            self.db.execute(
                "DELETE FROM bookings WHERE id = %s", (booking_id,))
            print("Booking cancelled successfully by admin.")
            user = self.db.fetchone(
                "SELECT email FROM users WHERE id = %s", (booking['user_id'],))
            if user:
                EmailService.send_email(
                    user['email'],
                    "Booking Cancellation by Admin",
                    f"Your booking (ID: {booking_id}) has been cancelled by admin."
                )
        else:
            print("Booking ID not found.")


class MovieBookingApp:
    def __init__(self):
        self.db = Database(db_config)
        self.user_service = UserService(self.db)
        self.movie_service = MovieService(self.db)
        self.theatre_service = TheatreService(self.db)
        self.booking_service = BookingService(self.db)
        self.payment_service = PaymentService(self.db)
        self.admin_panel = AdminPanel(self.db)

    def main_menu(self):
        while True:
            print("\n--- Movie Booking System ---")
            print("1. User Panel")
            print("2. Admin Panel")
            print("3. Fetch Movies/Theaters from API")
            print("4. Exit")
            choice = input("Enter choice: ")
            if choice == '1':
                self.user_panel()
            elif choice == '2':
                self.admin_panel_menu()
            elif choice == '3':
                self.movie_service.fetch_movies()
                self.theatre_service.fetch_theaters()
            elif choice == '4':
                print("Exiting...")
                self.db.close()
                break
            else:
                print("Invalid choice. Try again.")

    def user_panel(self):
        while True:
            print("\n--- User Panel ---")
            print("1. Signup")
            print("2. Login")
            print("3. Back to Main Menu")
            choice = input("Enter choice: ")
            if choice == '1':
                self.user_service.signup()
            elif choice == '2':
                user = self.user_service.login()
                if user:
                    self.logged_in_menu(user)
            elif choice == '3':
                break
            else:
                print("Invalid choice.")

    def logged_in_menu(self, user):
        while True:
            print(f"\n--- Welcome {user['name']} ---")
            print("1. View Movies")
            print("2. View Theaters")
            print("3. Book Ticket")
            print("4. View My Bookings")
            print("5. Cancel a Booking")
            print("6. Make Payment")
            print("7. Logout")
            choice = input("Enter choice: ")
            if choice == '1':
                self.movie_service.show_movies()
            elif choice == '2':
                self.theatre_service.show_theaters()
            elif choice == '3':
                user_email = self.db.fetchone(
                    "SELECT email FROM users WHERE id = %s", (user['id'],))['email']
                self.booking_service.book_ticket(user['id'], user_email)
            elif choice == '4':
                self.booking_service.show_bookings(user['id'])
            elif choice == '5':
                self.booking_service.cancel_booking(user['id'])
            elif choice == '6':
                booking_id = input("Enter Booking ID to make payment: ")
                self.payment_service.initiate_payment(booking_id)
            elif choice == '7':
                print("Logging out...")
                break
            else:
                print("Invalid choice.")

    def admin_panel_menu(self):
        password = input("Enter admin password: ")
        # In production, validate against a secure hash or environment variable.
        if password != "admin123":
            print("Invalid admin credentials.")
            return
        while True:
            print("\n--- Admin Panel ---")
            print("1. View All Bookings")
            print("2. View All Payments")
            print("3. Cancel a Booking")
            print("4. Back to Main Menu")
            choice = input("Enter choice: ")
            if choice == '1':
                self.admin_panel.view_bookings()
            elif choice == '2':
                self.admin_panel.view_payments()
            elif choice == '3':
                self.admin_panel.cancel_booking()
            elif choice == '4':
                break
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    app = MovieBookingApp()
    app.main_menu()