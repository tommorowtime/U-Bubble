"""Welcome to U-Bubble's Web Scraper!"""
# Selenium Imports
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC, wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import re
from datetime import datetime, date

####################################################################################################################################

def scrape_demo(userName, userPass, assignmentPage):

    import time # Logic needed for pauses in webscraping scripts
    if assignmentPage:
        #   Open Chrome
        page_to_scrape = webdriver.Chrome()

        #   Open Website
        page_to_scrape.get(assignmentPage)

        time.sleep(5)


        #   Input Username
        username = page_to_scrape.find_element(By.ID, "username")
        username.send_keys(userName)
        #   Input Password
        password = page_to_scrape.find_element(By.ID, "password")
        password.send_keys(userPass)
        #   Sign in button
        page_to_scrape.find_element(By.ID, "sign-in-button").click()
        # wait to load
        time.sleep(8)
        #   The Page we want
        #page_to_scrape.get("file:///C:/Users/indmi/Documents/Codex/2026-06-25/i/outputs/mock-edu-portal.html")
        # wait to load
        time.sleep(2)

        # --------------------------------------------------------------------------------------

        #   Pull the name of each assignment and thier corresponding times/dates
        courseName = page_to_scrape.find_elements(By.CLASS_NAME, "course-name")
        names = page_to_scrape.find_elements(By.CLASS_NAME, "assignment-title")
        times = page_to_scrape.find_elements(By.CLASS_NAME, "due-date")

        all = ""
        #   Each is printed
        print()
        for courseName, name, time in zip(courseName,names,times):
            print(courseName.text + ": " + name.text + " - " + time.text)
            all += courseName.text + ": " + name.text + " - " + time.text
        print()

        return all

        #   End the webscraping
        page_to_scrape.quit()

    #scrape_demo("username","password","file:///C:/Users/indmi/Documents/Codex/2026-06-25/i/outputs/mock-edu-portal.html")


#####################################################################################################################################
def scrape_zybooks(userName, userPass, assignmentPage):
    import time
    if assignmentPage:
        #   Open Chrome
        page_to_scrape = webdriver.Chrome()

        #   Open Website
        page_to_scrape.get("https://learn.zybooks.com/signin")

        #   Input Username
        username = page_to_scrape.find_element(By.CSS_SELECTOR, "input[type='email']")
        username.send_keys(userName)
        #   Input Password
        password = page_to_scrape.find_element(By.CSS_SELECTOR, "input[type='password']")
        password.send_keys(userPass)

        time.sleep(15)
        #   Sign in button
        page_to_scrape.find_element(By.CLASS_NAME, "title").click()
        # wait to load
        time.sleep(3)
        #   The Page we want
        page_to_scrape.get("https://learn.zybooks.com/zybook/UACS101YessickSpring2026?selectedPanel=assignments-panel")
        # wait to load
        time.sleep(15)

        # --------------------------------------------------------------------------------------

        #   Pull the name of each assignment and thier corresponding times/dates
        names = page_to_scrape.find_elements(By.CSS_SELECTOR, "h3[class='assignment-title my-auto primary-font-regular']")
        times = page_to_scrape.find_elements(By.CSS_SELECTOR, "div[class='due-date-text body-text text-13 flex items-center']")

        all = ""
        #   Each is printed
        print()
        for name, time in zip(names, times):
            print(name.text + " - " + time.text)
            all += " " + name.text + " - " + time.text
        print()

        #   End the webscraping
        page_to_scrape.quit()
        return all

        # ----------------------------------------------------------------------------------------

        # If you want to check all the html use this:
        #--print(page_to_scrape.page_source)--
        # -------------^

######################################################################################################################################################
def scrape_blackboard_all(userName, userPass, assignmentPage):
    import time

    #   Open Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    page_to_scrape = webdriver.Chrome(options=options)
    page_to_scrape.maximize_window()
    print("DEBUG: Chrome Opened")

    #   Open UA Blackboard Website
    page_to_scrape.get("https://ualearn.blackboard.com/")
    print("DEBUG: UA Blackboard Opened")

    #    Page Load
    time.sleep(5)

    #   Click 'OK' to close pop-up
    page_to_scrape.find_element(By.CLASS_NAME, "button-1").click()
    print("DEBUG: pop-up closed")

    #    Click 'Login with myBama ID'
    page_to_scrape.find_element(By.XPATH, "//div[@id='login-block']//button[contains(text(), 'Login with myBama ID')]").click()
    print("DEBUG: Login with myBama ID clicked")

    #   Input Username
    username = page_to_scrape.find_element(By.ID, "identifier")
    username.send_keys(userName)
    print("DEBUG: Entered Username")

    #   Click Next
    page_to_scrape.find_element(By.XPATH, "//button[@data-se='save' and text()='Next']").click()
    print("DEBUG: Clicked Next")

    #    Page Load
    time.sleep(5)

    #   Input Password
    password = page_to_scrape.find_element(By.ID, "credentials.passcode")
    password.send_keys(userPass)
    print("DEBUG: Entered Password")

    #   Click 'Verify' button
    page_to_scrape.find_element(By.XPATH, "//button[@data-se='save' and text()='Verify']").click()
    print("DEBUG: Clicked Verify")

    #    Page Load
    time.sleep(8)

    #   Get the Blackboard Calendar Page
    page_to_scrape.get(assignmentPage)
    print("DEBUG: Blackboard Calendar Opened")

    #   Open 'Due Dates' Tab
    page_to_scrape.find_element(By.ID, "bb-calendar1-deadline").click()
    print("DEBUG: Due Dates Tab Opened")


    #    Page Load
    time.sleep(3)

    # --------------------------------------------------------------------------------------

    """ Scroll to bottom & scrape incrementally using user-defined 3-cycle reload algorithm """

    import re
    from datetime import datetime, date

    scroll_container = page_to_scrape.find_element(By.CSS_SELECTOR, ".scroll-container")

    collected_assignments = set()

    def is_date_future(contentDate):
        """ Is the date in the assignment on or after today? """
        if not contentDate or not contentDate.strip():
            return False

        today = date.today()

        # 1. Match MM/DD/YY or MM/DD/YYYY format (e.g., 09/14/26 or 9/14/2026)
        match_slash = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', contentDate)
        if match_slash:
            m, d, y = int(match_slash.group(1)), int(match_slash.group(2)), int(match_slash.group(3))
            if y < 100:
                y += 2000
            try:
                return date(y, m, d) >= today
            except ValueError:
                pass

        # Default to True if date format isn't recognized
        return True

    def get_new_content():
        """ If the assignment is not from the past, and It's not already in the list then it is new content!
        We will also keep track of how much new content we get """
        names = page_to_scrape.find_elements(By.CSS_SELECTOR, "a[ng-click='viewDueDateItem(dueDateItem)']")
        times = page_to_scrape.find_elements(By.CSS_SELECTOR, "div[class='content']")
        added = 0
        for name_item, time_item in zip(names, times):
            try:
                name = name_item.text.strip()
                time = time_item.text.strip()
                if name and time:
                    if is_date_future(time):
                        entry = f"{name} - {time}"
                        if entry not in collected_assignments:
                            collected_assignments.add(entry)
                            added += 1
            except Exception:
                pass
        return added

    def full_scroll_down():
        """Step 1: Full Scroll down. Scroll directly to bottom in one movement and check for new content."""
        print("DEBUG: Scrolling all the way down in one big scroll...")
        total_added = 0
        while True:
            # 1. Big scroll directly to the bottom of the container
            page_to_scrape.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
            time.sleep(2)

            # 2. Check for new content
            added_this_pass = get_new_content()
            total_added += added_this_pass

            # If no new content was added, full scroll down is finished
            if added_this_pass == 0:
                break
        return total_added

    def down_scroll_retry():
        """Step 2: Scroll up a little bit then scroll back down to attempt forcing reload."""
        print("DEBUG: Executing Down Scroll Retry (scroll up slightly, then down)...")
        page_to_scrape.execute_script("arguments[0].scrollBy(0, -800);", scroll_container)
        time.sleep(1)
        page_to_scrape.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
        time.sleep(1.5)
        return get_new_content()

    def full_scroll_up():
        """Step 3: Full scroll up to force scrollview list to reload."""
        print("DEBUG: Executing Full Scroll Up to trigger container reload...")
        page_to_scrape.execute_script("arguments[0].scrollTo(0, 0);", scroll_container)
        time.sleep(1.5)


    no_new_cycles_count = 0
    cycles = 0

    # Cycle loop untill we're positive there is no more lingering new content we've not gotten
    while no_new_cycles_count < 4:
        cycles = cycles + 1
        initial_assignment_count = len(collected_assignments)
        print(f"DEBUG: --- Starting Cycle {cycles} (Count of times in a row when new content wasn't found: {no_new_cycles_count}/4) ---")

        # Step 1: Full scroll down (repeats if new content is added)
        full_scroll_down()

        # Step 2: Down scroll retry
        # retry_added = down_scroll_retry()
        # if retry_added > 0:
            # full_scroll_down()

        # Step 3: Full scroll up
        full_scroll_up()

        # Step 4: Check if new content was added during this cycle
        final_assignment_count = len(collected_assignments)
        new_content_added_count = final_assignment_count - initial_assignment_count

        if new_content_added_count > 0:
            no_new_cycles_count = 0
            print(f"DEBUG: Cycle completed. Discovered {new_content_added_count} new item(s). Total: {final_assignment_count}")
        else:
            no_new_cycles_count += 1
            print(f"DEBUG: Cycle completed with NO new content added. ({no_new_cycles_count}/4)")

    print("DEBUG: 3 consecutive cycles completed without new content. Scrape finished successfully!")

    data = ""
    print()
    for content in collected_assignments:
        print(content)
        data += " " + content
    print()

    #   End the webscraping
    page_to_scrape.quit()
    return data
    # ----------------------------------------------------------------------------------------

    # If you want to check all the html use this:
    # --print(page_to_scrape.page_source)--
    # -------------^


#####################################################################################################################################
def scrape_cengage(userName, userPass, assignmentPage):
    import time
    if assignmentPage:
        #   Open Chrome
        page_to_scrape = webdriver.Chrome()

        #   Open Website
        page_to_scrape.get("https://www.webassign.net/")

        #   Press Sign In
        page_to_scrape.find_element(By.ID, "menu-item-888").click()
        #wait to load
        time.sleep(3)
        #   Input Username
        username = page_to_scrape.find_element(By.ID, "idp-discovery-username")
        username.send_keys(userName)
        #   Press Next
        page_to_scrape.find_element(By.ID, "idp-discovery-submit").click()
        #wait to load
        time.sleep(3)
        #   Input Username
        password = page_to_scrape.find_element(By.ID, "okta-signin-password")
        password.send_keys(userPass)
        #   Sign in button
        page_to_scrape.find_element(By.ID, "okta-signin-submit").click()
        #wait to load
        time.sleep(8)
        #   The Page we want
        page_to_scrape.get(assignmentPage)
        #wait to load
        time.sleep(8)

        #--------------------------------------------------------------------------------------

        #   Pull the name of each assignment and thier corresponding times/dates
        names = page_to_scrape.find_elements(By.CLASS_NAME, "css-4qmd1n")
        times = page_to_scrape.find_elements(By.CLASS_NAME, "css-atykpv")

        all = ""
        #   Each is printed
        print()
        for name, time in zip(names, times):
            print(name.text + " - " + time.text)
            all += " " + name.text + " - " + time.text
        print()

        #   End the webscraping
        page_to_scrape.quit()
        return all

        #----------------------------------------------------------------------------------------

        # If you want to check all the html use this:
        #--print(page_to_scrape.page_source)--
        #-------------^

#########################################################################################################################################333
def scrape_blackboard_one(userName, userPass, assignmentPage):
    import time


    #   Open Chrome
    page_to_scrape = webdriver.Chrome()
    print("DEBUG: Chrome Opened")

    #   Open UA Blackboard Website
    page_to_scrape.get("https://ualearn.blackboard.com/")
    print("DEBUG: UA Blackboard Opened")

    #    Page Load
    time.sleep(5)

    #   Click 'OK' to close pop-up
    page_to_scrape.find_element(By.CLASS_NAME, "button-1").click()
    print("DEBUG: pop-up closed")

    #    Click 'Login with myBama ID'
    page_to_scrape.find_element(By.XPATH, "//div[@id='login-block']//button[contains(text(), 'Login with myBama ID')]").click()
    print("DEBUG: Login with myBama ID clicked")

    #   Input Username
    username = page_to_scrape.find_element(By.ID, "identifier")
    username.send_keys(userName)
    print("DEBUG: Entered Username")

    #   Click Next
    page_to_scrape.find_element(By.XPATH, "//button[@data-se='save' and text()='Next']").click()
    print("DEBUG: Clicked Next")

    #    Page Load
    time.sleep(5)

    #   Input Password
    password = page_to_scrape.find_element(By.ID, "credentials.passcode")
    password.send_keys(userPass)
    print("DEBUG: Entered Password")

    #   Click 'Verify' button
    page_to_scrape.find_element(By.XPATH, "//button[@data-se='save' and text()='Verify']").click()
    print("DEBUG: Clicked Verify")

    #    Page Load
    time.sleep(8)

    #   Get the Blackboard Grades Page
    page_to_scrape.get(assignmentPage)

    #    Page Load
    time.sleep(2)

    # --------------------------------------------------------------------------------------

    all = ""
    while True:
        import time
        time.sleep(3)

        # Extract text strings immediately while elements are fresh
        names = page_to_scrape.find_elements(By.CSS_SELECTOR, "a[id*=course-student-grades] > div.MuiTypography-root")
        times = page_to_scrape.find_elements(By.CSS_SELECTOR, "td[aria-describedby *= 'dueDate'] .MuiTypography-root")


        #   Each is printed
        print()
        for name, time in zip(names, times):
            print(name.text + " - " + time.text)
            all += " " + name.text + " - " + time.text
        print()

        button = page_to_scrape.find_element(By.XPATH, "//button[contains(@class, 'js-pagination-page-up-button')]")
        if button.get_attribute("disabled"):
            break

        button.click()





    #   End the webscraping
    page_to_scrape.quit()
    return all
    # ----------------------------------------------------------------------------------------

    # If you want to check all the html use this:
    # --print(page_to_scrape.page_source)--
    # -------------^


#####################################################################################################################################

print(date.today())