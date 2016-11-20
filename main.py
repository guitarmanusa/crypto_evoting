import ctypes, os, sys, time #time is for sleep(), remove in production
try:
    import gi
except ImportError:
    print (False, "Requires pygobject to be installed.")
try:
    gi.require_version("Gtk", "3.0")
except ValueError:
    print (False, "Requires gtk3 development files to be installed.")
except AttributeError:
    print (False, "pygobject version too old.")

try:
    from gi.repository import Gtk, Gdk, GObject
except (ImportError, RuntimeError):
    print (False, "Requires pygobject to be installed.")

try:
    import mysql.connector
    from mysql.connector import errorcode
except (ImportError, RuntimeError):
    print (False, "Requires MySQL DB connector to be installed.")

cnx = None

def program_quit(self=None, widget=None):
    try:
        global cnx
        cnx.close()
    except AttributeError:
        pass
    Gtk.main_quit()

def is_admin():
    try:
     is_admin = os.getuid() == 0
    except AttributeError:
     is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

def login_clicked(button):
    spinner = builder.get_object("spinner1")
    spinner.start()
    if is_admin():
        print("Attempting to log in...")
        #TODO implement login function
        try:
            global cnx
            cnx = mysql.connector.connect(
                host='159.203.140.245',
                user=builder.get_object("entry_username").get_text(),
                password=builder.get_object("entry_password").get_text(),
                database='evoting',
                auth_plugin='sha256_password',
                ssl_ca='ca.pem',
                ssl_cert='client-cert.pem',
                ssl_key='client-key.pem',
                ssl_verify_cert=True
            )
            login.set_label("Logged In!")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        spinner.stop()
    else:
        spinner.stop()
        dialog = Gtk.MessageDialog(button.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
        dialog.format_secondary_text("User must have administrator privileges to log in.")
        dialog.run()
        print("ERROR dialog closed")
        dialog.destroy()

def apply_button_clicked(assistant):
    print("The 'Apply' button has been clicked")

def close_button_clicked(assistant):
    print("The 'Close' button has been clicked")
    program_quit()

def cancel_button_clicked(assistant):
    print("The 'Cancel' button has been clicked")
    program_quit()

def prepare_handler(widget, data):
    if page1 == data:
        print("Page 1")
    if page2 == data:
        print("Page 2")
    if page3 == data:
        print("Page 3")
    if page4 == data:
        print("Page 4")
    if page5 == data:
        print("Page 5")
        print("Validate Unique User ID...")
        '''dialog = Gtk.MessageDialog(data.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
        dialog.format_secondary_text("User ID " + builder.get_object("entry4").get_text() + " has already voted.")
        dialog.run()
        print("ERROR dialog closed")
        dialog.destroy()
        assistant.previous_page()'''
        try:
            global cnx
            cnx = mysql.connector.connect(
                host='159.203.140.245',
                port='3306',
                user='read_candidates',
                password='GiantMeteor2016!@',
                database='evoting',
                auth_plugin='sha256_password',
                ssl_ca='ca.pem',
                ssl_cert='client-cert.pem',
                ssl_key='client-key.pem',
                ssl_verify_cert=True
            )
            cursor = cnx.cursor()
            query = ("SELECT pres_nom, vp_nom, party, c_id FROM candidates")
            cursor.execute(query)
            candidates = list(cursor)
            if len(candidates) >= 1:
                candidate1 = Gtk.RadioButton.new_with_label(None, candidates[0][0] + " and " + candidates[0][1] + " (" + candidates[0][2] + " Party)")
                page5.pack_start(candidate1, False, False, 0)
                current_button = candidate1
                for (pres_nom, vp_nom, party) in candidates[1:]:
                    # add radio buttons to the page
                    #page5
                    current_button = Gtk.RadioButton.new_with_label_from_widget(current_button, pres_nom + " and " + vp_nom + " (" + party + ")")
                    page5.pack_start(current_button, False, False, 0)
                current_button = Gtk.RadioButton.new_with_label_from_widget(current_button, "None of the Above")
                page5.pack_start(current_button, False, False, 0)
                page5.show_all()
            else:
                print("Error, Candidates list is empty.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    if page6 == data:
        print("Page 6")
    if page7 == data:
        print("Page 7")

def check_id_input(widget):
    new_text = widget.get_text()
    i = 0;
    while i < len(new_text):
        if '0' <= new_text[i] <= '9':
            pass
        else:
            new_text = new_text[:i] + new_text[(i+1):]
        i = i + 1
    widget.set_text(new_text)
    if len(new_text) == 10:
        assistant.set_page_complete(page4, True)
    else:
        assistant.set_page_complete(page4, False)

builder = Gtk.Builder()

if is_admin():
    builder.add_from_file("admin_login.glade")
    login = builder.get_object("button_login")
    login.connect("clicked", login_clicked)
    builder.get_object("entry_username").connect("activate", login_clicked)
    builder.get_object("entry_password").connect("activate", login_clicked)
    quit_menu_option = builder.get_object("imagemenuitem3")
    quit_menu_option.connect("activate", program_quit)
else:
    builder.add_from_file("voter_interface.glade")

    assistant = builder.get_object("main_window")
    assistant.connect("cancel", cancel_button_clicked)
    assistant.connect("close", close_button_clicked)
    assistant.connect("apply", apply_button_clicked)
    assistant.connect("prepare", prepare_handler)

    page1 = builder.get_object("label1")
    assistant.set_page_complete(page1, True)

    page2 = builder.get_object("label2")
    assistant.set_page_complete(page2, True)

    page3 = builder.get_object("label3")
    assistant.set_page_complete(page3, True)

    page4 = builder.get_object("box4")
    builder.get_object("entry4").connect("changed", check_id_input)
    assistant.set_page_complete(page4, False)

    page5 = builder.get_object("box5")
    assistant.set_page_complete(page5, True)

    page6 = builder.get_object("box6")
    assistant.set_page_complete(page6, True)

    page7 = builder.get_object("box7")
    assistant.set_page_complete(page7, True)

window = builder.get_object("main_window")
window.connect("delete-event", program_quit)
window.show_all()

Gtk.main()
