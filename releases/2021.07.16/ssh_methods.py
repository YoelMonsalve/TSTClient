"""
 * TRANSFER_PY
 * Utility to transfer the content of the gzip-ed files
 * into the folder csv/.tmp to the remote host
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

"""C snippet to handle signals

include <signal.h>

void sigpipe_handler(int unused)
{
}

int main(void)
{
  sigaction(SIGPIPE, &(struct sigaction){sigpipe_handler}, NULL);

  ...
"""

"""snippet to create a new Windows console
https://stackoverflow.com/questions/6469655/how-can-i-spawn-new-shells-to-run-python-scripts-from-a-base-python-script

(option 1) 
import os
os.system("start cmd /K dir") #/K remains the window, /C executes and dies (popup)

(option 2) 
subprocess.popen([sys.executable, 'script.py'], creationflags = subprocess.CREATE_NEW_CONSOLE)
"""

import os
import sys
from sys import stdin, stdout, stderr, argv
import subprocess
from time import sleep
import signal
import re         # regex
import shlex      # quote
from helpers import is_win, is_posix

stdin_fileno  = stdin.fileno()
stdout_fileno = stdout.fileno()
stderr_fileno = stderr.fileno()

def sigpipe_handler(signum, frame):
	"""Custom handler to SIGPIPE: ignore
	This happens when the child ends and closes the pipe, and
	the signal is delivered to the parent
	"""
	print(f"[{os.getpid()}] W: Received SIGPIPE. Event ignored.")


def decompress_files(HOST = "", path = "", verbose = False):
	if not HOST: return
	if not path: return
	
	# define SIGPIPE handler (UNIX)
	if is_posix():
		signal.signal(signal.SIGPIPE, sigpipe_handler)

	# In Windows, we use the more suitable method subprocess, instead of the low-level
	# methods fork() + spawn()
	p    = None
	pipe = None     # PIPE to talk with the child process (= subprocess.STDIN)
	if verbose:
		if is_win():
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags = subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	else:
		if is_win():
			cmd = "ssh -i .ssh/id_rsa tst@" + HOST
			cmd = "cmd /C " + "\"" + cmd + "\""
			p = subprocess.Popen(cmd
				, stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags=subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	
	if not p: return

	# The parent: send commands to child
	pipe = p.stdin
	# set permissions
	s = "chmod 640 \"{:s}\"/*.csv.gz 2> /dev/null;\n".format(path)
	print(s)
	pipe.write(s.encode('utf-8'))
	# decompress
	s  = "echo decompressing ...; "
	s += "ls \"{:s}\"/*.csv.gz 2> /dev/null && (ls \"{:s}\"/*.csv.gz | xargs gzip -df)\n".format(path, path)
	print(s)
	pipe.write(s.encode('utf-8'))
	# list content
	s = "echo \"Done. Content of {:s}:\" && ls -l {:s}\n".format(path, path)
	print(s)
	pipe.write(s.encode('utf-8'));

	# close & exit
	#pipe.write("exit".encode('utf-8'))
	pipe.write("echo -e -n \"\\nTask done. Close this windows to terminate ...\"\n".encode('utf-8'))
	pipe.write("while true; do sleep 30; done".encode('utf-8'))
	pipe.close()

	return p

def inspect_working_directory(HOST = "", path = "", verbose = False):
	if not HOST: return
	if not path: return
	
	# define SIGPIPE handler (UNIX)
	if is_posix():
		signal.signal(signal.SIGPIPE, sigpipe_handler)

	# In Windows, we use the more suitable method subprocess, instead of the low-level
	# methods fork() + spawn()
	p    = None
	pipe = None     # PIPE to talk with the child process (= subprocess.STDIN)
	if verbose:
		if is_win():
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags = subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	else:
		if is_win():
			cmd = "ssh -i .ssh/id_rsa tst@" + HOST
			cmd = "cmd /C " + "\"" + cmd + "\""
			p = subprocess.Popen(cmd
				, stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags=subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	
	if not p: return

	pipe = p.stdin
	# set permissions
	# s = "tree -d {:s} \n".format(path)
	s = "tree {:s} \n".format(path) # Yoel Monsalve 07/16/2021
	pipe.write(s.encode('utf-8'))
	
	# close & exit
	#pipe.write("exit".encode('utf-8'))
	pipe.write("echo -e -n \"\\nTask done. Will close automatically in 10 secs ...\"\n".encode('utf-8'))
	pipe.write("sleep 10\n".encode('utf-8'))
	pipe.close()

	return

def create_directory(HOST = "", new_path = "", mode = 0o750, create_structure = False, verbose = False):
	
	if not HOST: return
	if not new_path: return
	
	# define SIGPIPE handler (UNIX)
	if is_posix():
		signal.signal(signal.SIGPIPE, sigpipe_handler)

	# In Windows, we use the more suitable method subprocess, instead of the low-level
	# methods fork() + spawn()
	p    = None
	pipe = None     # PIPE to talk with the child process (= subprocess.STDIN)
	if verbose:
		if is_win():
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags = subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	else:
		if is_win():
			cmd = "ssh -i .ssh/id_rsa tst@" + HOST
			cmd = "cmd /C " + "\"" + cmd + "\""
			p = subprocess.Popen(cmd
				, stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags=subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	
	if not p: return

	# The parent: send commands to child
	print("SSH connection started, please wait ...")
	
	pipe = p.stdin

	pipe.write(f"echo \"Current content:\" && ls -l .\n".encode('utf-8'));

	# creating remote directory
	pipe.write(f"mkdir -p \"{new_path}\" && echo created '{new_path}' ... success.\n".encode('utf-8'))
	
	# setting mode/perms
	s = "chmod {:o} \"{:s}\" && echo mode changed to {:o} ... success.\n".format(
		mode, new_path, mode)
	pipe.write(s.encode('utf-8'))

	if create_structure:
		# creating directory structure
		s  = "echo \"Creating directory structure ...\"; "
		pipe.write(s.encode('utf-8'))
		# --> /csv
		s = "echo -n \"--> creating {:s}/csv ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/csv\"; ".format(new_path)
		s += "chmod 750 \"{:s}/csv\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> output
		s = "echo -n \"--> creating {:s}/output/ ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/output\"; ".format(new_path)
		s += "chmod 750 \"{:s}/output\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> /output/report
		s = "echo -n \"--> creating {:s}/output/report ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/output/report\"; ".format(new_path)
		s += "chmod 750 \"{:s}/output/report\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> /output/summary
		s = "echo -n \"--> creating {:s}/output/summary ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/output/summary\"; ".format(new_path)
		s += "chmod 750 \"{:s}/output/summary\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))

		# --> plots
		s = "echo -n \"--> creating {:s}/plots/ ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/plots\"; ".format(new_path)
		s += "chmod 750 \"{:s}/plots\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> /plots/angle
		s = "echo -n \"--> creating {:s}/plots/angle ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/plots/angle\"; ".format(new_path)
		s += "chmod 750 \"{:s}/plots/angle\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> /plots/volt
		s = "echo -n \"--> creating {:s}/plots/volt ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/plots/volt\"; ".format(new_path)
		s += "chmod 750 \"{:s}/plots/volt\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))
		# --> /plots/unstable
		s = "echo -n \"--> creating {:s}/plots/unstable ... \"; ".format(new_path)
		s += "mkdir -p \"{:s}/plots/unstable\"; ".format(new_path)
		s += "chmod 750 \"{:s}/plots/unstable\"; ".format(new_path)
		s += "(test $? -eq 0 && echo success );"
		pipe.write(s.encode('utf-8'))

		#s  = "echo \"Directory structure is:\"; "
		#s += "tree -d {:s}".format(new_path)
		#print(s)
		#pipe.write(s.encode('utf-8'))

	# close & exit
	#pipe.write("exit".encode('utf-8'))
	pipe.write("echo -e -n \"\\nTask done. Close this windows to terminate ...\"\n".encode('utf-8'))
	pipe.write("while true; do sleep 30; done".encode('utf-8'))
	pipe.close()

def run_app(HOST = "", working_dir = "", verbose = False):
	if not HOST: return
	if not working_dir: return
	
	# define SIGPIPE handler (UNIX)
	if is_posix():
		signal.signal(signal.SIGPIPE, sigpipe_handler)

	# In Windows, we use the more suitable method subprocess, instead of the low-level
	# methods fork() + spawn()
	p    = None
	pipe = None     # PIPE to talk with the child process (= subprocess.STDIN)
	if verbose:
		if is_win():
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags = subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	else:
		if is_win():
			cmd = "ssh -i .ssh/id_rsa tst@" + HOST
			cmd = "cmd /C " + "\"" + cmd + "\""
			p = subprocess.Popen(cmd
				, stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, creationflags=subprocess.CREATE_NEW_CONSOLE
				, close_fds=True
				)
		else:
			p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
				"tst@" + HOST], 
				stdin=subprocess.PIPE
				#, stdout=sys.stdout, stderr=subprocess.STDOUT
				, close_fds=True
				)
	
	if not p: return

	pipe = p.stdin
	# set permissions
	s = "./run {:s} \n".format(working_dir)
	pipe.write(s.encode('utf-8'))
	
	# close & exit
	#pipe.write("exit".encode('utf-8'))
	#pipe.write("echo -e -n \"\\nTask done. Will close automatically in 10 secs ...\"\n".encode('utf-8'))
	#pipe.write("sleep 10\n".encode('utf-8'))
	pipe.write("echo -e -n \"\\nTask done. Close this windows to terminate ...\"\n".encode('utf-8'))
	pipe.write("while true; do sleep 30; done".encode('utf-8'))
	pipe.close()

	return
	
def test():
	"""Test code"""
	
	HOST = "54.38.79.195"
	new_dir = "2021S_2"
	#p =create_directory(HOST, new_dir, 0o750, create_structure = True)
	#p = decompress_files(HOST, new_dir + '/csv')
	#p = inspect_working_directory(HOST, new_dir)
	p = run_app(HOST, new_dir)
	exit(0)
	
if __name__ == "__main__":
	test()
	
