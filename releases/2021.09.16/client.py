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
__version__   = ""
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
from compress import compress_files
from transfer import transfer_files, download_files
from ssh_methods import *

def login():
    return True

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

def main():
    
    host = "54.38.79.195"
    #host = "localhost"
    user = "tst"
    passwd = ""         # to be given interactively
    local_path  = ""
    remote_path = ""
    p = None             # underlying process

    # SSH objects
    ssh  = None
    sftp = None

    print(
        "******************************************************\n" + \
        "**           WELCOME TO TST CLIENT APP              **\n" + \
        "**     (C) 2018-2021. VDI Technologies, LLC.        **\n" + \
        "******************************************************\n"
    )
    
    if not login():
        exit(1)
    
    # init a connection
    print("Connecting with host")
    (ssh, sftp) = init_connection(host, user)

    # default path to CSV
    CSV_DIR = ''
    
    MENU_OPTIONS = {
        1:  "Create a working folder",
        2:  "Inspect the content of the working folder",          
        3:  "[*] Compress files locally",                            # Progress report
        4:  "[*] Transfer files to the remote host",                 # Progress report + timestamp
        5:  "[*] Decompress files in the remote host",               # Progress report
        6:  "Go all in one (compress + transfer + decompress)",
        7:  "Run the TST",
        8:  "Download the analysis result files from the server",
        9:  "Clean the CSV files in the server (not implemented)",
        #10: "Interact with the remote host via SSH (advanced)(not implemented)",
        10:  "Reconnect with host (try this if the connection is interrupted)",
        11: "Exit"
    }
    exit_option = -1
    for o in MENU_OPTIONS.keys():
        if MENU_OPTIONS[o].lower() == "exit":
            exit_option = o
    
    while 1:
        opt = menu(MENU_OPTIONS)

        if opt == 10:
            # start a SSH connection
            print("Connecting with host")
            (ssh, sftp) = init_connection(host, user)

        if opt == 1:
            # create a new working directory
            new_path = input("Enter the path for your new working directory: ")
            create_structure = input("Create a structure into this directory? y/[n]: ")
            create_structure = (create_structure.lower() == 'y')
            try:
                p = create_directory(ssh, 'work/' + new_path, 0o750, create_structure)
            except Exception as e:
                print(str(e))

        elif opt == 2:
            remote_wd = input("Enter the name of the remote working folder: ")
            show_files = input("Descend into files y/[n]? ")
            show_files = (show_files.lower() == 'y')
            try:
                p = inspect_wd(ssh, remote_wd, show_files)
            except Exception as e:
                print(str(e))
        
        if opt == 3:
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
        
        elif opt == 4:
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

        elif opt == 5:
            remote_wd = input("Enter the name of the remote working folder: ")
            remote_path = remote_wd + "/csv"
            try:
                p = decompress_files(ssh, remote_path)
            except Exception as e:
                print(str(e))
        
        elif opt == 6:
            # go in one (compress + transfer + decompress)
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

            local_path = CSV_DIR + ".tmp/"
            print("=> local path to get the compressed files from:", local_path)
            
            remote_wd = input("Enter the name of the remote working folder [without the final /csv]: ")
            remote_path = remote_wd + "/csv"
            print("=> remote path to transfer the files to:", remote_path)

            ans = input("Confirm to continue [y]/n: ")
            if not ans or ans.lower() == 'y':
                try:
                    p = compress_files(CSV_DIR)
                    p = transfer_files(ssh, local_path, remote_path)
                    p = decompress_files(ssh, remote_path)
                except Exception as e:
                    print(str(e))

        elif opt == 7:
            remote_wd = input("Enter the name of the remote working folder: ")
            try:
                p = run_app(host, remote_wd)
            except Exception as e:
                print(str(e))

        elif opt == 8:
            remote_wd = input("Enter the name of the remote working folder: ")
            remote_wd = "work/" + remote_wd
            local_wd  = input("Enter the name of your local working folder: ")
            print(remote_wd)
            print(local_wd)
            try:
                download_files(ssh, remote_wd, local_wd)
            except Exception as e:
                print(str(e))
            

        elif opt == exit_option:
            print("Thanks for using the TST app, by VDITech.- Bye!")
            exit(0)

if __name__ == "__main__":
    main()
    
