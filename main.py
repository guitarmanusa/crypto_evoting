import ctypes, os, sys, threading
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
candidate_list = None
vote = None
candidates_populated = False
window_template = None

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

def login_thread():
    if is_admin():
        print("Attempting to log in...")
        #verify against mysql - login function
        try:
            global cnx
            cnx = mysql.connector.connect(
                host='159.203.140.245',
                user=window_template.get_object("entry_username").get_text(),
                password=window_template.get_object("entry_password").get_text(),
                database='evoting',
                auth_plugin='sha256_password',
                ssl_ca='ca.pem',
                ssl_cert='client-cert.pem',
                ssl_key='client-key.pem',
                ssl_verify_cert=True
            )
            login.set_label("Logged In!")
            builder.get_object("users_menuitem").set_sensitive(True)
            builder.get_object("results_menuitem").set_sensitive(True)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                window_template.get_object("login_error_label").set_text("Something is wrong with your user name or password!")
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        window_template.get_object("spinner1").stop()
    else:
        window_template.get_object("spinner1").stop()
        dialog = Gtk.MessageDialog(button.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
        dialog.format_secondary_text("User must have administrator privileges to log in.")
        dialog.run()
        print("ERROR dialog closed")
        dialog.destroy()

def login_clicked(button):
    window_template.get_object("login_error_label").set_text("Attempting to log in...")
    window_template.get_object("spinner1").start()
    thread = threading.Thread(target=login_thread)
    thread.daemon = True
    thread.start()

def apply_button_clicked(assistant):
    print("The 'Apply' button has been clicked")

def close_button_clicked(assistant):
    print("The 'Close' button has been clicked")
    program_quit()

def cancel_button_clicked(assistant):
    print("The 'Cancel' button has been clicked")
    program_quit()

def validate_user_id(id):
    #query voter table and check if voter already voted
    print(id)
    return True

def prepare_handler(widget, data):
    if page4 == data:
        builder.get_object("entry4").connect("activate", lambda x: builder.get_object("assistant-action_area1").grab_focus())
    if page5 == data:
        print("Validate Unique User ID...")
        if validate_user_id(builder.get_object("entry4").get_text()):
            global candidate_list
            if (candidate_list == None):
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
                    candidate_list = list(cursor)
                except mysql.connector.Error as err:
                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                        print("Something is wrong with your user name or password")
                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                        print("Database does not exist")
                    else:
                        print(err)
            global candidates_populated
            if len(candidate_list) >= 1 and candidates_populated == False:
                candidate_buttons = []
                candidate_buttons.append(Gtk.RadioButton.new_with_label(None, candidate_list[0][0] + " and " + candidate_list[0][1] + " (" + candidate_list[0][2] + " Party)"))
                candidate_buttons[-1].connect("toggled", on_button_toggled, candidate_list[0][3])
                page5.pack_start(candidate_buttons[-1], False, False, 0)
                for (pres_nom, vp_nom, party, c_id) in candidate_list[1:]:
                    # add radio buttons to the page
                    candidate_buttons.append(Gtk.RadioButton.new_with_label_from_widget(candidate_buttons[-1], pres_nom + " and " + vp_nom + " (" + party + ")"))
                    candidate_buttons[-1].connect("toggled", on_button_toggled, c_id)
                    page5.pack_start(candidate_buttons[-1], False, False, 0)
                candidate_buttons.append(Gtk.RadioButton.new_with_label_from_widget(candidate_buttons[-1], "None of the Above"))
                candidate_buttons[-1].connect("toggled", on_button_toggled, None)
                candidate_buttons[-1].set_active(True)
                page5.pack_start(candidate_buttons[-1], False, False, 0)
                page5.show_all()
                candidate_list.append(("None of the above", "None", "None", None))
                candidates_populated = True
            else:
                print("Error, Candidates list is empty.")
            assistant.set_page_complete(page5, True)
        else:
            dialog = Gtk.MessageDialog(data.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
            dialog.format_secondary_text("User ID " + builder.get_object("entry4").get_text() + " has already voted.")
            dialog.run()
            print("ERROR dialog closed")
            dialog.destroy()
            assistant.previous_page()
    if page6 == data:
        global vote
        #show confirmation page with selected candidate information
        for candidate in candidate_list:
            if candidate[3] == vote:
                builder.get_object("label6").set_text("You have selected:\n\n" + candidate[0])
    if page7 == data:
        #submit vote
            #actual work done here
            #zero knowledge proof
            #blind signature
            #encrypt
            #store in database
            #update voter id has voted
        if submit():
            builder.get_object("label8").set_markup("<big><b>Success!</b></big>\n\nYour vote has been successfully recorded.")
            builder.get_object("image1").set_from_file("green-checkmark.png")
        else:
            builder.get_object("label8").set_markup("<big><b>Error!</b></big>\n\nThere was an error recording your vote.  Please start over again.")
            builder.get_object("image1").set_from_file("red-x.png")

def submit():
    return True

def on_button_toggled(button, c_id):
    global vote
    if button.get_active():
        vote = c_id

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

def show_login_window():
    global window_template
    window_template = None
    window_template = Gtk.Builder()
    window_template.add_from_file("admin_objects.glade")
    login = window_template.get_object("button_login")
    login.connect("clicked", login_clicked)
    window_template.get_object("entry_username").connect("activate", login_clicked)
    window_template.get_object("entry_password").connect("activate", login_clicked)
    builder.get_object("box1").pack_end(window_template.get_object("admin_grid"), False, False, 0)

def logout(self):
    #close MySQL connection
    try:
        global cnx
        cnx.close()
    except AttributeError:
        pass
    builder.get_object("users_menuitem").set_sensitive(False)
    builder.get_object("results_menuitem").set_sensitive(False)
    #delete child
    builder.get_object("box1").remove(
        builder.get_object("box1").get_children()[-1]
    )
    show_login_window()
    window_template.get_object("entry_username").grab_focus()

builder = Gtk.Builder()

if is_admin():
    builder.add_from_file("admin_login.glade")
    quit_menu_option = builder.get_object("quit_menu")
    quit_menu_option.connect("activate", program_quit)
    builder.get_object("logout_menu").connect("activate", logout)

    show_login_window()

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

    page4 = builder.get_object("grid1")
    builder.get_object("entry5").connect("changed", check_id_input)
    assistant.set_page_complete(page4, False)

    page5 = builder.get_object("box5")
    assistant.set_page_complete(page5, False)

    page6 = builder.get_object("box6")
    assistant.set_page_complete(page6, True)

    page7 = builder.get_object("box7")
    assistant.set_page_complete(page7, True)

window = builder.get_object("main_window")
window.connect("delete-event", program_quit)
window.show_all()

Gtk.main()
