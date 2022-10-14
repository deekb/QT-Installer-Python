import getpass
import math
import os
import sys

import qdarkstyle
# noinspection PyUnresolvedReferences
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QTextBrowser, QRadioButton


# Function for retrieving the relative path for resources
def get_path(relative_path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)


# Set text substitutions here, to use them place the key of a dictionary itme in curly brackets: {}
# For example, in the ui file created in QtDesigner you can place {home} and make an entry below to 
# replace it with the users home path at runtime, the mentioned code would look like this
"""
substitutions = {"home": os.path.expanduser("~")}

"""
# Make sure to call parsePlaceholder() on the object before running the app!

# Global constants:
substitutions = {"name": "Main",
                 "user": getpass.getuser().title(),
                 "version": "1.0.0",
                 "developer": "Derek Michael Baier",
                 "maintainer": "Derek Michael Baier",
                 "email": "Derek.m.baier@gmail.com"}

pages = {0: "welcome",
         1: "license",
         2: "install",
         3: "done"}

# Global variables:
Form, Window = uic.loadUiType(get_path("main.ui"))  # Load the UI file
app = QApplication([])
window = Window()  # Initialize the window
form = Form()
currentPage = 0
tabChangeAllowed = False


def parse_placeholders(text_object_list: list) -> None:
    if isinstance(text_object_list, list):
        for textObject in text_object_list:
            if isinstance(textObject, QTextBrowser):
                text = textObject.toPlainText()
            elif isinstance(textObject, (QLabel, QRadioButton)):
                text = textObject.text()
            else:
                text = ""

            for substitution in substitutions:  # Iterate through the substitutions and apply them
                text = text.replace("{" + substitution + "}", substitutions[substitution])

            if isinstance(textObject, QTextBrowser):
                textObject.setPlainText(text)
            elif isinstance(textObject, (QLabel, QRadioButton)):
                textObject.setText(text)
    else:
        print("Argument must be a list!")
        return


def copy_file(src, dst):
    print('copying "{}" to "{}"'.format(src, dst))

    size = os.stat(src).st_size
    print('file is {} bytes'.format(size))

    # Adjust the chunk size to the input size.
    divisor = 100  # .1%
    # chunk_size = size / divisor
    chunk_size = math.ceil(size / divisor)
    while chunk_size == 0 and divisor > 0:
        divisor /= 10
        chunk_size = size / divisor
    print('chunk size is {}'.format(chunk_size))

    # Copy.
    try:
        with open(src, 'rb') as ifp:
            with open(dst, 'wb') as ofp:
                copied = 0  # bytes
                chunk = ifp.read(chunk_size)
                while chunk:
                    # Write and calculate how much has been written so far.
                    ofp.write(chunk)
                    copied += len(chunk)
                    per = 100 * float(copied) / float(size)
                    print("\r", end="")
                    print(round(per, 2), end="")

                    # Read in the next chunk.
                    chunk = ifp.read(chunk_size)
                    form.installProgress.setValue(round(per))
                    form.installProgress.update()
                    QtCore.QCoreApplication.processEvents()

    except IOError as obj:
        print('\nERROR: {}'.format(obj))
        sys.exit(1)


def next_tab() -> None:  # Tab change by clicking next
    global tabChangeAllowed, currentPage, window
    if pages[currentPage] == "license":
        if not form.accepted.isChecked():
            print("Please accept the terms and conditions in order to proceed!")
            QMessageBox.information(window, "License", "Please accept the terms and conditions in order to proceed!"),
            return
    if pages[currentPage] == "install":
        print("Install button pressed, installing and disabling next button")
        form.next_button.setEnabled(False)
        install()
        form.next_button.hide()
        print("installed, changing next button text to \"Exit\"")
        form.cancel.setText("Exit")
    if currentPage < form.tabs.count() - 1:
        currentPage += 1
        tabChangeAllowed = True
        form.tabs.setCurrentIndex(currentPage)
        tabChangeAllowed = False
    if pages[currentPage] == "install":
        print("1 Tab left, changing next button text to \"Install\"")
        form.next_button.setText("Install")


def install():
    print("Installing...")
    print("Copying files")
    copy_file(get_path("main.bin"), os.path.expanduser("~/.local/bin/main"))
    print("Setting permissions")
    os.chmod(os.path.expanduser("~/.local/bin/main"), 0o744)
    print("Done Installing")


def tab_change() -> None:  # Block manual tab changes
    global tabChangeAllowed, currentPage
    if not tabChangeAllowed:
        print("Blocked an attempt to change page manually")
        tabChangeAllowed = True
        form.tabs.setCurrentIndex(currentPage)
        tabChangeAllowed = False


def close_window():
    window.close()
    # noinspection PyProtectedMember,PyUnresolvedReferences
    os._exit(0)


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
    else:  # User lacks root access, disable install for everyone
        form.installForEveryone.setEnabled(False)
        form.installForMeOnly.setChecked(True)

    parse_placeholders([form.welcomeLabel, form.programDescription, form.installForMeOnly, form.thankYouForInstalling])

    form.tabs.setCurrentIndex(currentPage)
    form.cancel.clicked.connect(close_window)
    form.next_button.clicked.connect(next_tab)
    form.tabs.currentChanged.connect(tab_change)


initialize_user_interface()  # Create the UI
window.show()  # Show the UI
app.exec()  # Run the app
