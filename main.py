import ctypes, os, sys, threading, random
from datetime import date
from re import sub
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
previous_length = 0
suffixes = ["Jr.", "Sr.", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

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
                user=builder.get_object("login_entry_username").get_text(),
                password=builder.get_object("login_entry_password").get_text(),
                database='evoting',
                auth_plugin='sha256_password',
                ssl_ca='ca.pem',
                ssl_cert='client-cert.pem',
                ssl_key='client-key.pem',
                ssl_verify_cert=True
            )
            builder.get_object("voters_menuitem").set_sensitive(True)
            builder.get_object("results_menuitem").set_sensitive(True)
            builder.get_object("candidates_menuitem").set_sensitive(True)
            builder.get_object("finalize_menuitem").set_sensitive(True)
            delete_admin_main_window()
            builder.get_object("logged_in_as_label").set_text(
                "Logged in as: " + builder.get_object("login_entry_username").get_text()
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                builder.get_object("login_error_label").set_text("Something is wrong with your user name or password!")
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        builder.get_object("login_spinner").stop()
    else:
        builder.get_object("login_spinner").stop()
        dialog = Gtk.MessageDialog(button.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
        dialog.format_secondary_text("User must have administrator privileges to log in.")
        dialog.run()
        print("ERROR dialog closed")
        dialog.destroy()

def login_clicked(button):
    builder.get_object("login_error_label").set_text("Attempting to log in...")
    builder.get_object("login_spinner").start()
    thread = threading.Thread(target=login_thread)
    thread.daemon = True
    thread.start()

def show_candidate_list(widget):
    print("TODO, show candidate list")

def finalize_election(widget):
    print("TODO, don't allow further changes to voters or candidates tables.")

def calc_election_results(widget):
    print("TODO, add all the encrypted votes, display results.")
    #TODO calc encrypted sum
    #TODO display results
        #TODO display fake results, then plug in real values

def delete_admin_main_window():
    for child in builder.get_object("box1").get_children():
        if type(child) is gi.repository.Gtk.Grid:
            builder.get_object("box1").remove(child)

def show_add_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("add_voter_grid"), False, False, 0
    )
    builder.get_object("button_add_voter").connect("clicked", req_add_voter)
    builder.get_object("entry_first_name").set_text("")
    builder.get_object("entry_middle_name").set_text("")
    builder.get_object("entry_last_name").set_text("")
    builder.get_object("combobox_suffix").set_active(0)
    #reset calendar
    today = date.today()
    builder.get_object("calendar_add").select_day(today.day)
    builder.get_object("calendar_add").select_month(today.month-1, today.year)
    builder.get_object("calendar_add").clear_marks()
    builder.get_object("entry_address").set_text("")
    builder.get_object("entry_ssn").set_text("")
    builder.get_object("entry_ssn").connect("changed", format_ssn)

def req_add_voter(widget):
    print("Checking voter information...")
    fname = builder.get_object("entry_first_name").get_text()
    mname = builder.get_object("entry_middle_name").get_text()
    if mname == "":
        mname = "NMN"
    lname = builder.get_object("entry_last_name").get_text()
    suffix = builder.get_object("combobox_suffix").get_active_text()
    dob = builder.get_object("calendar_add").get_date()
    address = builder.get_object("entry_address").get_text()
    ssn = builder.get_object("entry_ssn").get_text()
    print(fname, mname, lname, suffix, dob, address, ssn)
    if check_voter_info(widget, fname, lname, address, ssn):
        submit_voter_info(widget, fname, mname, lname, suffix, dob, address, ssn)

def check_voter_info(widget, fname, lname, address, ssn):
    error_message = ""
    if fname == "":
        error_message = error_message + "First Name cannot be empty.\n"
    if lname == "":
        error_message = error_message + "Last Name cannot be empty.\n"
    if address == "":
        error_message = error_message + "Mailing address cannot be empty.\n"
    if len(ssn) != 11:
        error_message = error_message + "Incorrect SSN length."
    if error_message == "":
        return True
    else:
        dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Problem with entry")
        dialog.format_secondary_text("Please correct the following errors and re-submit.\n\n" + error_message)
        dialog.run()
        dialog.destroy()
        return False

def submit_voter_info(widget, fname, mname, lname, suffix, dob, address, ssn):
    print("Everything looks good, submitting voter information...")
    dob_str = str(dob[0]) + "-" + str(dob[1]+1) + "-" + str(dob[2])
    #check that person doesn't already exist in DB
    new_user_resp = check_dup_voter(fname, mname, lname, suffix, dob_str, address, ssn)
    if new_user_resp == True:
        #generate random, unique voter id
        random.seed()
        voter_id = random.randint(0,9999999999)
        #check it doesn't already exist in system
        is_good_voter_id = check_voter_id(voter_id) == False
        while is_good_voter_id == False:
            voter_id = random.randint(0,9999999999)
            is_good_voter_id = check_voter_id(voter_id)
        print(voter_id)
        #send to MySQL database
        try:
            query = ("INSERT INTO registered_voters (voter_id, first_name, \
                middle_name, last_name, suffix, address, birth, ssn, has_voted) \
                VALUES (" + str(voter_id) + ", \"" + fname + "\", \"" + mname + "\", \"" + lname + \
                "\", \"" + suffix + "\", \"" + address + "\", \"" + dob_str + "\", \"" + ssn + "\", 0)")
            cursor = cnx.cursor()
            cursor.execute(query)
            cnx.commit()
            cursor.close()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Sucess: Registered Voter.")
            dialog.format_secondary_text("Voter information summary:\n\nVoter ID: "+str(voter_id)+\
                "\nFirst Name: "+fname+"\nMiddle Name: "+mname+"\nLast Name: "+lname+\
                "\nSuffix :" + suffix +"\nAddress: "+address+"\nDOB: "+dob_str+"\nSSN: "+ssn)
            dialog.run()
            dialog.destroy()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    else:
        #User already existed in DB, show error message
        dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Unable to register voter.")
        dialog.format_secondary_text(new_user_resp + " has already registered.")
        dialog.run()
        dialog.destroy()

def check_dup_voter(fname, mname, lname, suffix, dob_str, address, ssn):
    """Check if there is a user with the same PII or if SSN already exists in DB"""
    global cnx
    try:
        query = ("SELECT ssn FROM registered_voters")
        cursor = cnx.cursor()
        cursor.execute(query)
        for (ret_ssn) in list(cursor):
            if ret_ssn[0] == ssn:
                return "SSN"
        query = ("SELECT first_name, middle_name, last_name, suffix, birth, address, ssn \
            FROM registered_voters \
            WHERE first_name = \"" + fname + "\" AND middle_name = \"" + mname + "\" AND " \
            "last_name = \"" + lname + "\" AND suffix = \"" + suffix + "\" AND birth = \"" \
            + dob_str + "\" AND ssn = \"" + ssn + "\"")
        cursor.execute(query)
        print("Length of duplicate voter list: ", len(list(cursor)))
        if len(list(cursor)) > 0:
            return "Voter"
        else:
            return True
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

def check_voter_id(voter_id):
    global cnx
    try:
        query = ("SELECT voter_id FROM registered_voters")
        cursor = cnx.cursor()
        cursor.execute(query)
        for v_id in list(cursor):
            if voter_id == v_id:
                return False
        return True
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return False

def show_find_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("find_voter_grid"), False, False, 0
    )
    builder.get_object("entry_find_first_name").set_text("")
    builder.get_object("entry_find_middle_name").set_text("")
    builder.get_object("entry_find_last_name").set_text("")
    builder.get_object("combobox_find_suffix").set_active(0)
    #reset calendar
    today = date.today()
    builder.get_object("calendar_find").select_day(today.day)
    builder.get_object("calendar_find").select_month(today.month-1, today.year)
    builder.get_object("calendar_find").clear_marks()
    builder.get_object("entry_find_address").set_text("")
    builder.get_object("entry_find_ssn").set_text("")
    builder.get_object("entry_find_ssn").connect("changed", format_ssn)
    builder.get_object("button_find_voter").connect("clicked", find_voter)

def find_voter(widget):
    print("Looking for voter...")
    find_options = []
    if builder.get_object("entry_find_first_name").get_text() != "":
        find_options.append("first_name LIKE \"" + builder.get_object("entry_find_first_name").get_text() + "\"")
    if builder.get_object("entry_find_middle_name").get_text() != "":
        find_options.append("middle_name LIKE \"" + builder.get_object("entry_find_middle_name").get_text() + "\"")
    if builder.get_object("entry_find_last_name").get_text() != "":
        find_options.append("last_name LIKE \"" + builder.get_object("entry_find_last_name").get_text() + "\"")
    if builder.get_object("combobox_find_suffix").get_active_text() != " ":
        find_options.append("suffix = \"" + builder.get_object("combobox_find_suffix").get_active_text() + "\"")
    dob = builder.get_object("calendar_find").get_date()
    dob_str = str(dob[0]) + "-" + str(dob[1]+1) + "-" + str(dob[2])
    today_str = str(date.today().year) + "-" + str(date.today().month) + "-" + str(date.today().day)
    print(dob, dob_str, date.today(), dob_str == today_str)
    if dob_str != today_str:
        find_options.append("birth LIKE \"" + dob_str + "\"")
    if builder.get_object("entry_find_address").get_text() != "":
        find_options.append("address LIKE \"" + builder.get_object("entry_find_address").get_text() + "\"")
    if builder.get_object("entry_find_ssn").get_text() != "":
        find_options.append("ssn LIKE \"" + builder.get_object("entry_find_ssn").get_text() + "\"")

    if len(find_options) > 0:
        query_options = ""
        if len(find_options) > 1:
            for option in find_options[:-1]:
                query_options = query_options + option + " AND "
        query_options = query_options + find_options[-1]
        print(query_options)
        global cnx
        try:
            query = ("SELECT * FROM registered_voters WHERE " + query_options)
            cursor = cnx.cursor()
            cursor.execute(query)
            results = list(cursor)
            print(type(results))
            if len(results) > 0:
                delete_admin_main_window()
                builder.get_object("box1").pack_start(
                    builder.get_object("find_results_grid"), True, True, 0
                )
                builder.get_object("find_results_grid").grab_focus()
                thread = threading.Thread(target=add_results_to_treeview, args=[results])
                thread.daemon = True
                thread.start()
            else:
                print("No results found...")
                dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "No results found.")
                dialog.format_secondary_text("No results found with the given parameters: " + query_options)
                dialog.run()
                dialog.destroy()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    else:
        print("No search parameters entered...")
        dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, "WARNING: No search conducted.")
        dialog.format_secondary_text("No search parameters were given by user.")
        dialog.run()
        dialog.destroy()

def add_results_to_treeview(results):
    #builder.get_object("box1").show_all()
    result_store = builder.get_object("liststore_find_voter")
    #clear previous entries
    result_store.clear()
    #put results into liststore
    for (voter_id, first_name, middle_name, last_name, suffix, address, dob, ssn, has_voted) in results:
        dob_str = str(dob.month) + "/" + str(dob.day) + "/" + str(dob.year)
        result_store.append([int(voter_id), first_name, middle_name, last_name, suffix, address, dob_str, ssn])

def show_delete_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("delete_voter_grid"), True, True, 0
    )
    builder.get_object("entry_delete_voter_id").connect("changed", check_delete_id)
    builder.get_object("entry_delete_voter_id").connect("activate", check_delete_id)
    builder.get_object("button_delete_voter").connect("clicked", delete_voter)
    builder.get_object("entry_delete_voter_id").grab_focus()

def check_delete_id(widget):
    new_text = sanitize_id(widget)
    if len(new_text) == 10:
        builder.get_object("button_delete_voter").set_sensitive(True)
        builder.get_object("button_delete_voter").grab_focus()
    elif len(new_text) < 10:
        builder.get_object("button_delete_voter").set_sensitive(False)

def check_edit_id(widget):
    new_text = sanitize_id(widget)
    if len(new_text) == 10:
        builder.get_object("button_edit_voter").set_sensitive(True)
        builder.get_object("button_edit_voter").grab_focus()

def show_edit_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("edit_voter_grid"), True, True, 0
    )
    builder.get_object("entry_edit_voter_id").grab_focus()
    builder.get_object("entry_edit_voter_id").connect("changed", check_edit_id)
    builder.get_object("button_edit_voter").connect("clicked", edit_voter)

def edit_voter(widget):
    #query details and fill into widgets
    try:
        global cnx
        query = ("SELECT first_name, middle_name, last_name, suffix, birth, address, ssn \
            FROM registered_voters WHERE voter_id = " + \
            builder.get_object("entry_edit_voter_id").get_text())
        cursor = cnx.cursor()
        cursor.execute(query)
        list_cursor = list(cursor)
        if len(list_cursor) == 1:
            delete_admin_main_window()
            builder.get_object("box1").pack_start(
                builder.get_object("edit_voter_details_grid"), False, False, 0
            )
            for (first_name, middle_name, last_name, suffix, birth, address, ssn) in list_cursor:
                builder.get_object("entry_edit_first_name").set_text(first_name)
                if middle_name == "NMN":
                    builder.get_object("entry_edit_middle_name").set_text("")
                else:
                    builder.get_object("entry_edit_middle_name").set_text(middle_name)
                builder.get_object("entry_edit_last_name").set_text(last_name)
                builder.get_object("combobox_edit_suffix").set_active(get_suffix_index(suffix))
                #reset edit calendar
                builder.get_object("calendar_edit").select_day(birth.day)
                builder.get_object("calendar_edit").select_month(birth.month-1, birth.year)
                builder.get_object("entry_edit_address").set_text(address)
                builder.get_object("entry_edit_ssn").set_text(ssn)
                builder.get_object("entry_edit_ssn").connect("changed", format_ssn)
                builder.get_object("entry_edit_voter_id").connect("changed", check_edit_id)
                builder.get_object("button_save_edit_voter").connect("clicked", save_edit_voter)
        else:
            print("Voter ID not found...")
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Sucess: Voter removed.")
            dialog.format_secondary_text("Voter ID: " + builder.get_object("entry_edit_voter_id").get_text() + " not found!")
            dialog.run()
            dialog.destroy()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

def get_suffix_index(suffix):
    return {
        "": 0,
        "Jr.": 1,
        "Sr.": 2,
        "II": 3,
        "III": 4,
        "IV": 5,
        "V": 6,
        "VI": 7,
        "VII": 8,
        "VIII": 9,
        "IX": 10,
        "X": 11,
    }[suffix]

def format_ssn(widget):
    if ((len(widget.get_text()) == 3 and previous_length != 4) \
        or (len(widget.get_text()) == 6 and previous_length != 7)) \
        and previous_length != 8 and \
        not (previous_length == 5 and len(widget.get_text()) == 3):
        widget.stop_emission("insert_text")
        widget.insert_text("-", -1)
        GObject.idle_add(widget.set_position, -1)
    elif (previous_length == 5 and len(widget.get_text()) == 4) \
        or (previous_length == 8 and len(widget.get_text()) == 7):
        test = widget.get_text()
        widget.stop_emission("insert_text")
        widget.stop_emission("changed")
        widget.set_text(test[:-1])
        GObject.idle_add(widget.set_position, -1)
    global previous_length
    previous_length = len(widget.get_text())

def save_edit_voter(widget):
    print("Saving updated voter information...TODO.")
    global cnx
    voter_id = builder.get_object("entry_edit_voter_id").get_text()
    fname = builder.get_object("entry_edit_first_name").get_text()
    mname = builder.get_object("entry_edit_middle_name").get_text()
    lname = builder.get_object("entry_edit_last_name").get_text()
    suffix = builder.get_object("combobox_edit_suffix").get_active_text()
    dob = builder.get_object("calendar_edit").get_date()
    dob_str = str(dob[0]) + "-" + str(dob[1]+1) + "-" + str(dob[2])
    address = builder.get_object("entry_edit_address").get_text()
    ssn = builder.get_object("entry_edit_ssn").get_text()

    if check_voter_info(widget, fname, lname, address, ssn):
        #send to MySQL database
        try:
            query = ("UPDATE registered_voters SET first_name = \"" + fname + "\", \
                middle_name = \"" + mname + "\", last_name = \"" + lname + "\", \
                suffix = \"" + suffix + "\", address = \"" + address + "\", birth = \"" + dob_str +\
                "\", ssn = \"" + ssn + "\" WHERE voter_id = " + voter_id)
            print(query)
            cursor = cnx.cursor()
            cursor.execute(query)
            cnx.commit()
            cursor.close()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Sucess: Updated Voter Information.")
            dialog.format_secondary_text("Voter information summary:\n\nVoter ID: "+str(voter_id)+\
                "\nFirst Name: "+fname+"\nMiddle Name: "+mname+"\nLast Name: "+lname+\
                "\nSuffix :" + suffix +"\nAddress: "+address+"\nDOB: "+dob_str+"\nSSN: "+ssn)
            dialog.run()
            dialog.destroy()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)

def delete_voter(widget):
    print("Deleting voter number " + builder.get_object("entry_delete_voter_id").get_text())
    # check to see if the voter_id is NOT in the database (== False)
    if check_voter_id(builder.get_object("entry_delete_voter_id").get_text()) == False:
        try:
            query = ("DELETE FROM registered_voters WHERE voter_id = " + \
                builder.get_object("entry_delete_voter_id").get_text())
            cursor = cnx.cursor()
            cursor.execute(query)
            cnx.commit()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Sucess: Voter removed.")
            dialog.format_secondary_text("Voter ID: "+str(builder.get_object("entry_delete_voter_id").get_text()))
            dialog.run()
            dialog.destroy()
            cursor.close()
            builder.get_object("entry_delete_voter_id").grab_focus()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    else:
        dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "ERROR: Voter not removed.")
        dialog.format_secondary_text("Voter ID: "+str(builder.get_object("entry_delete_voter_id").get_text()) + \
            " does not exist in database.")
        dialog.run()
        dialog.destroy()
        builder.get_object("entry_delete_voter_id").grab_focus()

def apply_button_clicked(assistant):
    print("The 'Apply' button has been clicked")

def close_button_clicked(assistant):
    print("The 'Close' button has been clicked")
    program_quit()

def cancel_button_clicked(assistant):
    print("The 'Cancel' button has been clicked")
    program_quit()

def validate_voter_id(voter_id):
    int_id = int(voter_id)
    #query voter table and check if voter already voted
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
        query = ("SELECT voter_id, first_name, middle_name, last_name, suffix, has_voted from registered_voters")
        cursor = cnx.cursor()
        cursor.execute(query)
        for (v_id, first_name, middle_name, last_name, suffix, voted) in list(cursor):
            if (v_id == int_id
                and first_name == builder.get_object("entry_first_name").get_text()
                and middle_name == builder.get_object("entry_middle_name").get_text()
                and last_name == builder.get_object("entry_last_name").get_text()
                and suffix == builder.get_object("entry_suffix").get_text()
                ):
                if voted == 0:
                    return "valid_non_voted"
                return "valid_voted"
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    return "invalid"

def load_candidates():
    global candidate_list
    if (candidate_list == None):
        try:
            global cnx
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
        #delete spinner
        page5.remove(page5.get_children()[-1])
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
    assistant.set_page_complete(page5, True)

def prepare_handler(widget, data):
    if page4 == data:
        builder.get_object("entry_voter_id").connect("activate", lambda x: builder.get_object("assistant-action_area1").grab_focus())
    if page5 == data:
        print("Validate Unique User ID...")
        valid_id_response = validate_voter_id(builder.get_object("entry_voter_id").get_text())
        if valid_id_response == "valid_non_voted":
            builder.get_object("spinner1").start()
            print("Spinner started...")
            thread = threading.Thread(target=load_candidates)
            thread.daemon = True
            thread.start()
        elif valid_id_response == "valid_voted":
            dialog = Gtk.MessageDialog(data.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Possible Voter Fraud")
            dialog.format_secondary_text("Voter ID " + builder.get_object("entry_voter_id").get_text() + " has already voted.")
            dialog.run()
            print("ERROR dialog closed")
            dialog.destroy()
            assistant.previous_page()
        elif valid_id_response == "invalid":
            dialog = Gtk.MessageDialog(data.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Unable to validate")
            dialog.format_secondary_text("Unable to validate voter ID " + builder.get_object("entry_voter_id").get_text() + " with the information provided.  Please try again.")
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

def sanitize_id(widget):
    new_text = widget.get_text()
    i = 0;
    while i < len(new_text):
        if '0' <= new_text[i] <= '9':
            pass
        else:
            new_text = new_text[:i] + new_text[(i+1):]
        i = i + 1
    widget.set_text(new_text)
    return new_text

def check_id_input(widget):
    new_text = sanitize_id(widget)
    if len(new_text) == 10:
        assistant.set_page_complete(page4, True)
    else:
        assistant.set_page_complete(page4, False)

def show_login_window():
    builder.get_object("button_login").connect("clicked", login_clicked)
    builder.get_object("login_entry_username").connect("activate", login_clicked)
    builder.get_object("login_entry_password").connect("activate", login_clicked)
    builder.get_object("login_entry_username").set_text("")
    builder.get_object("login_entry_password").set_text("")
    builder.get_object("box1").pack_end(
        builder.get_object("login_grid"), False, False, 0
    )
    builder.get_object("login_error_label").set_text("")

def logout(self):
    #close MySQL connection
    try:
        global cnx
        cnx.close()
    except AttributeError:
        pass
    builder.get_object("voters_menuitem").set_sensitive(False)
    builder.get_object("results_menuitem").set_sensitive(False)
    builder.get_object("candidates_menuitem").set_sensitive(False)
    builder.get_object("finalize_menuitem").set_sensitive(False)
    #delete child
    delete_admin_main_window()
    builder.get_object("logged_in_as_label").set_text("")
    show_login_window()
    builder.get_object("login_entry_username").grab_focus()

def show_about(widget):
    aboutdialog = Gtk.AboutDialog()
    authors = ["Kyle Francis", "Damon Gass", "Ben Epsey"]
    documenters = ["Kyle Francis"]
    aboutdialog.set_program_name("E-Voting CSCI 6230")
    aboutdialog.set_copyright(
        "Copyright \xa9 2016 Rensselaer Polytechnic Institute")
    aboutdialog.set_authors(authors)
    aboutdialog.set_documenters(documenters)
    aboutdialog.set_website("https://github.com/guitarmanusa/crypto_evoting")
    aboutdialog.set_website_label("Github homepage")
    aboutdialog.set_version("0.1")
    license_file = open("GPL.txt", "r")
    aboutdialog.set_license(license_file.read())
    license_file.close()
    aboutdialog.set_wrap_license(True)
    # close the aboutdialog when "close" is clicked
    aboutdialog.connect("response", close_about)
    # show the aboutdialog
    aboutdialog.show()

def close_about(widget, action):
    widget.destroy()

builder = Gtk.Builder()

if is_admin():
    builder.add_from_file("admin.glade")
    quit_menu_option = builder.get_object("quit_menu")
    quit_menu_option.connect("activate", program_quit)
    builder.get_object("logout_menu").connect("activate", logout)
    builder.get_object("candidate_list_menu").connect("activate", show_candidate_list)
    builder.get_object("add_voter_menu").connect("activate", show_add_voter)
    builder.get_object("edit_voter_menu").connect("activate", show_edit_voter)
    builder.get_object("delete_voter_menu").connect("activate", show_delete_voter)
    builder.get_object("find_voter_menu").connect("activate", show_find_voter)
    builder.get_object("finalize_election_menu").connect("activate", finalize_election)
    builder.get_object("execute_results_menu").connect("activate", calc_election_results)
    builder.get_object("about_menuitem").connect("activate", show_about)
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
    builder.get_object("entry_voter_id").connect("changed", check_id_input)
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
