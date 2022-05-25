#!/usr/bin/env python3
"""
 * CLIENT_PY
 * This is a Command Line Interface (CLI) client program
 * to interact with TST in the remote host
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "July, 2019"
__modified__  = "2021-11-06"
__version__   = "0.9.3"
__copyright__ = "VDI Technologies, LLC"

import os
import stat        # stat mode flags: S_IRWXU, etc.
import sys
from sys import stdin, stdout, stderr, argv, exit
import subprocess
from time import sleep
import signal
import re         # regex
from helpers import is_win, is_posix
import helpers
import utilities

# session
from session import CLI_session

def login():
    """ Login authentications for future versions """
    return True

def header():
    print(
        "******************************************************\n" + \
        "**           WELCOME TO TST CLIENT APP              **\n" + \
        "**     (C) 2018-2021. VDI Technologies, LLC.        **\n" + \
        "******************************************************\n"
    )
    
def menu(MENU_OPTIONS = {}):
    
    if not MENU_OPTIONS: return
    
    valid_options = [o['option'] for o in MENU_OPTIONS]
    opt = 0
    while opt not in valid_options:
        if opt != 0: print("??? Wrong option")
        s  = "\nActions:\n"
        s += "==================================================\n"
        for o in MENU_OPTIONS:
            s += "  [{:2d}] {:s}\n".format(o['option'], o['caption'])
        print(s)
        
        opt = input(f"Select option [{valid_options[0]}-{valid_options[-1]}] ==> ")
        try:
            opt = int(opt)
        except:
            opt = 0
        
    return opt

class CLI():
    """
    This class describes the CLI (Commmand Line Interface) object.
    """
    def __init__(self):
        self.session = CLI_session()

        # underlying SSH process
        p = None             

        # SSH objects
        ssh  = None
        sftp = None

        self.local_path = ""
        self.remote_path = ""

    def log(self, msg=''):
        if self.session is not None:
            self.session.log(msg)

def get_menu_option(opt, MENU_OPTIONS):
    for o in MENU_OPTIONS:
        if o['option'] == opt:
            return o['code']
    return ''

def main():
    
    local_path  = ""

    header()
    if not login():
        exit(1)

    O_CLI = CLI()
    user = "?"
    host = ""
    O_CLI.session.user = user
    O_CLI.session.host = host

    # default path to CSV
    CSV_DIR = ''
    
    MENU_OPTIONS = [
        {'option': 1, 'code': 'CREATE_WORKING_DIR', 'caption': 'Create a new working folder'},
        {'option': 2, 'code': 'RENAME_FOLDER', 'caption': 'Rename a folder'},
        {'option': 3, 'code': 'REMOVE_FOLDER', 'caption': 'Remove a folder'},
        {'option': 4, 'code': 'RUN_TST', 'caption': 'Run the TST in a case-study individually'},
        {'option': 5, 'code': 'MASTER_REPORT', 'caption': 'Generate Master Report (upon a complete exercise)'},
        {'option': 6, 'code': 'CLEAN_CSV', 'caption': 'Clean the CSV files in the server'},
        {'option': 7, 'code': 'EXIT', 'caption': 'Exit'}
    ]
    
    while 1:
        opt = menu(MENU_OPTIONS)

        # Create a new working directory
        if get_menu_option(opt, MENU_OPTIONS) == 'CREATE_WORKING_DIR':
            new_path = input("Enter the path for your new working directory: ")
            create_structure = input("Create a structure into this directory? y/[n]: ")
            create_structure = (create_structure.lower() == 'y')
            try:
                p = utilities.create_directory(new_path, 0o750, create_structure)
                # log this event ...
                O_CLI.log(f"{user} has created directory {new_path}")
            except Exception as e:
                print(str(e))
            input("Press ENTER to continue ...")

        # Rename a folder
        elif get_menu_option(opt, MENU_OPTIONS) == 'RENAME_FOLDER':
            old_path = input("Enter the path of the folder to be renamed: ")
            new_path = input("Enter the new path/name to the folder: ")
            utilities.rename_folder(old_path, new_path)
            input("Press ENTER to continue ...")

        # Remove a folder
        elif get_menu_option(opt, MENU_OPTIONS) == 'REMOVE_FOLDER':
            path = input("Enter the path of the folder to be removed: ")
            utilities.remove_folder(path)
            input("Press ENTER to continue ...")

        # Run the TST
        elif get_menu_option(opt, MENU_OPTIONS) == 'RUN_TST':
            wd = input("Enter the name of the working folder: ")
            try:
                p = utilities.run_app(wd)

                # log this event ...
                O_CLI.log(f"{user} has run TST app")
            except Exception as e:
                print(str(e))
            input("Press ENTER to continue ...")

        # Generate Master Report
        if get_menu_option(opt, MENU_OPTIONS) == 'MASTER_REPORT':
            work_dir = input("Enter the path for the exercise: ")
            if not os.path.exists or not os.path.isdir(work_dir):
                print(f"Sorry, there is not a folder '{work_dir}'")
                continue
            utilities.build_master_report(work_dir, 'Master-Report.xlsx')
            utilities.build_judgement(work_dir, 'Judgement.xlsx')
            input("Press ENTER to continue ...")

        # Clean the CSV files in the remote host
        elif get_menu_option(opt, MENU_OPTIONS) == 'CLEAN_CSV':
            path = input("Enter the path of the folder/case-study whose CSV's you want to remove: ")
            utilities.clean_csv(path)
            input("Press ENTER to continue ...")

        # Exit
        elif get_menu_option(opt, MENU_OPTIONS) == 'EXIT':
            print("Thanks for using the TST app, by VDITech.- Bye!")
            exit(0)

        # Inspect the content of the working directory
        """elif get_menu_option(opt, MENU_OPTIONS) == 'INSPECT_WORKING_DIR':
            remote_wd = input("Enter the name of the remote working folder: ")
            show_files = input("Descend into files y/[n]? ")
            show_files = (show_files.lower() == 'y')
            try:
                p = inspect_wd(ssh, remote_wd, show_files)
                # log this event ...
                O_CLI.log(f"{user} has inspected {remote_wd}")
            except Exception as e:
                print(str(e))
        """
        
        
if __name__ == "__main__":
    main()
    
