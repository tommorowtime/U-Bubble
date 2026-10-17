"""Welcome to U-Bubble!"""
# Frontend Imports + "copy and paste function" import
import webbrowser
import pyperclip
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.animation import Animation
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.card import MDCard
from kivy.properties import StringProperty, ColorProperty, BooleanProperty
from kivy.core.window import Window
from kivymd.uix.button import MDFillRoundFlatButton
from kivy.uix.screenmanager import Screen
#######################################################################################################
# Internal Imports
from G_Tools import (
    google_auth, sync_assignments_to_tasks
)
from ububbleDB import (
    send_login, get_login, send_class, recieve_scraped,
    send_account, get_classes, delete_class, edit_class, delete_login, all_scraped
)
#########################################################################################################
# App Screens and their python logic, most functions are connected to buttons in the KV file
class MainScreen(Screen):

    def account_in(self):
        """Once the user signs in, the sign-in button changes color and says welcome to the user"""
        self.ids.sign_in_button.text = f"Welcome {MDApp.get_running_app().isSignedIn} !"
        self.ids.sign_in_button.md_bg_color = [0.67, 0.6, 0.66, 1]
        self.ids.sign_in_button.text_color = [1, 1, 1, 1]

    def account_out(self):
        """Once the user signs out, the sign-in button changes color and says sign in"""
        self.ids.sign_in_button.text = "Sign in"
        self.ids.sign_in_button.md_bg_color = [0.3, 0.2, 0.4, 1]
        self.ids.sign_in_button.text_color = [1, 1, 1, 1]

class SettingsScreen(Screen):

    def connect_google(self):
        """Authenticate the connection to google services so that we can modify tasks"""
        MDApp.get_running_app().show_notif("Opening browser for Google Authentication...","process")
        if google_auth(force_refresh=True):
            MDApp.get_running_app().show_notif("Successfully connected to Google!", "success")


    def get_gemini_key(self):
        """Send user to get their own api key, should be easy for them to find"""
        webbrowser.open("https://aistudio.google.com/app/apikey")
        MDApp.get_running_app().show_notif("Opening browser to get Gemini API Key...", "process")

    def save_api_key(self):
        """Have the api entered from the text field put in its own text file"""
        api_key = self.ids.api_key_field.text
        if api_key.strip():
            with open("api_key.txt", "w") as f:
                f.write(api_key.strip())
            MDApp.get_running_app().show_notif("Gemini API Key saved successfully!", "success")
        else:
            MDApp.get_running_app().show_notif("Please enter a valid API key.", "error")

    def choose_website(self, text):
        """If the selected website has already been connected, then when it's pressed, the user will be taken to a disconnect screen"""
        MDApp.get_running_app().websiteName = text
        if get_login(text, MDApp.get_running_app().isSignedIn) == text:
            MDApp.get_running_app().disconnect_mode = True
        else:
            MDApp.get_running_app().disconnect_mode = False
        self.manager.current = "enter web data"

    def load_settings(self):
        """Internal search for if a website is connected in the DB, if it is then the button turns green for that connection"""
        for site in ["blackboard", "zybooks", "cengage", "demo"]:
            if get_login(site, MDApp.get_running_app().isSignedIn) == site:
                self.ids[f"connect_{site}_button"].text = f"{site.capitalize()} Connected"
                self.ids[f"connect_{site}_button"].md_bg_color = [0.19, 0.8, 0.19, 1]
            else:
                self.ids[f"connect_{site}_button"].text = f"Connect {site.capitalize()}"
                self.ids[f"connect_{site}_button"].md_bg_color = [0.4, 0.3, 0.5, 1]

class ClassAddScreen(Screen):

    def save_to_class(self):
        """Create a class item and save it to the database"""
        classname = self.ids.class_name.text
        webname = self.ids.assignment_website.text
        assignmentpage = self.ids.assignment_page_input.text
        if classname == webname == assignmentpage == "":
            pass
            MDApp.get_running_app().show_notif("Text fields can not be empty", "error")
        else:
            send_class(classname, webname, "", assignmentpage, MDApp.get_running_app().isSignedIn)
            MDApp.get_running_app().show_notif(classname + " has been added and can now be scraped!", "success")

class SignInScreen(Screen):
    
    def sign_in(self):
        """Sign the user in, then the page changes to just a "Log out" button and send user back to main screen"""
        MDApp.get_running_app().isSignedIn = send_account(self.ids.username_field.text,self.ids.pin_field.text)
        self.ids.sign_in_card.opacity = 0
        self.ids.sign_in_card.disabled = True
        self.ids.sign_out_button.opacity = 1
        self.ids.sign_out_button.disabled = False
        self.manager.get_screen('main').account_in()
        
    def sign_out(self):
        """Sign the user out, then the page changes back to the option for the user to sign in"""
        MDApp.get_running_app().isSignedIn = "user"
        self.ids.sign_in_card.opacity = 1
        self.ids.sign_in_card.disabled = False
        self.ids.sign_out_button.opacity = 0
        self.ids.sign_out_button.disabled = True
        self.manager.get_screen('main').account_out()

class WebsiteDataScreen(Screen):
    def prepare_screen(self):
        """Switch between the original screen that asks user to sign in and a disconnect button only on the screen"""
        if MDApp.get_running_app().disconnect_mode:
            self.ids.website_data_card.opacity = 0
            self.ids.website_data_card.disabled = True
            self.ids.disconnect_button.opacity = 1
            self.ids.dis_label.opacity = 1
            self.ids.disconnect_button.disabled = False
            self.ids.dis_label.text = f"Disconnect from {MDApp.get_running_app().websiteName.capitalize()}?"
        else:
            self.ids.website_label.text = f"Connect to {MDApp.get_running_app().websiteName.capitalize()}"

    def reset_screen(self):
        """Reset connection screen back to how it's originaly viewed"""
        self.ids.website_data_card.opacity = 1
        self.ids.website_data_card.disabled = False
        self.ids.disconnect_button.opacity = 0
        self.ids.dis_label.opacity = 0
        self.ids.disconnect_button.disabled = True
        self.ids.username_field.text = ""
        self.ids.password_field.text = ""

    def save_to_login(self):
        """Save the user's login information to the database, "connect to website" """
        name = MDApp.get_running_app().websiteName
        userName = self.ids.username_field.text
        userPass = self.ids.password_field.text
        send_login(name, userName, userPass, MDApp.get_running_app().isSignedIn)
        MDApp.get_running_app().show_notif(f"{name.capitalize()} connected.", "success")
        self.manager.get_screen('settings').load_settings()
        self.manager.current = "settings"

    def disconnect_website(self):
        """Delete the user's login information from the database, aka "Disconnect from website" """
        website_name = MDApp.get_running_app().websiteName
        delete_login(website_name, MDApp.get_running_app().isSignedIn)
        MDApp.get_running_app().show_notif(f"{website_name.capitalize()} disconnected.", "success")
        self.manager.get_screen('settings').load_settings()
        self.manager.current = "settings"

class ClassEditScreen(Screen):
    # Clear Drop-down menu
    menu = None
    def open_menu(self):
        """Open the drop-down menu when clicked"""
        if self.menu:
            self.menu.open()

    def on_enter(self):
        """Populate drop-down menu with current classes"""
        class_names = get_classes(MDApp.get_running_app().isSignedIn)
        menu_items = [
            {
                "text": name[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=name[0], y=name[1], z=name[2]: self.set_item(x,y,z),
            } for name in class_names
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.class_dropdown_btn,
            items=menu_items,
            width_mult=4,
        )

    def set_item(self, classname, classweb, classpage):
        """Pre-fill the text fields with the selected class information"""
        self.ids.class_dropdown_btn.text = f"Selected: {classname}"
        self.menu.dismiss()
        self.ids.class_name.text = classname
        self.ids.assignment_website.text = classweb
        self.ids.assignment_page.text = classpage
        global oldname
        oldname = classname

    def edit(self):
        """Confirm the edit of the selected class information"""
        try:
            edit_class(MDApp.get_running_app().isSignedIn, self.ids.class_name.text, self.ids.assignment_website.text, self.ids.assignment_page.text, oldname)
            MDApp.get_running_app().show_notif(self.ids.class_name.text + " has been edited!", "success")
        except:
            MDApp.get_running_app().show_notif("No Class selected or Invalid Class", "error")

    def delete_class(self):
        """Confirm the deletion of the selected class"""
        try:
            delete_class(oldname, MDApp.get_running_app().isSignedIn)
            MDApp.get_running_app().show_notif(oldname + " has been deleted.", "success")
        except:
            MDApp.get_running_app().show_notif("No Class selected or Invalid Class", "error")

class ClassesScreen(Screen):
    def populate_classes(self):
        """Create buttons for each class created by the user"""
        self.ids.class_button_container.clear_widgets()
        classes = get_classes(MDApp.get_running_app().isSignedIn)
        for class_info in classes:
            btn = MDFillRoundFlatButton(
                text=class_info[0],
                on_release=lambda x, class_name=class_info[0], web_name=class_info[1]: self.update_panel(class_name, web_name),
                size_hint=(1, None),
                height="48dp"
            )
            self.ids.class_button_container.add_widget(btn)

    def update_panel(self, class_name, website_name):
        """Update the panel based off of the selected class"""
        self.ids.class_title.text = class_name
        self.ids.class_website.text = website_name

    def text_to_copy(self, text):
        """Show the user the text that they can copy to their clipboard"""
        self.ids.copy_box.text = text

    def copy_to_clipboard(self):
        """Copy the text to the clipboard"""
        pyperclip.copy(raw_text)
        MDApp.get_running_app().show_notif("Text copied to clipboard!", "success")

    def get_assignments_to_tasks(self):
        """Extract the info from the selected class and send it to google tasks or allow user to copy the raw text themselves"""
        MDApp.get_running_app().show_notif("Getting assignments...", "process")
        unfiltered_assignments = recieve_scraped(self.ids.class_title.text, self.ids.class_website.text, MDApp.get_running_app().isSignedIn)
        if unfiltered_assignments:
            sync_assignments_to_tasks(unfiltered_assignments)
            self.text_to_copy(str(unfiltered_assignments))
            MDApp.get_running_app().show_notif("assignments sent and available to copy","success")
        else:
            MDApp.get_running_app().show_notif("No assignments found to sync. Maybe sign in or connect a site.", "error")

    def extract_all(self):
        self.update_panel("All Classes", "--All--")
        MDApp.get_running_app().show_notif("Getting assignments...", "process")
        global raw_text
        raw_text = all_scraped(MDApp.get_running_app().isSignedIn)
        if raw_text:
            sync_assignments_to_tasks(raw_text)
            self.text_to_copy(raw_text)
            MDApp.get_running_app().show_notif("assignments sent and available to copy","success")
        else:
            MDApp.get_running_app().show_notif("No assignments found to sync. Maybe sign in or connect a site.", "error")

class TopNotification(MDCard):
    # initialize the notification text and it's color (purple by default)
    message_text = StringProperty("")
    message_color = ColorProperty([0.7, 0.3, 1, 1])

    def __init__(self, **kwargs):
        """Intitialize text and animation"""
        super().__init__(**kwargs)
        self.full_text = ""
        self.char_index = 0
        self.type_event = None

    def show(self, text, notif_type="process"):
        """Notification animation and colors based off of situation"""
        if notif_type == "error":
            self.message_color = [1, 0.3, 0.3, 1]
        elif notif_type == "success":
            self.message_color = [0.3, 1, 0.3, 1]
        else:
            self.message_color = [0.7, 0.3, 1, 1]
        self.full_text = text
        self.message_text = ""
        self.char_index = 0
        self.pos_hint = {"center_x": 0.5, "top": 1.2}
        anim = Animation(pos_hint={"center_x": 0.5, "top": 0.96}, duration=0.4, t="out_quad")
        anim.bind(on_complete=self.start_typing)
        anim.start(self)

    def start_typing(self, *args):
        """Typing animation for the notification"""
        if self.type_event:
            self.type_event.cancel()
        self.type_event = Clock.schedule_interval(self.type_next_char, 0.03)

    def type_next_char(self, dt):
        """Type the notification character by character then hide it at the end"""
        if self.char_index < len(self.full_text):
            self.message_text += self.full_text[self.char_index]
            self.char_index += 1
        else:
            self.type_event.cancel()
            Clock.schedule_once(self.hide, 3)

    def hide(self, dt):
        """Hide the notification"""
        anim = Animation(pos_hint={"center_x": 0.5, "top": 1.2}, duration=0.4, t="in_quad")
        anim.start(self)

class UBubbleApp(MDApp):
    isSignedIn = "user"
    disconnect_mode = BooleanProperty(False)

    def show_notif(self, text, notif_type="process"):
        """Make notification"""
        self.root.ids.global_notif.show(text, notif_type)

    def on_start(self):
        """Starting welcome and instructions"""
        self.show_notif("Welcome to U-Bubble! Sign in to get started.","success")

    def build(self):
        """Set theme and colors"""
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.theme_style = "Dark"
        return

# Start
if __name__ == "__main__":
    UBubbleApp().run()