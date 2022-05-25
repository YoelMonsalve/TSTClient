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
from transfer import transfer_files

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
			s += f"  [{o}] {MENU_OPTIONS[o]}\n"
		print(s)
		
		opt = input(f"Select option [{valid_options[0]}-{valid_options[-1]}] ==> ")
		try:
			opt = int(opt)
		except:
			opt = 0
		
	return opt

def main():
	
	#CSV_DIR = "../work/2021S_2/csv/"
	CSV_DIR = ""
	
	HOST = "54.38.79.195"
	local_path = "../work/2021S_2/csv/.tmp/"
	remote_path = "work/2021S_2/csv/"
	
	print(
	    "******************************************************\n" + \
	    "**           WELCOME TO TST CLIENT APP              **\n" + \
	    "**           (C) VDI Technologies, LLC              **\n" + \
	    "******************************************************\n"
	)
	
	if not login():
		exit(1)
	#transfer(HOST, local_path, remote_path)
	
	MENU_OPTIONS = {
		1: "Create a working folder (not implemented)",
		2: "Inspect the content of the working folder (not implemented)",
		3: "Compress files locally",
		4: "Transfer files to the remote host",
		5: "Compress and transfer (in one go) (not implemented)",
		6: "Run the TST (pending)",
		7: "Download the analysis result files from the server",
		8: "Interact with the remote host via SSH (advanced)(not implemented)",
		9: "Exit",
	}
	exit_option = -1
	for o in MENU_OPTIONS.keys():
		if MENU_OPTIONS[o].lower() == "exit":
			exit_option = o
	
	while 1:
		opt = menu(MENU_OPTIONS)
		
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
			compress_files(CSV_DIR)
		
		elif opt == 4:
			if not CSV_DIR:
				CSV_DIR = input("Enter the path where you have your CSV files: ")
			if not CSV_DIR[-1] == '/': CSV_DIR += '/'
			if not os.path.exists(CSV_DIR) or not os.path.isdir(CSV_DIR):
				# verifying the file exists and it is directory
				print("??? Does not exist, or it is not a directory")
				continue
			local_path = CSV_DIR + ".tmp"
			print("=> local path to get the compressed files from:", local_path)
			
			remote_wd = input("Enter the name of the remote working folder (WITHOUT the prefix 'work/'): ")
			remote_path = "work/" + remote_wd + "/csv"
			print("=> remote path to get transfer the files to:", remote_path)
			transfer_files(HOST, local_path, remote_path)
			
		elif opt == exit_option:
			print("Thanks for using the TST app, by VDITech.- Bye!")
			exit(0)
	
if __name__ == "__main__":
	main()
	
