""" Welcome to U-Bubble's connection to Google!: Google Tasks, OAuth 2.0 """
# Google Imports
import re
import time
import json
import os.path
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
########################################################################################################################

def split_due_date_time(due_date_str):
    """Separate a string like '9/11/26, 11:59 PM (CDT)' into ('YYYY-MM-DD', 'HH:MM am/pm')."""
    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', str(due_date_str))
    if date_match:
        m, d, y = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        if y < 100:
            y += 2000
        due_date = f"{y:04d}-{m:02d}-{d:02d}"
    else:
        due_date = str(due_date_str).strip()

    time_match = re.search(r'(\d{1,2}:\d{2}\s*[aApP][mM])', str(due_date_str))
    due_time = time_match.group(1).lower() if time_match else "11:59 pm"

    return due_date, due_time

def split_title_and_type(title_str):
    """Separate a title like 'Assignment: Impact of Credit Scores' into ('Impact of Credit Scores', 'Assignment')."""
    keywords = r'\b(Assignment|Quiz|Homework|HW|Project|Exam|Test|Lab|Discussion)\b'
    match = re.search(keywords, str(title_str), re.IGNORECASE)

    if match:
        assignment_type = match.group(1).capitalize()
        # Remove the keyword and any leftover ':' or '-' next to it
        short_title = re.sub(rf'{keywords}\s*[:\-]?\s*', '', str(title_str), count=1, flags=re.IGNORECASE).strip()
        # If removing the keyword leaves nothing (or just a number like '1' from 'Quiz 1'), keep the original title
        assignment_title = str(title_str).strip() if (not short_title or short_title.isdigit()) else short_title
    else:
        assignment_type = "Assignment"
        assignment_title = str(title_str).strip()

    return assignment_title, assignment_type

########################################################################################################################

def extract_assignments(assignments_json):
    assignments = json.loads(assignments_json) if isinstance(assignments_json, str) else assignments_json

    for item in assignments:
        item["due_date"], item["due_time"] = split_due_date_time(item.get("due_date", ""))
        item["assignment_title"], item["assignment_type"] = split_title_and_type(item.get("assignment_title", ""))

    print(f"DEBUG: {assignments}")
    return assignments

########################################################################################################################

try:
    from secret_config import CLIENT_CONFIG
except ImportError:
    CLIENT_CONFIG = {}

########################################################################################################################

def google_auth(force_refresh=False):
    """Connect to user Google account, connect to the U-Bubble app on Google Cloud, and connect to Google Tasks"""
    creds = None
    Tasks = ['https://www.googleapis.com/auth/tasks']

    # Have you signed in before? The token is what allows the software to get and edit data from the scope |google tasks|
    if os.path.exists('token.json') and not force_refresh:
        creds = Credentials.from_authorized_user_file('token.json', Tasks)

    # Expired access can get refreshed here
    if force_refresh or not creds or not creds.valid:
        should_reauth = False
        if not force_refresh and creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}. Deleting token and re-authenticating.")
                should_reauth = True
        else:
            should_reauth = True

        #the user will have to re-login to google if forcing refresh or token expired
        if should_reauth:
            if os.path.exists('token.json'):
                os.remove('token.json')

            if not CLIENT_CONFIG:
                raise ValueError("CLIENT_CONFIG is missing. Make sure secret_config.py exists.")
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, Tasks)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Create the service object to interact with Google Tasks
    return build('tasks', 'v1', credentials=creds)

########################################################################################################################

def sync_assignments_to_tasks(unfiltered_assignment_list):
    """Create Tasks from data and send to google tasks"""

    # filter assignments
    print("Assignments are being processed...")
    assignments = extract_assignments(unfiltered_assignment_list)
    if not assignments:
        return

    # connect to google (if not already)
    tasksconnect = google_auth()

    # ---Scan for duplicates across ALL lists & find/create "📚 School Work" list ---
    print("Scanning current tasks to prevent duplicates...")
    existing_task_titles = []
    target_list_name = "📚 School Work"
    school_list_id = None

    t_count = 0

    # Get all lists
    tasklists_result = tasksconnect.tasklists().list().execute()
    for t_list in tasklists_result.get('items', []):
       if t_list.get('title') == target_list_name:
           school_list_id = t_list['id']

       # Get all tasks in each list (showHidden=True includes completed tasks, False doesn't)
       tasks_result = tasksconnect.tasks().list(tasklist=t_list['id'], showHidden=True).execute()
       for t in tasks_result.get('items', []):
            if t_count < 100:
                # We save the title of up to 100 task you currently have or are completed
                existing_task_titles.append(t['title'])
                t_count = t_count + 1

    # Create "📚 School Work" list if it doesn't exist yet
    if not school_list_id:
        new_list = tasksconnect.tasklists().insert(body={'title': target_list_name}).execute()
        school_list_id = new_list['id']
        print(f"Created new Google Tasks list: {target_list_name}")

    # Sort furthest due date first so soonest assignments end up at the top of the list
    assignments.sort(key=lambda x: x['due_date'], reverse=True)

    # Get today's date for the past-due filter
    today = datetime.date.today()


    for item in assignments:

       due_date_obj = datetime.datetime.strptime(item['due_date'], "%Y-%m-%d").date()


       # Here, we're setting what the title will look like
       # Check if we're given a class_name, class_ID, or both (class_name would take priority in that case).
       type_emojis = {
           "Assignment": "📝",
           "Homework": "📓",
           "Hw": "📓",
           "Quiz": "⚡",
           "Exam": "🚨",
           "Test": "🚨",
           "Lab": "🧪",
           "Project": "🛠️",
           "Discussion": "💬"
       }
       type_emoji = type_emojis.get(item['assignment_type'], "📝")

       class_label = item['class_name'] or item['class_id'] or "College Class"
       formatted_title = (
                          f"{class_label} [{type_emoji} {item['assignment_type']}]"
                          f"                                                        "
                          f"{item['assignment_title']}                                              "
                          f"                                                         "
                          f"⏰ DUE {item['due_time']}"
                         )
       formatted_notes = f"🔗 link: {item['link']}"

       # Filter 1: Is it due today or in the future?
       if due_date_obj >= today:


           # Filter 2: Does it already exist?
           # We check if the base assignment title is ANYWHERE inside your existing tasks
           is_duplicate = any(formatted_title in existing_title for existing_title in existing_task_titles)


           if is_duplicate:
               print(f"Skipped duplicate: '{item['assignment_title']}' already exists.")
               continue  # This skips the rest of the loop and moves to the next assignment

           # If it's not a duplicate, build and insert it
           task_body = {
               'title': formatted_title,
               'notes': formatted_notes,
               'due': f"{item['due_date']}T00:00:00Z"
           }


           # Inserting into your "📚 School Work" list
           result = tasksconnect.tasks().insert(tasklist=school_list_id, body=task_body).execute()
           print(f"Successfully added: {' '.join(result.get('title', '').split())} | Task ID: {result.get('id')}")


           time.sleep(1)  # Prevent 429 errors
       else:
           print(f"Skipped past assignment: {item['assignment_title']} (Was due: {item['due_date']})")


    print("\nAll future, non-duplicate assignments have been synced to your Google Tasks!")




### JSON list of objects - each JSON should follow this schema:
### {
###     "class_name": "The class name created by the user from the app screen, could be None",
###     "assignment_type": "parsed keyword from the assignment name",
###     "assignment_title": "The assignment name with the keyword removed or shortened",
###     "due_date": "assignment due date",
###     "due_time": "assignment due time",
###     "link": "URL directly to the assignment",
###     "class_id": "May be used for the class name label in the tasks if 'class_name' is not provided",
###
### }



###DEBUG - Check for existing lists
def check_task_lists():
   service = google_auth()


   # Ask Google for all your task lists
   results = service.tasklists().list(maxResults=10).execute()
   items = results.get('items', [])


   print("\n--- Your Google Task Lists ---")
   if not items:
       print("No task lists found.")
   else:
       for item in items:
           print(f"List Name: {item['title']} | List ID: {item['id']}")


###DEBUG - Quick test for sync_assignments_to_tasks()
if __name__ == "__main__":
    fake_scraped_json = [
        {
            "class_name": "Personal Finance",
            "assignment_type": None,
            "assignment_title": "Assignment: Impact of Credit Scores on Personal Loans",
            "due_date": "11/11/26, 11:59 PM (CDT)",
            "due_time": None,
            "link": "https://ualearn.blackboard.com/ultra/courses/_123_1/outline/assessment/_456_1",
            "class_id": "FIN-101"
        },
        {
            "class_name": None,
            "assignment_type": None,
            "assignment_title": "Quiz 1",
            "due_date": "11/15/2026, 2:30 PM (CDT)",
            "due_time": None,
            "link": "https://ualearn.blackboard.com/ultra/courses/_789_1/outline/assessment/_101_1",
            "class_id": "CS-100"
        },
        {
            "class_name": "Intro to Biology",
            "assignment_type": None,
            "assignment_title": "Cell Structure Reading",
            "due_date": "9/02/25",
            "due_time": None,
            "link": "https://learn.zybooks.com/zybook/BIO101",
            "class_id": "BIO-101"
        }
    ]

    sync_assignments_to_tasks(fake_scraped_json)