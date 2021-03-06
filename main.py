import ctypes, os, sys, threading, random, socket, ssl, gmpy2
from datetime import date
from re import sub
from phe import paillier
from phe.util import powmod
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import random

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
    from gi.repository import Gtk, Gdk, GObject, GLib
except (ImportError, RuntimeError):
    print (False, "Requires pygobject to be installed.")

try:
    import mysql.connector
    from mysql.connector import errorcode
except (ImportError, RuntimeError):
    print (False, "Requires MySQL DB connector to be installed.")

cnx = None
candidate_list = None
results_list = []
votes = []
candidates_populated = False
candidate_buttons = None
previous_length = 0
suffixes = ["Jr.", "Sr.", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
public_key = paillier.PaillierPublicKey(
    int('1484838658248464064259856757081154421171196989150622299748222043593445654503905553445414915359609687'
    '77035409413270882739651258158816563585214558468913443613231772079652558633998048113787675894701782805516'
    '041546348825706150790878817148626225214317380324006002845687798158170472767179664512573569011721121619210'),
    int('1484838658248464064259856757081154421171196989150622299748222043593445654503905553445414915359609687'
        '7703540941327088273965125815881656358521455846891344361323177207965255863399804811378767589470178280'
        '5516041546348825706150790878817148626225214317380324006002845687798158170472767179664512573569011721'
        '121619209')
)
private_key = paillier.PaillierPrivateKey(
    public_key,
    int('1484838658248464064259856757081154421171196989150622299748222043593445654503905553445414915359609687'
        '7703540941327088273965125815881656358521455846891344358880963170584176288941616997560216298988517672'
        '6588376014938598260107322562226654703806789497328701896179629787893923643909191408512732865362468774'
        '086425616'),
    int('1209818863361520907055266245043852094900453407335081622100520230243300448309204108498953798361998392'
        '1570412242276048398025358048658505315991931527094126348287807292980653840196979204526725748445692159'
        '3321437146917095663352914793202115969617820051688955720890628284454433067364261001918913237353254939'
        '782572370')
)
RSA_public_key = RSA.construct((
    int('3286263872074415988522731415732565023312391530808916640547945962451032839260032818752406195649382925'
        '5841707306963263944377173403241377917291058133635145296746759541988036065564512765895534762510687701'
        '3057443202332373543498990044331157492829860958738717106705881273923453962522669714506317007005895148'
        '0123315418638721207351019650573956003080466565080337749749013413154849856919689441467669745180356224'
        '3748850604232331340511453053595728950867177885893419756755583260713280775148288207232646190641638476'
        '2865026106742545012973705428444737625665832339539991816576370873289393586156110119028881256879626602'
        '4666454051777956259496486109413504774033505990964594784984752008703224978055936257808192299334692169'
        '6507236932427259974879490356859054497447834471273122930324737965380134373361037131766966503795655903'
        '5917025800410488630756760950980868540197155188855860610741030280367298069541002364433391490995746322'
        '7829692251765684847376359'), 65537))

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

def finalize_election(widget):
    print("TODO, don't allow further changes to voters or candidates tables.")

def calc_election_results(widget):
    global results_list
    print("Add all the encrypted votes, display results.")
    delete_admin_main_window()
    builder.get_object("box1").pack_start(builder.get_object("results_grid"), True, True, 0)
    #calc results in a thread
    thread = threading.Thread(target=calc_results_thread)
    thread.daemon = True
    thread.start()
    thread.join()
    #TODO display results
    for result in results_list:
        candidate_result = result[0] + " and " + result[1] + " received:\t<b><big>" + str(result[3]) + "</big></b>\n"
        builder.get_object("label_results").set_text(
            builder.get_object("label_results").get_text() + candidate_result
        )
    builder.get_object("label_results").set_use_markup(True)
    builder.get_object("spinner_results").stop()

def calc_results_thread():
    global candidate_list
    global results_list
    try:
        global cnx
        cursor = cnx.cursor()
        query = ("SELECT * FROM private_key")
        cursor.execute(query)
        for (Lambda, mu) in list(cursor):
            private_key = paillier.PaillierPrivateKey(public_key, int(Lambda), int(mu))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    try:
        cursor = cnx.cursor()
        query = ("SELECT pres_nom, vp_nom, party, c_id FROM candidates")
        cursor.execute(query)
        candidate_list = []
        for (pres_nom, vp_nom, party, c_id) in list(cursor):
            candidate_list.append([pres_nom, vp_nom, c_id])
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    #calc encrypted sum
    for i in range(0,len(candidate_list)):
        candidate_sum = public_key.encrypt(0)
        try:
            # (voter_id, encrypted_vote, signature, c_id)
            cursor = cnx.cursor(prepared=True)
            query = ("SELECT ctxt, c_id FROM votes WHERE c_id = %s")
            cursor.execute(query, (str(candidate_list[i][2]),))
            for (ctxt_vote, cv_id) in list(cursor):
                print("Ctxt vote: ", int(ctxt_vote.decode('ascii')))
                encrypted_vote = paillier.EncryptedNumber(public_key, int(ctxt_vote.decode('ascii')))
                candidate_sum = candidate_sum._add_encrypted(encrypted_vote)
            cursor.close()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        #decrypt sums
        candidate_list[i].append(private_key.decrypt(candidate_sum))
    #determin the winner
    def getkey(candidate):
        return candidate[3]
    results_list = sorted(candidate_list, key=getkey, reverse=True)
    print(results_list)
    candidate_list = None #reset because we needed it as a list vice a tuple to calc results

def delete_admin_main_window():
    for child in builder.get_object("box1").get_children():
        if type(child) is gi.repository.Gtk.Grid:
            builder.get_object("box1").remove(child)

def show_add_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("add_voter_grid"), False, False, 0
    )
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)")
            cursor = cnx.cursor(prepared=True)
            cursor.execute(query, (str(voter_id), fname, mname, lname, suffix, address, dob_str, ssn))
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
            WHERE first_name = %s AND middle_name = %s AND " \
            "last_name = %s AND suffix = %s AND birth = %s AND ssn = %s")
        cursor.execute(query, (fname, mname, lname, suffix, dob_str, ssn))
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
            cursor.close()
            if len(results) > 0:
                delete_admin_main_window()
                builder.get_object("box1").pack_start(
                    builder.get_object("find_results_grid"), True, True, 0
                )
                builder.get_object("find_results_grid").grab_focus()
                #builder.get_object("box1").show_all()
                result_store = builder.get_object("liststore_find_voter")
                #clear previous entries
                result_store.clear()
                #put results into liststore
                for result in results:
                    print(result)
                for (voter_id, first_name, middle_name, last_name, suffix, address, dob, ssn, has_voted) in results:
                    dob_str = str(dob.month) + "/" + str(dob.day) + "/" + str(dob.year)
                    new_iter = result_store.append([int(voter_id), first_name, middle_name, last_name, suffix, address, dob_str, ssn])
                    #result_store.row_inserted(result_store.get_path(new_iter), new_iter)
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
    return

def show_delete_voter(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("delete_voter_grid"), True, True, 0
    )
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

def edit_voter(widget):
    #query details and fill into widgets
    try:
        global cnx
        query = ("SELECT first_name, middle_name, last_name, suffix, birth, address, ssn \
            FROM registered_voters WHERE voter_id = %s")
        cursor = cnx.cursor(prepared=True)
        cursor.execute(query, (builder.get_object("entry_edit_voter_id").get_text(),))
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
    global previous_length
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
            query = ("UPDATE registered_voters SET first_name = %s, \
                middle_name = %s, last_name = %s, suffix = %s, address = %s, \
                birth = %s, ssn = %s WHERE voter_id = %s")
            print(query)
            cursor = cnx.cursor(prepared=True)
            cursor.execute(query (fname, mname, lname, suffix, address, dob_str, ssn, voter_id))
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
            query = ("DELETE FROM registered_voters WHERE voter_id = %s")
            cursor = cnx.cursor(prepared=True)
            cursor.execute(query, (builder.get_object("entry_delete_voter_id").get_text(),))
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

def close_button_clicked(data):
    print("The 'Close' button has been clicked")
    program_quit()

def cancel_button_clicked(data):
    print("The 'Cancel' button has been clicked")
    program_quit()

def validate_voter_id_thread(widget, voter_id):
    pass

def add_mainloop_task(callback, *args):
    """http://stackoverflow.com/questions/26362447/dialog-in-thread-freeze-whole-app-despite-gdk-threads-enter-leave"""
    def cb(args):
        try:
            args[0](*args[1:])
        except TypeError:
            pass
        return False
    args= [callback]+list(args)
    Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT, cb, args)

def show_dialog_in_thread(dialog):
    dialog.run()
    dialog.destroy()

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

def load_candidates(is_voting):
    global candidate_list
    global votes
    global candidates_populated
    global candidate_buttons
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
    if len(candidate_list) > 1 and candidates_populated == False:
        if is_voting == False:
            for candidate in candidate_list:
                if candidate[3] == 1:
                    candidate_list.remove(candidate)
        pres = candidate_list[0][0]
        vp = candidate_list[0][1]
        party = candidate_list[0][2]
        c_id = candidate_list[0][3]
        candidate_buttons = []
        if c_id == 1:
            candidate_buttons.append(Gtk.RadioButton.new_with_label(None, "None of the Above"))
        else:
            candidate_buttons.append(Gtk.RadioButton.new_with_label(None, pres + " and " + vp + " (" + party + " Party)"))
        candidate_buttons[-1].connect("toggled", on_button_toggled, c_id)
        votes.append([c_id,0])
        for (pres_nom, vp_nom, party, c_id) in candidate_list[1:]:
            # add radio buttons to the page
            if c_id != 1:  #make special name for "None of the above" candidate
                candidate_buttons.append(Gtk.RadioButton.new_with_label_from_widget(candidate_buttons[-1], pres_nom + " and " + vp_nom + " (" + party + " Party)"))
            else:
                candidate_buttons.append(Gtk.RadioButton.new_with_label_from_widget(candidate_buttons[-1], "None of the Above"))
                candidate_buttons[-1].set_active(True)
            candidate_buttons[-1].connect("toggled", on_button_toggled, c_id)
            votes.append([c_id,0])
        candidates_populated = True

def prepare_handler(widget, data):
    global votes
    if page5 == data:
        print("Validate Unique User ID...")
        builder.get_object("spinner1").start()
        print("Spinner started...")
        voter_id = builder.get_object("entry_voter_id").get_text()
        print("Voter ID: ", voter_id)
        valid_id_response = validate_voter_id(voter_id)
        print(valid_id_response)
        if valid_id_response == "valid_non_voted":
            thread = threading.Thread(target=load_candidates, args=(True,))
            thread.start()
            thread.join()
            global candidate_buttons
            #delete spinner
            builder.get_object("spinner1").stop()
            page5.remove(builder.get_object("spinner1"))
            print("Candidate buttons: ", candidate_buttons)
            for button in candidate_buttons:
                page5.pack_start(button, False, False, 0)
            page5.show_all()
            assistant.set_page_complete(page5, True)
        elif valid_id_response == "valid_voted":
            spinner = builder.get_object("spinner1")
            spinner.stop()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Possible Voter Fraud")
            dialog.format_secondary_text("Voter ID " + builder.get_object("entry_voter_id").get_text() + " has already voted.")
            add_mainloop_task(show_dialog_in_thread, dialog)
            print("ERROR dialog closed")
            add_mainloop_task(assistant.previous_page(), None)
        elif valid_id_response == "invalid":
            spinner = builder.get_object("spinner1")
            spinner.stop()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "ERROR: Unable to validate")
            dialog.format_secondary_text("Unable to validate voter ID " + builder.get_object("entry_voter_id").get_text() + " with the information provided.  Please try again.")
            add_mainloop_task(show_dialog_in_thread, dialog)
            print("ERROR dialog closed")
            add_mainloop_task(assistant.previous_page(), None)
    if page6 == data:
        print("Finding out vote...")
        print(len(votes), votes)
        #show confirmation page with selected candidate information
        for vote in votes:
            print(vote)
            if vote[1] == 1:
                candidate_selected = vote[0]
        for candidate in candidate_list:
            print(candidate)
            if candidate[3] == candidate_selected:
                builder.get_object("label6").set_text("You have selected:\n\n" + candidate[0])
    if page8 == data:
        if votes_proven == True:
            builder.get_object("label8").set_markup("<big><b>Success!</b></big>\n\nYour vote has been successfully recorded.")
            builder.get_object("image1").set_from_file("green-checkmark.png")
        else:
            builder.get_object("label8").set_markup("<big><b>Error!</b></big>\n\nThere was an error recording your vote.  Please start over again.")
            builder.get_object("image1").set_from_file("red-x.png")

def submit_zkp(widget):
    builder.get_object("spinner2").start()
    global votes_proven
    votes_proven = False
    print("Page 7 votes: ", votes)

    voter_id = builder.get_object("entry_voter_id").get_text()
    thread = threading.Thread(target=prove_votes, args=[(voter_id,)])
    thread.daemon = True
    thread.start()

def prove_votes(voter_id):
    global votes
    global votes_proven
    votes_proven = False
    ZKP_STATUS = True

    #make TLS connection to EM/BB
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    context.load_verify_locations("ca.pem")
    conn = context.wrap_socket(socket.socket(socket.AF_INET))
    conn.connect(('localhost', 8443))

    for i in range(0,len(votes)):
        def egcd(a, b):
            if a == 0:
                return (b, 0, 1)
            else:
                g, y, x = egcd(b % a, a)
                return (g, x - (b // a) * y, y)

        def modinv(a, m):
            g, x, y = egcd(a, m)
            if g != 1:
                raise Exception('modular inverse does not exist')
            else:
                return x % m

        if ZKP_STATUS == False:
            break
        else:
            #actual work done here
            #encrypt (need ciphertext for ZKP)
            m = votes[i][1]
            x = random.randint(1,10)
            enc_vote = public_key.encrypt(votes[i][1], r_value=x)
            votes[i][1] = enc_vote
            #start zero knowledge proof
            conn.send(bytes("ZKP START",'ascii'))

            for j in range(1,5):
                if ZKP_STATUS == True:
                    print("ZKP Started...round " + str(j))
                    successful = False

                    while not successful:
                        print("x: ", x)
                        c = (powmod(public_key.g,m,public_key.nsquare)*powmod(x,public_key.n,public_key.nsquare)) % public_key.nsquare
                        print("c: ", c)
                        r = random.randint(0,public_key.n)
                        print("r = ", r)
                        s = random.randint(3,public_key.n)
                        while s == r: # make s in the set Z*n (excluding r)
                            s = random.randint(3,public_key.n)
                        print("s = ", s)
                        u = (powmod(public_key.g,r,public_key.nsquare)*powmod(s,public_key.n, public_key.nsquare)) % public_key.nsquare
                        print("u = ", u)
                        #send c and u
                        conn.send(bytes(str(c),'ascii'))
                        conn.send(bytes(str(u),'ascii'))
                        #get e back
                        e = conn.recv(2048)
                        e = int(e.decode('ascii'))
                        print("e: ", e)
                        try:
                            #calculate v and w
                            ex_inv = modinv(powmod(x,e*public_key.n, public_key.nsquare), public_key.nsquare)
                            wn = (powmod(s, public_key.n, public_key.nsquare) * ex_inv)
                            print("wn: ", wn)
                            conn.send(bytes(str(wn),'ascii'))
                            v = r-(e*m)
                            print("v: ", v)
                            conn.send(bytes(str(v),'ascii'))
                            resp = conn.recv(2048)
                            resp = resp.decode('ascii')
                            print("U calculated by server: ", resp)
                            if resp == "PASS ROUND":
                                print("Passed round " + str(j) + " of 4 in ZKP.")
                                successful = True
                            else:
                                ZKP_STATUS = False
                                votes_proven = False
                                successful = True
                                print("Failed round " + str(j) + " of 4 in ZKP.")
                                break
                        except:
                            print("No inverse of s*x^-e, picking new e and s.")
                            conn.send(bytes("restart", 'ascii'))
            if ZKP_STATUS == True:
                #generate blind signature
                ## Protocol: Blind signature ##
                # must be guaranteed to be chosen uniformly at random
                r = random.randint(0, RSA_public_key.n)
                msg_plain_text = str(votes[i][1])
                c_id = str(votes[i][0])

                msg_for_signing = voter_id[0] + "-" + msg_plain_text + "-" + c_id

                # hash message so that messages of arbitrary length can be signed
                hash = SHA256.new()
                hash.update(msg_for_signing.encode('utf-8'))
                msgDigest = hash.digest()
                print("digest: ", msgDigest)
                print(sys.getsizeof(msgDigest))

                # user computes
                msg_blinded = RSA_public_key.blind(msgDigest, r)
                print("Blinded Message: ", msg_blinded)
                print(sys.getsizeof(msg_blinded))
                #send for signing
                conn.send(msg_blinded)
                #wait for signature
                data = conn.recv(1024)
                print(data)
                #match the beginning of the string to "SUCCESS"
                if data.decode('utf-8') == "FAILED":
                    blind_signature = None
                    do_continue = False
                else:
                    #save the rest of the response as the blind_signature
                    blind_signature = data
                    do_continue = True

                if blind_signature != None and do_continue == True:
                    #store (signature, encrypted vote, voter_id) in database
                    try:
                        c_id = votes[i][0]
                        if c_id == "None":
                            c_id = 0;
                        query = ("INSERT INTO votes (voter_id, ctxt, c_id)\
                            VALUES (%s, %s, %s)"
                        )
                        cursor = cnx.cursor(prepared=True)
                        cursor.execute(query, (builder.get_object("entry_voter_id").get_text(), str(votes[i][1].ciphertext()), str(c_id)
                        ))
                        cnx.commit()
                        cursor.close()
                        votes_proven = True
                    except mysql.connector.Error as err:
                        votes_proven = False
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                            print("Something is wrong with your user name or password")
                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                            print("Database does not exist")
                        else:
                            print(err)
                    #update voter id has voted
                    try:
                        query = ("UPDATE registered_voters SET has_voted = 1\
                            WHERE voter_id = %s"
                        )
                        cursor = cnx.cursor(prepared=True)
                        cursor.execute(query, (builder.get_object("entry_voter_id").get_text(),))
                        cnx.commit()
                        cursor.close()
                    except mysql.connector.Error as err:
                        votes_proven = False
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                            print("Something is wrong with your user name or password")
                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                            print("Database does not exist")
                        else:
                            print(err)
    conn.close()

    #vote was submitted successfully
    builder.get_object("spinner2").stop()
    assistant.next_page()

def submit():
    return True

def on_button_toggled(changed_button, c_id):
    global votes
    for vote in votes:
        if vote[0] == c_id:
            if changed_button.get_active():
                vote[1] = 1
            else:
                vote[1] = 0

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

def show_candidate_list(widget):
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("grid_candidates_list"), True, True, 0
    )
    for child in builder.get_object("box_candidates").get_children():
        builder.get_object("box_candidates").remove(child)
    global candidate_list
    candidate_list = None
    global candidates_populated
    candidates_populated = False
    thread = threading.Thread(target=load_candidates, args=(False,))
    thread.daemon = True
    thread.start()
    thread.join()
    global candidate_buttons
    #delete spinner
    builder.get_object("spinner_candidates").stop()
    builder.get_object("grid_add_candidate").remove(builder.get_object("spinner_candidates"))
    print("Candidate buttons: ", candidate_buttons)
    for button in candidate_buttons:
        builder.get_object("box_candidates").pack_start(button, False, False, 0)
    builder.get_object("box_candidates").show_all()

def add_candidate(widget):
    print("TODO...adding candidate")
    delete_admin_main_window()
    builder.get_object("box1").pack_start(
        builder.get_object("grid_add_candidate"), True, True, 0
    )

def submit_candidate(widget):
    print("Checking that candidate is not already in DB.")
    global candidate_list
    global cnx
    if (candidate_list == None):
        try:
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
    proceed = ""
    for (pres_nom, vp_nom, party, c_id) in candidate_list:
        if pres_nom == builder.get_object("entry_pres_nom").get_text():
            proceed = "Presidential"
        if vp_nom == builder.get_object("entry_vpres_nom").get_text():
            proceed = "Vice Presidential"
    if proceed == "":
        try:
            query = ("INSERT INTO candidates (pres_nom, vp_nom, party)\
                VALUES (%s, %s, %s)"
            )
            cursor = cnx.cursor(prepared=True)
            cursor.execute(query, (builder.get_object("entry_pres_nom").get_text(), builder.get_object("entry_vpres_nom").get_text(), builder.get_object("entry_party").get_text()))
            cnx.commit()
            cursor.close()
            dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Sucess: Added candidates to ballot.")
            dialog.format_secondary_text("Candidate information summary:\n\n\
                Presidential Nominee: "+builder.get_object("entry_pres_nom").get_text()+ "\n\
                Vice President Nominee: "+builder.get_object("entry_vpres_nom").get_text()+"\n\
                Party: " + builder.get_object("entry_party").get_text()
            )
            dialog.run()
            dialog.destroy()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    elif proceed == "Presidential" or proceed == "Vice Presidential":
        if proceed == "Presidential":
            entry = "entry_pres_nom"
        else:
            entry = "entry_vpres_nom"
        dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Failed: Unable to add to ballot.")
        dialog.format_secondary_text(
            proceed + " Nominee: "+builder.get_object(entry).get_text()+ \
            " already appears on the ballot."
        )
        dialog.run()
        dialog.destroy()

def delete_candidate(widget):
    print("TODO...delete candidate")
    global votes
    global cnx
    for vote in votes:
        if vote[1] == 1:
            candidate_selected = vote[0]
    try:
        query = ("DELETE FROM candidates WHERE c_id = %s")
        cursor = cnx.cursor(prepared=True)
        cursor.execute(query, (str(candidate_selected),))
        cnx.commit()
        for candidate in candidate_list:
            if candidate[3] == candidate_selected:
                dialog = Gtk.MessageDialog(widget.get_toplevel(), 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Sucess: Candidate removed.")
                dialog.format_secondary_text("Candidate ID: "+str(vote[0])+"\n\
                    Presidential Nominee: "+candidate[0]+"\n\
                    Vice Presidential Nominee: "+candidate[1]+"\n\
                    Party: "+candidate[2])
                dialog.run()
                dialog.destroy()
        cursor.close()
        show_candidate_list(widget)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

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
    #main menubar connections
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
    #login window connections
    builder.get_object("button_login").connect("clicked", login_clicked)
    builder.get_object("login_entry_username").connect("activate", login_clicked)
    builder.get_object("login_entry_password").connect("activate", login_clicked)
    #add voter connections
    builder.get_object("button_add_voter").connect("clicked", req_add_voter)
    builder.get_object("entry_ssn").connect("changed", format_ssn)
    #candidates buttons
    builder.get_object("button_add_candidate").connect("clicked", add_candidate)
    builder.get_object("button_delete_candidate").connect("clicked", delete_candidate)
    builder.get_object("button_submit_candidate").connect("clicked", submit_candidate)
    #delete voter connections
    builder.get_object("entry_delete_voter_id").connect("changed", check_delete_id)
    builder.get_object("entry_delete_voter_id").connect("activate", check_delete_id)
    builder.get_object("button_delete_voter").connect("clicked", delete_voter)
    #edit voter connections
    builder.get_object("entry_edit_voter_id").connect("changed", check_edit_id)
    builder.get_object("button_edit_voter").connect("clicked", edit_voter)
    builder.get_object("entry_edit_ssn").connect("changed", format_ssn)
    builder.get_object("entry_edit_voter_id").connect("changed", check_edit_id)
    builder.get_object("button_save_edit_voter").connect("clicked", save_edit_voter)
    #find voter connections
    builder.get_object("entry_find_ssn").connect("changed", format_ssn)
    builder.get_object("button_find_voter").connect("clicked", find_voter)

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
    builder.get_object("entry_voter_id").connect("activate", lambda x: builder.get_object("assistant-action_area1").grab_focus())
    assistant.set_page_complete(page4, False)

    page5 = builder.get_object("box5")
    assistant.set_page_complete(page5, False)

    page6 = builder.get_object("box6")
    assistant.set_page_complete(page6, True)

    page7 = builder.get_object("box7")
    assistant.set_page_complete(page7, False)
    builder.get_object("button_zkp").connect("clicked", submit_zkp)

    page8 = builder.get_object("box8")
    assistant.set_page_complete(page8, True)

window = builder.get_object("main_window")
window.connect("delete-event", program_quit)
window.show_all()

GObject.threads_init()
Gtk.main()
