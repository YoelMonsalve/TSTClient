"""
 * CLIENT_PY
 * This is a Command Line Interface (CLI) client program
 * to interact with TST in the remote host
 *
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "July, 2019"
__modified__  = "July, 2021"
__version__   = "0.9.1"
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
    
    valid_options = [o for o in MENU_OPTIONS.keys()]
    opt = 0
    while opt not in valid_options:
        if opt != 0: print("??? Wrong option")
        s  = "\nActions:\n"
        s += "==================================================\n"
        for o in MENU_OPTIONS.keys():
            s += "  [{:2d}] {:s}\n".format(o, MENU_OPTIONS[o])
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

def main():
    
    host = "54.38.79.195"
    #host = "localhost"
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

    # default path to CSV
    CSV_DIR = ''
    
    MENU_OPTIONS = {
        1:  "Create a working folder",
        2:  "Inspect the content of the working folder",          
        3:  "Upload files",
        4:  "Run the TST",
        5:  "Download the analysis result files from the server",
        6:  "Clean the CSV files in the server (not implemented)",
        7:  "Reconnect with host (try this if the connection is interrupted)",
        8:  "Exit"
        # === disabled options ===
        #9:  "Compress files locally",                     # disabled
        #10:  "Transfer files to the remote host",          # disabled
        #11:  "Decompress files in the remote host",        # disabled
        #12: "Interact with the remote host via SSH (advanced)",
    }
    exit_option = -1
    for o in MENU_OPTIONS.keys():
        if MENU_OPTIONS[o].lower() == "exit":
            exit_option = o
    
    while 1:
        opt = menu(MENU_OPTIONS)

        # Create a new working directory
        if opt == 1:
            new_path = input("Enter the path for your new working directory: ")
            create_structure = input("Create a structure into this directory? y/[n]: ")
            create_structure = (create_structure.lower() == 'y')
            try:
                p = create_directory(ssh, 'work/' + new_path, 0o750, create_structure)
                # log this event ...
                O_CLI.log(f"{user} has created directory {new_path}")
            except Exception as e:
                print(str(e))

        # Inspect the content of the working directory
        elif opt == 2:
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
        elif opt == 3:
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
        elif opt == 4:
            remote_wd = input("Enter the name of the remote working folder: ")
            try:
                p = run_app(host, remote_wd)

                # log this event ...
                O_CLI.log(f"{user} has run TST app")   # === TODO === !!!!
            except Exception as e:
                print(str(e))

        # Download the files in the local host
        elif opt == 5:
            remote_wd = input("Enter the name of the remote working folder: ")
            remote_wd = "work/" + remote_wd
            local_wd  = input("Enter the name of your local working folder: ")
            try:
                #download_files(ssh, remote_wd, local_wd, O_CLI.session)
                download_files(ssh, remote_wd, local_wd)
            except Exception as e:
                print(str(e))

        # Clean the CSV files in the remote host
        elif opt == 6:
            print("Sorry, not implemented")

        # Connect/reconnect with host
        if opt == 7:
            print("Connecting with host")
            (ssh, sftp) = init_connection(host, user)
            if ssh:
                O_CLI.log(f"user {user}@{host} has logged in")

        # NOTE: disabled option.- Compress files
        elif opt == 9:
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
        
        elif opt == exit_option:
            print("Thanks for using the TST app, by VDITech.- Bye!")
            exit(0)

if __name__ == "__main__":
    main()
    
