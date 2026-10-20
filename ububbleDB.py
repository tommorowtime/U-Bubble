"""Welcome to U-Bubble's Local Database!"""
# Imports: SQLite and Kivy App for notification handling
import sqlite3
from kivymd.app import MDApp
###################################################################################################################################
# Internal Imports
from Assignment_WEB import (
    scrape_cengage, scrape_zybooks, scrape_blackboard_all, scrape_blackboard_one, scrape_demo
)
######################################################################################################################################

# Global variable to hold the in-memory database connection
mem_connection = None

def get_mem_connection():
    """Creates and returns a single in-memory database connection.Initializes tables if the connection is new."""
    global mem_connection
    if mem_connection is None:
        mem_connection = sqlite3.connect(':memory:')
        control = mem_connection.cursor()
        # Create login table for in-memory use
        control.execute("""CREATE TABLE IF NOT EXISTS
            login (name TEXT, username TEXT, password TEXT, isSigned TEXT)
        """)
        # Create class table for in-memory use
        control.execute("""CREATE TABLE IF NOT EXISTS
            class (classname TEXT, webname TEXT, classid TEXT, assignmentpage TEXT, isSigned TEXT)
        """)
        # Create account table for in-memory use
        control.execute("""CREATE TABLE IF NOT EXISTS
            account (username TEXT, pin INTEGER)
        """)
    return mem_connection


def create_login_table():
    connection = sqlite3.connect('ububble.db')

    control = connection.cursor()

    control.execute("""CREATE TABLE IF NOT EXISTS
    
        login (name TEXT, username TEXT, password TEXT, isSigned TEXT)
    
    """)

    connection.commit()
    connection.close()

def create_class_table():
    connection = sqlite3.connect('ububble.db')

    control = connection.cursor()

    control.execute("""CREATE TABLE IF NOT EXISTS
            class (classname TEXT, webname TEXT, classid TEXT, assignmentpage TEXT, isSigned TEXT)
        """)

    connection.commit()
    connection.close()

def create_account_table():
    connection = sqlite3.connect('ububble.db')

    control = connection.cursor()

    control.execute("""CREATE TABLE IF NOT EXISTS

        account (username TEXT, pin INTEGER)

    """)

    connection.commit()
    connection.close()

########################################################################################################################
def send_login(name, userName, userPass, isSigned):
    """Send login info to DB"""
    data = (name, userName, userPass, isSigned)

    if isSigned != "user":
        # User is signed in and the login will be saved to their account

        connection = sqlite3.connect("ububble.db")

        control = connection.cursor()

        create_login_table()

        control.execute("INSERT OR IGNORE INTO login VALUES (?, ?, ?, ?)", data)

        connection.commit()
        connection.close()

        MDApp.get_running_app().show_notif(name + " site has been connected!", "success")
        print( name + "site has been connected!")
        return name

    else:
        # save login to temp memory
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("INSERT OR IGNORE INTO login VALUES (?, ?, ?, ?)", data)
        memConnection.commit()
        # Do not close the connection, as it's shared.

        MDApp.get_running_app().show_notif(name + " site has been connected!", "success")
        print(name + " site has been connected! (in memory)")
        return name

def get_login(name,isSignedIn):
    """Get login info from DB"""
    if isSignedIn != "user":
        create_login_table()
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT * FROM login WHERE isSigned=? AND name=?", (isSignedIn, name))
        login = control.fetchall()
        connection.close()
        if login:
            print(login[0][0])
            return login[0][0]
        else:
            return ""
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("SELECT * FROM login WHERE isSigned=? AND name=?", (isSignedIn, name))
        login = memControl.fetchall()
        if login:
            print(login[0][0])
            return login[0][0]
        else:
            return ""

def get_connected_websites(isSignedIn):
    """Get all connected websites for the user from DB"""
    if isSignedIn != "user":
        create_login_table()
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT name FROM login WHERE isSigned=?", (isSignedIn,))
        logins = control.fetchall()
        connection.close()
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("SELECT name FROM login WHERE isSigned=?", (isSignedIn,))
        logins = memControl.fetchall()

    websites = []
    for login in logins:
        site = login[0]
        if site not in websites:
            websites.append(site)
        if site == "blackboard" and "blackboard1" not in websites:
            websites.append("blackboard1")
    return websites

def delete_login(name, isSignedIn):
    """Delete login info from DB"""
    if isSignedIn != "user":
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("DELETE FROM login WHERE name=? AND isSigned=?", (name, isSignedIn))
        connection.commit()
        connection.close()
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("DELETE FROM login WHERE name=? AND isSigned=?", (name, isSignedIn))
        memConnection.commit()
############################################################################################################
def recieve_scraped(classname, name, isSigned):
    """Send webscraper to get raw text of assignments based off of the connected websites and signed in user"""
    if isSigned != "user":
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT * FROM login")
        logins = control.fetchall()
    else:
        print("Working in memory...")
        connection = get_mem_connection()
        memControl = connection.cursor()
        memControl.execute("SELECT * FROM login")
        logins = memControl.fetchall()

    all_data = []

    for login in logins:

        # Collection of Classes
        if name == login[0] == "demo" and login[3] == isSigned:
            all_data += scrape_demo(login[1], login[2], get_page(classname, "demo", isSigned))

        if name == "blackboard" and login[0] == "blackboard" and login[3] == isSigned:
            all_data += scrape_blackboard_all("BB Class", login[1], login[2], get_page(classname, "blackboard", isSigned))

        # Singular Classes
        if name == login[0] == "cengage" and login[3] == isSigned:
            all_data += scrape_cengage(classname, login[1], login[2], get_page(classname, "cengage", isSigned))

        if name == "zybooks" and login[0] == "zybooks" and login[3] == isSigned:
            all_data += scrape_zybooks(classname, login[1], login[2], get_page(classname, "zybooks", isSigned))

        if name == "blackboard1" and login[0] == "blackboard" and login[3] == isSigned:
            all_data += scrape_blackboard_one(classname, login[1], login[2], get_page(classname, "blackboard1", isSigned))



    return all_data

def all_scraped(isSigned):
    """Scrape ALL classes"""
    if isSigned != "user":
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT * FROM class")
        classes = control.fetchall()
    else:
        print("Working in memory...")
        connection = get_mem_connection()
        memControl = connection.cursor()
        memControl.execute("SELECT * FROM class")
        classes = memControl.fetchall()

    all_data = ""

    for clas in classes:

        if clas[4] == isSigned:
            all_data = recieve_scraped(clas[0], clas[1], clas[4])

    if all_data:
        return all_data
    else:
        MDApp.get_running_app().show_notif("You have no classes to scrape.", "error")



def get_page(cn, dbSite, isSignedIn):
    """Get assignment page from DB"""
    if isSignedIn != "user":
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT * FROM class WHERE webname=? AND classname=?", (dbSite,cn))
        classItem = control.fetchall()
        connection.close()
        if classItem:
            return classItem[0][3]
        else:
            print("No page found")
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("SELECT * FROM class WHERE webname=?", (dbSite,))
        classItem = memControl.fetchall()
        if classItem:
            return classItem[0][3]
        else:
            print("No page found")


################################################################################################################################################

def send_class(classname, webname, classid, assignmentpage, isSignedIn):
    """Send class info to DB"""
    data = (classname, webname, classid, assignmentpage, isSignedIn)

    if isSignedIn != "user":
        create_class_table()

        connection = sqlite3.connect("ububble.db")

        control = connection.cursor()

        control.execute("""CREATE TABLE IF NOT EXISTS

                        class (classname TEXT, webname TEXT, classid TEXT, assignmentpage TEXT, isSigned BLOB)

                    """)

        control.execute("INSERT OR IGNORE INTO class VALUES (?, ?, ?, ?, ?)", data)

        connection.commit()
        connection.close()

        print(classname + " has been added and can now be scraped!")

    else:

        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        # The table is now created in get_mem_connection, and the schema is corrected.
        # The data tuple has 5 elements, so we need 5 placeholders.
        memControl.execute("INSERT OR IGNORE INTO class VALUES (?, ?, ?, ?, ?)", data)
        memConnection.commit()
        # Do not close the connection.

        print(classname + " has been added and can now be scraped!")

def get_classes(isSignedIn):
    """Get classes from DB"""
    if isSignedIn != "user":
        create_class_table()
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("SELECT classname, webname, assignmentpage FROM class WHERE isSigned=?", (isSignedIn,))
        classes = control.fetchall()
        connection.close()
        return classes
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("SELECT classname, webname, assignmentpage FROM class WHERE isSigned=?", (isSignedIn,))
        classes = memControl.fetchall()
        return classes

def edit_class(isSignedIn,newname, newweb, newpage, oldname):
    """Update class in DB"""
    if isSignedIn != "user":
        create_class_table()
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute(("UPDATE class SET classname = ?, webname = ?, assignmentpage = ? WHERE classname = ?"), (newname, newweb, newpage, oldname))
        connection.commit()
        connection.close()
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute(("UPDATE class SET classname = ?, webname = ?, assignmentpage = ? WHERE classname = ?"), (newname, newweb, newpage, oldname))
        memConnection.commit()

def delete_class(classname, isSignedIn):
    """Delete class from DB"""
    if isSignedIn != "user":
        connection = sqlite3.connect('ububble.db')
        control = connection.cursor()
        control.execute("DELETE FROM class WHERE classname=? AND isSigned=?", (classname, isSignedIn))
        connection.commit()
        connection.close()
    else:
        memConnection = get_mem_connection()
        memControl = memConnection.cursor()
        memControl.execute("DELETE FROM class WHERE classname=? AND isSigned=?", (classname, isSignedIn))
        memConnection.commit()

######################################################################################################################################
def send_account(username, pin):
    """Add account to DB"""
    data = (username,pin)
    connection = sqlite3.connect('ububble.db')
    control = connection.cursor()
    create_account_table()

    # Query to check if the specific account already exists
    control.execute("SELECT * FROM account WHERE username = ? AND pin = ?", data)
    existing_account = control.fetchone()

    if existing_account:
        print("Signing you back in...")
        MDApp.get_running_app().show_notif("Signing you back in...", "success")
        connection.close()
        return retrieve_account(username, pin)
    else:
        control.execute("INSERT OR IGNORE INTO account VALUES (?,?)", data)
        print("Creating your account...")
        MDApp.get_running_app().show_notif("Creating your account...", "success")
        connection.commit()
        connection.close()
        return username

def retrieve_account(_username,_pin):
    """Retrieve account from DB"""
    connection = sqlite3.connect('ububble.db')
    control = connection.cursor()
    control.execute("SELECT * FROM account WHERE username = ? AND pin = ?", (_username, _pin))
    sign = control.fetchall()
    connection.close()

    if sign:
        return sign[0][0]
    return None
##########################################################################################################################################

"""Manually delete Tables & Data"""
#connection = sqlite3.connect('ububble.db')
#control = connection.cursor()
#control.execute("DROP TABLE class")
#control.execute(" DELETE FROM login WHERE name = 'demo' ")
#connection.commit()
#connection.close()

