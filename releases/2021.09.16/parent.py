"""Parent process of the simple echo subprogram
"""

"""include <signal.h>

void sigpipe_handler(int unused)
{
}

int main(void)
{
  sigaction(SIGPIPE, &(struct sigaction){sigpipe_handler}, NULL);

  ...
"""

import os
import sys
from sys import stdin, stdout, stderr
import subprocess
from time import sleep
import signal
import re         # regex
from helpers import is_win, is_posix

stdin_fileno  = stdin.fileno()
stdout_fileno = stdout.fileno()
stderr_fileno = stderr.fileno()

def sigpipe_handler(signum, frame):
	print(f"[{os.getpid()}] W: Received SIGPIPE. Event ignored.")

"""
(r,w) = os.pipe()
print("Creating the child")
pid = os.fork()

if pid == 0:
	# the child
	os.close(w)     # close the write-end
	
	#os.close(stdin_fileno)
	#os.dup(r)
	os.dup2(r, stdin_fileno)
	
	#buf = os.read(r, 4)
	#buf = sys.stdin.readline().strip()
	#buf = sys.stdin.read(4)
	#print("child read: " + buf.decode('utf-8') + '\n')
	#print("child read: " + buf + '\n')
	
	#cpid = os.spawnvp(os.P_NOWAIT, "python", ["python", "echo.py"])
	#os.spawnv(os.P_NOWAIT, "/usr/bin/ls", ["ls", "."])
	#os.spawnvp(os.P_NOWAIT, "sftp", ["sftp", "tst@54.38.79.195"])
	#os.spawnlp(os.P_NOWAIT, "sftp", "sftp -v yoel@localhost")
	#cpid = os.spawnvp(os.P_NOWAIT, "sftp", ["sftp", "-v", "yoel@localhost"])
	
	#cpid = os.spawnlp(os.P_NOWAIT, "sftp", "sftp", "-v", "-i", ".ssh/id_rsa", 
	#"-b", "scripts/transfer.sftp", "tst@54.38.79.195")
	
	cpid = os.spawnlp(os.P_NOWAIT, "sftp", "sftp", "-i", ".ssh/id_rsa", 
	"tst@54.38.79.195")
	print(f"[{os.getpid()}] created child pid: {cpid}")
	os.close(r)
	exit(0)
	
elif pid > 0:
	
	# define SIGPIPE handler
	signal.signal(signal.SIGPIPE, sigpipe_handler)
	
	# the parent
	os.close(r)     # close the read-end
	
	#os.dup2(w, stdout_fileno)
	#os.write(w, 'foooo\n'.encode('utf-8'))
	#stdout.write('foo\n')
	
	print("SFTP connection started, please wait ...")
	
	# see local path
	os.write(w, b"!pwd\n")
	
	# see remote path
	os.write(w, b"pwd\n")
	
	# changing local directory
	os.write(w, b"lcd ../work/2021S_2/csv/.tmp/\n")
	
	# changing remote directory
	os.write(w, b"cd work/2021S_2/csv/\n")
	
	# files to be transferred
	os.write(w, b"!ls *.csv.gz\n")
	
	#os.write(w, b"progress\n")
	#os.write(w, b"put P1-1-002-002_2021S_out.csv.gz\n")
	#os.write(w, b"put P1-1-002-002_2021S_out.csv.gz\n")
	#print('foooo')
	#sleep(1.0)
	#os.write(w, 'buuuu\n'.encode('utf-8'))
	#stdout.write('buuuu\n'.encode('utf-8'))
	#print('buuuu')
	#sleep(1.0)
	#os.write(w, 'end\n'.encode('utf-8'))
	#stdout.write('end\n'.encode('utf-8'))
	#print('end')
	
	matcher = re.compile(r".*\.csv\.gz$")
	for f in os.listdir("../work/2021S_2/csv/.tmp/"):
		if matcher.match(f):
			os.write(w, (f"put \"{f}\"\n").encode('utf-8'))
			break

	os.write(w, b"exit\n")
	
	try:
		while os.waitpid(pid, os.WNOHANG):
			print("parent: waiting for child")
			sleep(1.0)
	except Exception as e:
		print("parent: exception: " + str(e) + '\n')
		pass
	print(f"parent: child done\n")
	
	os.close(w)

	exit(0)
"""	
#exit(0)

"""
matcher = re.compile(r".*\.csv$")
	if matcher.match(filename):
		stdout.write(f"  reading: {filename}")
"""

# define SIGPIPE handler
#signal.signal(signal.SIGPIPE, sigpipe_handler)

print("Creating the child")
#subprocess.Popen(["python", "./echo.py"], stdin=
#p = subprocess.Popen(["ls", "."], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#p = subprocess.Popen(["python", "./echo.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#p = subprocess.Popen(["sftp", "-i", ".ssh/id_rsa", 
#	"tst@54.38.79.195"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#p = subprocess.Popen(["sftp", "yoel@localhost"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#p = subprocess.Popen(["sftp", "-i", ".ssh/id_rsa", 
#	"-b", "scripts/transfer.sftp", "tst@54.38.79.195"], stdin=subprocess.PIPE, 
#	stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

p = subprocess.Popen(["sftp", "-i", ".ssh/id_rsa", 
	"-b", "scripts/transfer.sftp", "tst@54.38.79.195"], stdin=subprocess.PIPE)

"""
if p is not None:
	r = p.communicate(b"pwd\n")
	print(r)
	print("out =>", r[0].decode())
	if r[1]: print("err =>", r[1].decode())
"""

#p.kill()
p.wait()
