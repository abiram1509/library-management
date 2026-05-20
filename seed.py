from app import create_app, db
from app.models import Genre, Book, User, Subscription
import bcrypt
from datetime import date, timedelta

app = create_app()


with app.app_context():
    # GENRES FIRST
    genres = ['Fiction', 'Non-Fiction', 'Science', 'Technology',
              'History', 'Biography', 'Self-Help', 'Mystery',
              'Fantasy', 'Romance']
    
    for g in genres:
        existing = Genre.query.filter_by(name=g).first()
        if not existing:
            db.session.add(Genre(name=g))
    db.session.commit()
    print("Genres done!")

    # BOOKS (your existing list stays here)
    
    books = [
        # Technology
        Book(title='Clean Code', author='Robert C. Martin', isbn='978-0132350884', genre_id=4, price=499, total_copies=3, available_copies=3),
        Book(title='The Pragmatic Programmer', author='Andrew Hunt', isbn='978-0135957059', genre_id=4, price=599, total_copies=2, available_copies=2),
        Book(title='Python Crash Course', author='Eric Matthes', isbn='978-1593279288', genre_id=4, price=449, total_copies=2, available_copies=2),
        Book(title='Introduction to Algorithms', author='Thomas H. Cormen', isbn='978-0262033848', genre_id=4, price=899, total_copies=2, available_copies=2),
        Book(title='You Don\'t Know JS', author='Kyle Simpson', isbn='978-1491924464', genre_id=4, price=349, total_copies=3, available_copies=3),

        # Fiction
        Book(title='The Alchemist', author='Paulo Coelho', isbn='978-0062315007', genre_id=1, price=299, total_copies=3, available_copies=3),
        Book(title='The Great Gatsby', author='F. Scott Fitzgerald', isbn='978-0743273565', genre_id=1, price=199, total_copies=3, available_copies=3),
        Book(title='To Kill a Mockingbird', author='Harper Lee', isbn='978-0061935466', genre_id=1, price=249, total_copies=2, available_copies=2),
        Book(title='1984', author='George Orwell', isbn='978-0451524935', genre_id=1, price=199, total_copies=3, available_copies=3),
        Book(title='The Catcher in the Rye', author='J.D. Salinger', isbn='978-0316769174', genre_id=1, price=229, total_copies=2, available_copies=2),

        # Science
        Book(title='A Brief History of Time', author='Stephen Hawking', isbn='978-0553380163', genre_id=3, price=399, total_copies=2, available_copies=2),
        Book(title='Sapiens', author='Yuval Noah Harari', isbn='978-0062316097', genre_id=3, price=549, total_copies=2, available_copies=2),
        Book(title='The Selfish Gene', author='Richard Dawkins', isbn='978-0198788607', genre_id=3, price=449, total_copies=1, available_copies=1),
        Book(title='Cosmos', author='Carl Sagan', isbn='978-0345539434', genre_id=3, price=499, total_copies=2, available_copies=2),
        Book(title='The Gene', author='Siddhartha Mukherjee', isbn='978-1476733524', genre_id=3, price=599, total_copies=1, available_copies=1),

        # Self-Help
        Book(title='Atomic Habits', author='James Clear', isbn='978-0735211292', genre_id=7, price=399, total_copies=3, available_copies=3),
        Book(title='Deep Work', author='Cal Newport', isbn='978-1455586691', genre_id=7, price=349, total_copies=2, available_copies=2),
        Book(title='Think and Grow Rich', author='Napoleon Hill', isbn='978-1585424337', genre_id=7, price=249, total_copies=3, available_copies=3),
        Book(title='The 7 Habits of Highly Effective People', author='Stephen Covey', isbn='978-0743269513', genre_id=7, price=349, total_copies=2, available_copies=2),
        Book(title='Man\'s Search for Meaning', author='Viktor Frankl', isbn='978-0807014271', genre_id=7, price=299, total_copies=2, available_copies=2),

        # History
        Book(title='Guns, Germs, and Steel', author='Jared Diamond', isbn='978-0393317558', genre_id=5, price=499, total_copies=2, available_copies=2),
        Book(title='The Diary of a Young Girl', author='Anne Frank', isbn='978-0553296983', genre_id=5, price=249, total_copies=3, available_copies=3),
        Book(title='India After Gandhi', author='Ramachandra Guha', isbn='978-0330396110', genre_id=5, price=699, total_copies=1, available_copies=1),
        Book(title='The Discovery of India', author='Jawaharlal Nehru', isbn='978-0195623598', genre_id=5, price=449, total_copies=2, available_copies=2),

        # Biography
        Book(title='Steve Jobs', author='Walter Isaacson', isbn='978-1451648539', genre_id=6, price=599, total_copies=2, available_copies=2),
        Book(title='Elon Musk', author='Walter Isaacson', isbn='978-1982181284', genre_id=6, price=699, total_copies=2, available_copies=2),
        Book(title='The Story of My Experiments with Truth', author='Mahatma Gandhi', isbn='978-0807059098', genre_id=6, price=299, total_copies=3, available_copies=3),
        Book(title='Wings of Fire', author='A.P.J. Abdul Kalam', isbn='978-8173711466', genre_id=6, price=199, total_copies=3, available_copies=3),

        # Mystery
        Book(title='The Girl with the Dragon Tattoo', author='Stieg Larsson', isbn='978-0307949486', genre_id=8, price=349, total_copies=2, available_copies=2),
        Book(title='Gone Girl', author='Gillian Flynn', isbn='978-0307588371', genre_id=8, price=299, total_copies=2, available_copies=2),
        Book(title='The Da Vinci Code', author='Dan Brown', isbn='978-0307474278', genre_id=8, price=349, total_copies=3, available_copies=3),

        # Fantasy
        Book(title='Harry Potter and the Philosopher\'s Stone', author='J.K. Rowling', isbn='978-0439708180', genre_id=9, price=399, total_copies=3, available_copies=3),
        Book(title='The Hobbit', author='J.R.R. Tolkien', isbn='978-0547928227', genre_id=9, price=349, total_copies=2, available_copies=2),
        Book(title='The Name of the Wind', author='Patrick Rothfuss', isbn='978-0756404079', genre_id=9, price=449, total_copies=1, available_copies=1),

        # Non-Fiction
        Book(title='Outliers', author='Malcolm Gladwell', isbn='978-0316017930', genre_id=2, price=349, total_copies=2, available_copies=2),
        Book(title='Thinking, Fast and Slow', author='Daniel Kahneman', isbn='978-0374533557', genre_id=2, price=499, total_copies=2, available_copies=2),
        Book(title='The Power of Now', author='Eckhart Tolle', isbn='978-1577314806', genre_id=2, price=299, total_copies=2, available_copies=2),
    ]
    for b in books:
        existing = Book.query.filter_by(isbn=b.isbn).first()
        if not existing:
            db.session.add(b)
    db.session.commit()
    print("Books done!")