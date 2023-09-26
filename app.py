# imports - standard imports
from datetime import datetime
from random import randint
import sqlite3

# imports - third party imports
from flask import Flask, render_template, request, redirect, flash
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.wrappers import response

# setting up Flask instance
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Library.db'

db = SQLAlchemy(app)

# Creating Tables

# Table Books for storing Books.
class Books(db.Model):
    # Table Books  => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued | 

    book_id = db.Column(db.Integer , primary_key = True)
    book_name = db.Column(db.String(150))
    author = db.Column(db.String(75))
    publisher = db.Column(db.String(75))
    quantity = db.Column(db.Integer , default = 1)
    borrower = db.Column(db.Integer , default = -1)
    isbn = db.Column(db.String(15))
    times_issued = db.Column(db.Integer , default = 0)
    
# Table Members for storing the member details.
class Members(db.Model):
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    member_id = db.Column(db.Integer , primary_key = True)
    member_name = db.Column(db.String(150))
    member_balance = db.Column(db.Float , default = 1000)
    member_borrowed = db.Column(db.Boolean, default = False)
    library_fees_given = db.Column(db.Float , default = 0)

# Table Transactions for storing all the transactions details.
class Transactions(db.Model):
    # Table Transactions => | _id | book_name | member_name | direction | time |

    _id = db.Column(db.Integer , primary_key = True)
    book_name =  db.Column(db.String(150))
    member_name = db.Column(db.String(150))
    direction = db.Column(db.Boolean, default = True)
    time = db.Column(db.DateTime , default = datetime.utcnow)

@app.route('/')
def home():
    available_books = Books.query.all()
    return render_template('home.html' , books = available_books)


@app.route('/members', methods = ["POST" , "GET"])
def members():
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |


    if request.method == "POST":

        user_name = request.form['user_name']    
        member_balance = request.form['balance'] 

        if not is_alphabets(user_name): 
            message = "Please enter correct User-Name"
            return render_template('error.html', message = message, page = "members")
        
        if not member_balance.isnumeric():
            message = "Please enter correct balence"
            return render_template('error.html',
                                    message = message,
                                    page = "members"
                                    )
        
        try:
            
            member = Members(
                            member_name=user_name,
                            member_balance = float(member_balance)
                            ) 
                            
            db.session.add(member)  
            db.session.commit()     
            
        except:

            return render_template('error.html', message = "Unexpected Error, Cannot add Member")

    members = Members.query.all()                               
    return render_template('members.html', members = members)   
        

@app.route('/transactions')
def transactions():
    # Table Transactions => | _id | book_name | member_name | direction | time |

    transactions = Transactions.query.order_by(Transactions.time.desc()).all() #sort from most recent
    return render_template('transactions.html', transactions = transactions)

# Logic for renting out a book
@app.route('/rent_out/<int:book_id>', methods = ["POST" , "GET"])
def rent_out(book_id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued
    # Table members      => | member_id| member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |

    # Members with a clean slit - no book borrowed
    all_members = Members.query.filter(
                            Members.member_borrowed == False
                            ).all()

    if request.method == "POST":

        id_of_the_member = request.form['id']

        if not id_of_the_member.isnumeric():
            return render_template('error.html', message = "Enter a numeric value")

        # Get form data.
        member = Members.query.get(int(id_of_the_member))
        
        if member == None:
            return render_template('error.html', message = "Not A Member!")

        if member.member_balance < -500:

            message = f" {member.member_name}'s balance is {member.member_balance} \
            which is less than -500, kindly top up before borrowing books."

            return render_template('error.html', message = message)
        
        if member.member_borrowed==True:
            # User has already borrowed a book.

            message = f"{member.member_name} has already Borrowed a book and is not currently eligible "
            return render_template('error.html' , message= message)
        

        try:
            member.member_borrowed = True   
            member.member_balance -= 500   
            member.library_fees_given += 500   

            book = Books.query.get(book_id)  
            if book == None:
                return render_template('error.html', message = "Book is in our system")
                
            book.quantity = 0   
            book.times_issued += 1  # book's Time issued is increased by 1.
            book.borrower = member.member_id    # Book's borrower is set to the id of member's id.

            # New transaction is registered and added to transactions.
            trans = Transactions(
                                book_name = book.book_name,
                                member_name = member.member_name,
                                direction = False
                                )

            db.session.add(trans)
            db.session.commit()

            return redirect(url_for('home'))

        except:

            return render_template(
                                'error.html',
                                message = "Unexpected Error Occured"
                                )
        
    return render_template(
                        'rent_out.html',
                        id = book_id,
                        members = all_members
                        )

# @app.route('/addBooks', methods = ["POST" , "GET"])
# def addBooks():

#     if request.method == "POST":

#         # Gets the data from The API.
#         response = make_API_call()

#         # going through data.
#         for data in response:

#             # book ID from the form.
#             book_id = int(data["bookID"])

#             # Does book exist in db or not
#             to_find = Books.query.get(book_id)

#             if to_find == None:

#                 # add if not in db.
#                 book = Books(
#                             book_id = book_id,
#                             book_name = data["title"],
#                             author = data["authors"],
#                             publisher =data["publisher"],
#                             isbn = data["isbn"]
#                             )

#                 db.session.add(book)
#                 db.session.commit()
            
#         return redirect(url_for('home'))

#     else:
#         return render_template('add_books.html')


@app.route('/addBooks', methods=["POST", "GET"])
def addBooks():
    if request.method == "POST":
    # Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

        book_id = request.form['book_id']
        book_name = request.form['book_name']
        author = request.form['author']
        publisher = request.form['publisher']
        isbn = request.form['isbn'] or 404

        # Is value valid and does book_id exist
        
        if not book_id.isnumeric():
            return render_template(
                                'error.html',
                                message = "Book ID does not exist. Please enter a valid book ID"
                                )
        
        book_id = int(book_id)
        if Books.query.get(book_id) != None:
            return render_template('error.html', message = "Book Id already Exists in the Database")

        # every thing is valid 
        try:
            book = Books(
                        book_id = book_id,
                        book_name = book_name,
                        author = author,
                        publisher = publisher,
                        isbn = isbn
                        )

            db.session.add(book)
            db.session.commit()
            return redirect(url_for('home'))

        except:
            return render_template('error.html', message = "Unexpected Error")
        
    else:
        return render_template('add_books.html')


# renders all the books which are currently rented Out.
@app.route('/return_book')
def return_book():

    #  Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

    books = Books.query.filter(
                        Books.quantity == 0     # render only those books which have been issued
                        ).all()

    return render_template(
                        'return_book.html',
                        books = books
                        )


# This is the function which reverts the data to its initial stage
@app.route('/summary/<int:id>')
def summary(id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued | 
    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |

    book = Books.query.get(id)                  # get The book.
    book.quantity = 1                           # set its quantity to 1 again.
    member = Members.query.get(book.borrower)   # get the member using borrower column.

    # get the old transaction to get the time at which the book was issued.
    old_trans = Transactions.query.filter(
        Transactions.book_name == book.book_name
        ).first()

    # create a new transaction for the return of book
    trans = Transactions(
                        book_name = book.book_name,
                        member_name = member.member_name,
                        direction = True
                        )

    db.session.add(trans)   # Add it to the session.
    book.borrower = -1  # set the borrower to -1 again as it has no borrower now.

    # Calculate the balance of member by the formula => 10 * number of days for which the book was borrowed
    charges = (datetime.utcnow() - old_trans.time).days * 10

    # deduct the amount from the members wallet
    member.member_balance -= charges

    # add the amount deducted by the user wallet to the library profits
    member.library_fees_given += charges
    
    member.member_borrowed = False  # set this property to False as the member has not borrowed a book.
    db.session.commit()     # commit changes.

    return render_template('summary.html', member = member)


@app.route('/delete_member/<int:id>')
def delete(id):

    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    try:

        task_to_delete =  Members.query.get(id)
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/members')

    except:

        return render_template('error.html', message = "Unexpected Error Occured")


@app.route('/update/<int:id>', methods = ["POST", "GET"])
def update(id):

    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    if request.method == "POST":
        try:

            user = Members.query.get(id)
            user.member_balance += float(request.form['amount'])
            db.session.commit()
            return redirect(url_for('members'))

        except:

            return render_template('error.html', message = "Unexpected Error Occured")
    else:
        return render_template('update.html', id = id)


# Helper Functions
# checks if a string is alphabetical
def is_alphabets(s : str):
    return ''.join(s.split()).isalpha() 

# Removes unnecessary spaces between characters
def remove_spaces(s : str):
    return ' '.join(s.split())


if __name__ == '__main__':
    app.run(debug=True)
    db.create_all()