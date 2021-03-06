"""
 * COMPRESS_PY
 * Utility to compress the content of the CSV folder
 * using the gzip format, prior to transmission.
 *
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "June, 2019"
__modified__  = "July, 2021"
__version__   = ""
__copyright__ = "VDI Technologies, LLC"

import os
from sys import stdin, stdout, stderr, argv, exit
import sys
import stat    # chmod
import re      # regex
from datetime import datetime, timedelta
import gzip

def compress_files(DIR = ''):

	if not DIR:
		stderr.write(f"{sys.argv[0]}: compress_files: No directory specified")

	# appending '/' to the final of path
	if not DIR[-1] == '/': DIR += '/'
	
	# creating temporary directory
	TMP = DIR + '.tmp/'
	print(f"Reading folder: {TMP}")
	if not (os.path.exists(TMP) and os.path.isdir(TMP)):
		os.mkdir(TMP)
		os.chmod(TMP, mode=0o770)

	OW_ALL  = False        # overwrite all
	NOW_ALL = False        # don't overwrite any
	OW      = True         # overwrite this

	t1 = datetime.now()
	for filename in os.listdir(DIR):
		
		# only taking .CSV files
		matcher = re.compile(r".*\.csv$")
		if matcher.match(filename):
			stdout.write(f"  reading: {filename}")
		else:
			#print("  does not match", filename)
			continue
		
		path_in = DIR + filename
		if os.path.exists(path_in) and os.path.isfile(path_in):
			# if it is a regular file
			o_mode = os.stat(path_in).st_mode
			if not o_mode & stat.S_IRUSR:
				print(f"\n  changing mode for {path_in} to user-readable")
				stdout.flush()
				os.chmod(path_in, o_mode | stat.S_IRUSR)
			
			fi = open(path_in, "rb")
			if fi:
				data = fi.read()
				
				path_out = TMP + filename + ".gz"
				OW = False
				if OW_ALL: OW = True
				if not OW_ALL and os.path.isfile(path_out):
					if NOW_ALL:
						print("    skipping") 
						continue
					else:
						ans = input(f"\n    Overwrite {path_out}? [y]es / [n]o / [Y]es to all / [N]ot to all: ")
						if ans == 'y': 
							OW = True
						elif ans == 'Y': 
							OW_ALL = True
							OW = True
						elif ans == 'N': 
							NOW_ALL = True
						else:
							continue    # skip this file
				"""try:
					zip_data = gzip.compress(data, compresslevel = 5)
					
				except Exception as e:
					stderr.write("gzip error: " + str(e) + '\n')
				
				path_out = TMP + filename + ".gz"
				fo = open(path_out, "wb")
				fo.write(zip_data)
				fo.close()
				"""
				
				fzip = gzip.open(path_out, mode="wb", compresslevel = 5)
				if fzip:
					fzip.write(data)
					#print("written to " + path_out)
					#fzip.close()
				else:
					stderr.write(f"error: creating the gzip gile '{path_out}'\n")
					
				fi.close()
				print("    done")
	
	print(f"Were compressed to {TMP}")
	t2 = datetime.now()
	print("Processed in", t2 - t1)

def test():
	"""Test code"""
	
	DIR = "../work/2021S_2/csv/"
	compress_files(DIR)
	
if __name__ == "__main__":
	test()
	
