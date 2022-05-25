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
__version__   = "0.9.2"
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
from compress import compress_files
from transfer import upload_files, download_files
import ssh_methods
from ssh_methods import *

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
    
    host = "54.38.79.195"
    #host = "localhost"
    
    # .............................. quit this later!
    user   = "tst"
    
    passwd = ""          # to be given interactively
    local_path  = ""
    remote_path = ""
    p = None             # underlying SSH process

    # SSH objects
    ssh  = None
    sftp = None

    header()
    if not login():
        exit(1)

    O_CLI = CLI()
    O_CLI.session.user = user
    O_CLI.session.host = host

    # init a connection
    print("Connecting with host")
    (ssh, sftp) = init_connection(host, user)
    if ssh:
        O_CLI.log(f"user {user}@{host} has logged in")
    else:
        return

    # default path to CSV
    CSV_DIR = ''
    
    MENU_OPTIONS = [
        {'option': 1, 'code': 'CREATE_WORKING_DIR', 'caption': 'Create a new working folder'},
        {'option': 2, 'code': 'RENAME_FOLDER', 'caption': 'Rename a folder'},
        {'option': 3, 'code': 'REMOVE_FOLDER', 'caption': 'Remove a folder'},
        {'option': 4, 'code': 'INSPECT_WORKING_DIR', 'caption': 'Inspect the content of the working folder'},
        {'option': 5, 'code': 'UPLOAD_FILES', 'caption': 'Upload files'},
        {'option': 6, 'code': 'RUN_TST', 'caption': 'Run the TST'},
        {'option': 7, 'code': 'DOWNLOAD_FILES', 'caption': 'Download the analysis result from the server'},
        {'option': 8, 'code': 'CLEAN_CSV', 'caption': 'Clean the CSV files in the server'},
        {'option': 9, 'code': 'RECONNECT', 'caption': 'Reconnect with host (try this if the connection is interrupted)'},
        {'option': 10, 'code': 'EXIT', 'caption': 'Exit'}
    ]
    
    while 1:
        opt = menu(MENU_OPTIONS)

        # Create a new working directory
        if get_menu_option(opt, MENU_OPTIONS) == 'CREATE_WORKING_DIR':
            new_path = input("Enter the path for your new working directory: ")
            create_structure = input("Create a structure into this directory? y/[n]: ")
            create_structure = (create_structure.lower() == 'y')
            try:
                p = create_directory(ssh, 'work/' + new_path, 0o750, create_structure)
                # log this event ...
                O_CLI.log(f"{user} has created directory {new_path}")
            except Exception as e:
                print(str(e))

        # Rename a folder
        elif get_menu_option(opt, MENU_OPTIONS) == 'RENAME_FOLDER':
            old_path = input("Enter the path of the folder to be renamed: ")
            new_path = input("Enter the new path/name to the folder: ")
            ssh_methods.rename_folder(ssh, old_path, new_path)

        # Remove a folder
        elif get_menu_option(opt, MENU_OPTIONS) == 'REMOVE_FOLDER':
            path = input("Enter the path of the folder to be removed: ")
            ssh_methods.remove_folder(ssh, path)

        # Inspect the content of the working directory
        elif get_menu_option(opt, MENU_OPTIONS) == 'INSPECT_WORKING_DIR':
            remote_wd = input("Enter the name of the remote working folder: ")
            show_files = input("Descend into files y/[n]? ")
            show_files = (show_files.lower() == 'y')
            try:
                p = inspect_wd(ssh, remote_wd, show_files)
                # log this event ...
                O_CLI.log(f"{user} has inspected {remote_wd}")
            except Exception as e:
                print(str(e))
        
        # Upload files in one (compress + transfer + decompress)
        elif get_menu_option(opt, MENU_OPTIONS) == 'UPLOAD_FILES':
            CSV_DIR = ''
            print(f"Your current folder is: '{os.getcwd()}'")
            CSV_DIR = input("Enter the path where you have your CSV files: ")
            if not CSV_DIR[-1] == '/': CSV_DIR += '/'
            if not os.path.exists(CSV_DIR) or not os.path.isdir(CSV_DIR):
                # verifying the file exists and it is directory
                print("??? Does not exist, or it is not a directory")
                continue
            
            # changing the directory modes (user: read + write)
            O_CLI.log(f"changing the mode of `{CSV_DIR}` to u+rw")
            os.chmod(CSV_DIR, os.stat('.').st_mode | stat.S_IRUSR | stat.S_IXUSR)

            local_path = CSV_DIR + ".tmp/"
            print("=> local path to get the compressed files from:", local_path)
            
            remote_wd = input("Enter the name of the remote working folder [without the final /csv]: ")
            remote_path = remote_wd + "/csv"
            print("=> remote path to transfer the files to:", remote_path)

            ans = input("Confirm to continue [y]/n: ")
            if not ans or ans.lower() == 'y':
                try:
                    p = compress_files(CSV_DIR, O_CLI.session)
                    p = upload_files(ssh, local_path, remote_path, O_CLI.session)
                    p = decompress_files(ssh, remote_path, O_CLI.session)
                except Exception as e:
                    print(str(e))

        # Run the TST
        elif get_menu_option(opt, MENU_OPTIONS) == 'RUN_TST':
            remote_wd = input("Enter the name of the remote working folder: ")
            try:
                p = run_app(host, remote_wd)

                # log this event ...
                O_CLI.log(f"{user} has run TST app")   # === TODO === !!!!
            except Exception as e:
                print(str(e))

        # Download the files in the local host
        elif get_menu_option(opt, MENU_OPTIONS) == 'DOWNLOAD_FILES':
            remote_wd = input("Enter the name of the remote working folder: ")
            remote_wd = "work/" + remote_wd
            local_wd  = input("Enter the name of your local working folder: ")
            try:
                #download_files(ssh, remote_wd, local_wd, O_CLI.session)
                download_files(ssh, remote_wd, local_wd)
            except Exception as e:
                print(str(e))

        # Clean the CSV files in the remote host
        elif get_menu_option(opt, MENU_OPTIONS) == 'CLEAN_CSV':
            path = input("Enter the path of the folder/case-study whose CSV's you want to remove: ")
            ssh_methods.clean_csv(ssh, path)

        # Connect/reconnect with host
        elif get_menu_option(opt, MENU_OPTIONS) == 'RECONNECT':
            print("Connecting with host")
            (ssh, sftp) = init_connection(host, user)
            if ssh:
                O_CLI.log(f"user {user}@{host} has logged in")

        elif get_menu_option(opt, MENU_OPTIONS) == 'EXIT':
            print("Thanks for using the TST app, by VDITech.- Bye!")
            exit(0)


        # ===== DEPRECATED OPTIONS =====
        #
        # NOTE: disabled option.- Compress files
        """elif opt == 10:
            # compress files
            CSV_DIR = ''
            print(f"Your current folder is: '{os.getcwd()}'")
            CSV_DIR = input("Enter the path where you have your CSV files: ")
            if not CSV_DIR[-1] == '/': CSV_DIR += '/'
            if not os.path.exists(CSV_DIR) or not os.path.isdir(CSV_DIR):
                # verifying the file exists and it is directory
                print("??? Does not exist, or it is not a directory")
                continue
            # changing the directory modes (user: read + write)
            os.chmod(CSV_DIR, os.stat('.').st_mode | stat.S_IRUSR | stat.S_IXUSR)
            #os.chmod(DIR, 0o700)
            try:
                p = compress_files(CSV_DIR)
            except Exception as e:
                print(str(e))
        
        # NOTE: disabled option.- Transfer (compressed) files
        elif opt == 10:
            if not CSV_DIR:
                CSV_DIR = input("Enter the path where you have your CSV files: ")
            if not CSV_DIR[-1] == '/': CSV_DIR += '/'
            if not os.path.exists(CSV_DIR) or not os.path.isdir(CSV_DIR):
                # verifying the file exists and it is directory
                print("??? Does not exist, or it is not a directory")
                continue
            local_path = CSV_DIR + ".tmp/"
            print("=> local path to get the compressed files from:", local_path)
            
            remote_wd = input("Enter the name of the remote working folder [without the final /csv]: ")
            remote_path = remote_wd + "/csv"
            print("=> remote path to transfer the files to:", remote_path)
            try:
                p = transfer_files(ssh, local_path, remote_path)
            except Exception as e:
                print(str(e))

        # NOTE: disabled option.- Decompress files
        elif opt == 11:
            remote_wd = input("Enter the name of the remote working folder: ")
            remote_path = remote_wd + "/csv"
            try:
                p = decompress_files(ssh, remote_path)
            except Exception as e:
                print(str(e))
        """

if __name__ == "__main__":
    main()
    
