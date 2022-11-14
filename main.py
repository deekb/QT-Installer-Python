#! /bin/python3
import getpass
import math
import os
import sys
import time
import datetime
import hashlib

try:
    import qdarkstyle
except ModuleNotFoundError as e:
    print("Recoverable exception: could not find module \"qdarkstyle\"")
    NOQDARKSTYLE = True
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QTextBrowser, QRadioButton

# Get some colored terminal output
from colors import Colors

fg, bg = Colors.Foreground, Colors.Background


def log_out(string, end="\n"):
    print(string, end=end)
    LOG_FILE_OBJECT.write(string + end)


# Function for retrieving the relative path for resource files
def get_path(relative_path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)


# Set text substitutions here, to use them place the key of a dictionary itme in curly brackets: {}
# For example, in the ui file created in QtDesigner you can place {home} and make an entry below to 
# replace it with the users home path at runtime, the mentioned code would look like this
"""
substitutions = {"home": os.path.expanduser("~")}

"""
# Make sure to call parsePlaceholder() on the object before running the app!

# <CONSTANTS>

PROGRAM_NAME = "IP-Geo"
BINARY_NAME = "ip-geo"
VERSION = "1.42"
LOG_FILENAME = f"{PROGRAM_NAME}_{datetime.datetime.now()}.log"
LOG_PATH = f"/tmp/{LOG_FILENAME}"
INSTALLED = False
DESKTOP_SHORTCUT_PATH = os.path.expanduser(f"~/Desktop/{PROGRAM_NAME}.desktop")
MENU_SHORTCUT_PATH = os.path.expanduser(f"~/.local/share/applications/{PROGRAM_NAME}.desktop")
DESKTOP_SHORTCUT_CONTENTS = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Name={PROGRAM_NAME} {VERSION}
Comment=Locate IP addresses and find information about them
Exec=bash -c "ip-geo; sleep 10"
Type=Application
Categories=Utility;
Icon=gnome-globe
Terminal=true\
"""

LOG_FILE_OBJECT = open(LOG_PATH, "a")

SUBSTITUTIONS = {"name": PROGRAM_NAME,
                 "user": getpass.getuser().title(),
                 "version": VERSION,
                 "developer": "Derek Michael Baier",
                 "maintainer": "Derek Michael Baier",
                 "email": "Derek.m.baier@gmail.com"}

PAGES = {0: "welcome",
         1: "license",
         2: "install",
         3: "done"}


def parse_placeholders(*text_objects) -> None:
    for textObject in list(*text_objects):
        if isinstance(textObject, QTextBrowser):
            text = textObject.toPlainText()
        elif isinstance(textObject, (QLabel, QRadioButton)):
            text = textObject.text()
        else:
            log_out(f"[parse_placeholders]: \"{textobject}\" is not a valid text object or is not yet supported")
            text = ""

        for substitution in SUBSTITUTIONS:  # Iterate through the substitutions and apply them
            text = text.replace("{" + substitution + "}", SUBSTITUTIONS[substitution])

        if isinstance(textObject, QTextBrowser):
            textObject.setPlainText(text)
        elif isinstance(textObject, (QLabel, QRadioButton)):
            textObject.setText(text)


def copy_file(src, dst, chunks=100):
    log_out(f"[copy_file]: copying \"{src}\" to \"{dst}\"")

    size = os.stat(src).st_size
    log_out(f"[copy_file]: file is {size} bytes")

    chunk_size = math.ceil(size / chunks)
    while chunk_size == 0 and chunks > 0:
        chunks /= 10
        chunk_size = size / chunks
    log_out(f"[copy_file]: Moving in {chunks} chunks, each chunk is {chunk_size} bytes")

    # Copy.
    try:
        with open(src, 'rb') as input_file:
            with open(dst, 'wb') as output_file:
                copied_bytes = 0  # bytes
                chunk = input_file.read(chunk_size)
                while chunk and window.isVisible():
                    # Write and calculate how much has been written so far.
                    output_file.write(chunk)
                    copied_bytes += len(chunk)
                    percent_complete = 100 * float(copied_bytes) / float(size)
                    log_out(f"[copy_file]: INFO: {round(percent_complete)}% Complete ")
                    # Read in the next chunk.
                    chunk = input_file.read(chunk_size)
                    form.installProgress.setValue(round(percent_complete))
                    form.installProgress.update()
                    QtCore.QCoreApplication.processEvents()
        if not window.isVisible():
            os.remove(dst)
            return False
        else:
            return True

    except IOError as e:
        QMessageBox.critical(window, "Failed",
                             "The installer failed to copy the required files!\n Please retry as root")
        log_out(fg.red + f"\n[copy_file]: {e}" + Colors.reset)
        raise Exception


def next_tab() -> None:  # Manage tab changes using the next button
    global tabChangeAllowed, currentPage, window
    if PAGES[currentPage] == "license":
        if not form.accepted.isChecked():
            log_out(
                fg.yellow + "[next_tab]: Please accept the terms and conditions in order to proceed!" + Colors.reset)
            QMessageBox.information(window, "License", "Please accept the terms and conditions in order to proceed!"),
            return
        print("[next_tab]: Terms and con")
    if PAGES[currentPage] == "install":
        log_out("[next_tab]: Install button pressed, installing and disabling next button")
        form.next_button.setEnabled(False)
        install()
        form.next_button.hide()
        log_out("[next_tab]: Installed, changing next button text to \"Exit\"")
        form.cancel.setText("Exit")
    if currentPage < form.tabs.count() - 1:
        currentPage += 1
        tabChangeAllowed = True
        form.tabs.setCurrentIndex(currentPage)
        tabChangeAllowed = False
    if PAGES[currentPage] == "install":
        log_out("[next_tab]: Changing next button text to \"Install\"")
        form.next_button.setText("Install")


def install() -> None:  # Copy the binary to the bin folder
    if form.installForEveryone.isChecked():
        install_path = f"/usr/bin/{BINARY_NAME}"
    else:
        install_path = os.path.expanduser(f"~/.local/bin/{BINARY_NAME}")

    completed = copy_file(get_path("binary"), install_path)
    if completed:
        log_out("[install]: Setting permissions")
        os.chmod(install_path, 0o744)
    else:
        print("[install]: Installation canceled")
        QMessageBox.warning(window, "Installation Canceled", "Installation was canceled by the user!")
        log_out("Installation canceled: exiting")
        close_window()


def tab_change() -> None:  # Block manual tab changes
    global tabChangeAllowed, currentPage
    if not tabChangeAllowed:
        log_out("[tab_change]: Blocked manual tab change")
        tabChangeAllowed = True
        form.tabs.setCurrentIndex(currentPage)
        tabChangeAllowed = False


def close_window():
    log_out("[close_window]: Closing")
    print(window.isVisible())
    window.close()
    print(window.isVisible())


def create_desktop_shortcut():
    global DESKTOP_SHORTCUT_PATH, DESKTOP_SHORTCUT_CONTENTS
    with open(DESKTOP_SHORTCUT_PATH, "w") as f:
        f.write(DESKTOP_SHORTCUT_CONTENTS)
    os.chmod(DESKTOP_SHORTCUT_PATH, 0o744)


def create_menu_shortcut():
    global MENU_SHORTCUT_PATH, DESKTOP_SHORTCUT_CONTENTS
    with open(MENU_SHORTCUT_PATH, "w") as f:
        f.write(DESKTOP_SHORTCUT_CONTENTS)
    os.chmod(MENU_SHORTCUT_PATH, 0o744)


def run_program():
    os.system(f"x-terminal-emulator -e \"{BINARY_NAME}; sleep 10\"")


def initialize_user_interface():
    global form, window, app, currentPage, tabChangeAllowed

    form = Form()  # Set the window contents
    window.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())  # Set the style sheet of the window (using QDarkStyle)
    form.setupUi(window)  # Set up the UI

    currentPage = 0  # Set the starting page
    tabChangeAllowed = False

    if os.geteuid() == 0:  # User has root access so allow installing for everyone
        form.installForEveryone.setEnabled(True)
        form.installForEveryone.setChecked(True)
    else:  # User lacks root access, disable "install for everyone"
        form.installForEveryone.setEnabled(False)
        form.installForMeOnly.setChecked(True)

    parse_placeholders([form.welcomeLabel, form.programDescription, form.installForMeOnly, form.thankYouForInstalling])

    # Connect UI form signals
    form.tabs.setCurrentIndex(currentPage)
    form.cancel.clicked.connect(close_window)
    form.next_button.clicked.connect(next_tab)
    form.launchNow.clicked.connect(run_program)
    form.tabs.currentChanged.connect(tab_change)
    form.addDesktopEntry.clicked.connect(create_desktop_shortcut)
    form.addMenuEntry.clicked.connect(create_menu_shortcut)


def main():
    global app, Form, form, Window, window, currentPage, tabChangeAllowed
    app = QApplication([])
    Form, Window = uic.loadUiType(get_path("main.ui"))  # Load the UI file
    window = Window()
    form = Form()
    if not ("NOQDARKSTYLE" in locals()) and not NOQDARKSTYLE:
        window.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    currentPage = 0
    tabChangeAllowed = False
    log_out("Initializing user interface... ", end="")
    initialize_user_interface()  # Create the UI
    log_out("Done")
    window.show()  # Show the UI
    app.exec()  # Run the app
    LOG_FILE_OBJECT.close()
    return 0


if __name__ == "__main__":
    if os.path.exists("/home/derek/.local/bin/ip-geo"):
        byte_string = open("/home/derek/.local/bin/ip-geo", "rb").read()

        m = hashlib.md5()
        m.update(byte_string)
        if m.hexdigest() == "b552797d9413b3b0a33072c804c829b7":
            if QMessageBox.warning(window, "Warning", "Warning, the installer found an an existing version of this "
                                                      "program, would you like to continue?",
                                   QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
                exit(main())
        else:
            exit(main())
    else:
        exit(main())
