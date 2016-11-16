import ctypes, os, sys
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

def is_admin():
    try:
     is_admin = os.getuid() == 0
    except AttributeError:
     is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

def login_clicked(button):
    if is_admin():
        print "Attempting to log in..."
    else:
        dialog = Gtk.MessageDialog(button.get_toplevel(), 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Insufficient Permissions")
        dialog.format_secondary_text("User must have administrator privileges to log in.")
        dialog.run()
        print("ERROR dialog closed")

        dialog.destroy()

builder = Gtk.Builder()

if is_admin():
    builder.add_from_file("admin_login.glade")
    login = builder.get_object("button_login")
    login.connect("clicked", login_clicked)
else:
    def apply_button_clicked(assistant):
        print("The 'Apply' button has been clicked")

    def close_button_clicked(assistant):
        print("The 'Close' button has been clicked")
        Gtk.main_quit()

    def cancel_button_clicked(assistant):
        print("The 'Cancel' button has been clicked")
        Gtk.main_quit()

    def checkbutton_toggled(checkbutton):
        assistant.set_page_complete(box1, checkbutton.get_active())

    builder.add_from_file("voter_interface.glade")

    assistant = builder.get_object("main_window")
    print assistant
    assistant.connect("cancel", cancel_button_clicked)
    assistant.connect("close", close_button_clicked)
    assistant.connect("apply", apply_button_clicked)

    page1 = builder.get_object("label1")
    assistant.set_page_complete(page1, True)

    page2 = builder.get_object("label2")
    assistant.set_page_complete(page2, True)

    page3 = builder.get_object("label3")
    assistant.set_page_complete(page3, True)

    page4 = builder.get_object("box4")
    assistant.set_page_complete(page4, True)

    page5 = builder.get_object("box5")
    assistant.set_page_complete(page5, True)

    page6 = builder.get_object("box6")
    assistant.set_page_complete(page6, True)

window = builder.get_object("main_window")
window.connect("delete-event", Gtk.main_quit)
window.show_all()

Gtk.main()
