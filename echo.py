"""Simple echo program
@throws Exception
"""
import sys
from sys import stdin, stdout, stderr
from time import sleep

stderr.write("child: I'm the echo program\nIntro a command\n")
while 1:
	try:
		cmd = sys.stdin.readline().strip()
		stdout.write('>> ' + cmd + '\n')        # echoing
	except Exception as e:
		stderr.write("exception: " + str(e) + ". Ignoring\n")
	#exit()
	sleep(3.0)
	exit()
	if cmd.lower() == "end": break

stderr.write("child: bye!\n")
exit(0)

