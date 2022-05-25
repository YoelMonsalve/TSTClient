#!/usr/bin/env python3
"""
 * COMPRESS_PY
 * Utility to compress the content of the CSV folder
 * using the gzip format, prior to transmission.
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "June, 2021"
__modified__  = "2021-11-05"
__version__   = "0.9.2"
__copyright__ = "VDI Technologies, LLC"

import os
from sys import stdin, stdout, stderr, argv, exit
import sys
import stat    # chmod
import re      # regex
from datetime import datetime, timedelta
import gzip

# helpers
from helpers import getchar

# session
from session import CLI_session

def compress_files(DIR = '', session = None):
    """
    Compress files contained in DIR, into a temporal folder,
    ready to be transmitted.
    
    :param      DIR:      the name of the directory containing the files (csv)
    :type       DIR:      str
    :param      session:  optional, a session over what to log the operations
    :type       session:  object, CLI_session
    """

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

    Y_ALL = False        # overwrite all
    N_ALL = False        # don't overwrite any
    OW    = True         # overwrite this

    t1 = datetime.now()

    # count files
    total = 0
    for filename in os.listdir(DIR):    
        # only taking .CSV files
        matcher = re.compile(r".*\.csv$")
        if matcher.match(filename):
            total += 1

    count     = 0
    succeeded = 0
    failed    = 0
    for filename in os.listdir(DIR):
        
        # only taking .CSV files
        matcher = re.compile(r".*\.csv$")
        if matcher.match(filename):
            count += 1
            print(f"[{count}/{total}]  reading: {filename}")
            
            #...................................quit this later !
            #if count > 10: break
        else:
            #print("  does not match", filename)
            continue
        
        path_in = DIR + filename
        if os.path.exists(path_in) and os.path.isfile(path_in):
            # if it is a regular file
            o_mode = os.stat(path_in).st_mode
            if not o_mode & stat.S_IRUSR:
                print(f"  changing mode for {path_in} to user-readable")
                stdout.flush()
                os.chmod(path_in, o_mode | stat.S_IRUSR)
            
            fi = open(path_in, "rb")
            if fi:
                data = fi.read()
                
                path_out = TMP + filename + ".gz"
                OW = False
                if Y_ALL: OW = True
                if not Y_ALL and os.path.isfile(path_out):
                    if N_ALL:
                        print("    skipping") 
                        continue
                    else:
                        ans = input(f"    Overwrite {path_out}? [y]es / [n]o / [Y]es to all / [N]ot to all: ")
                        if ans == 'y': 
                            OW = True
                        elif ans == 'Y': 
                            Y_ALL = True
                            OW    = True
                        elif ans == 'N': 
                            N_ALL = True
                            print("    skipping") 
                            continue
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
                    print(f"    written to '{path_out}'\n    done")
                    fzip.close()
                    succeeded += 1

                    # log the event (if a session was given)
                    if session:
                        session.log(f"file `{DIR}{filename}` compressed to `{path_out}`")
                else:
                    print(f"  error: creating the gzip gile `{path_out}`\n")
                    failed += 1

                    # log the event (if a session was given)
                    if session:
                        session.log(f"E: compression of `{filename}` failed")
                    
                fi.close()
    
    print(f"Were compressed to {TMP}")
    print(f"{succeeded} succeeded, {failed} failed")
    t2 = datetime.now()
    print("Processed in", t2 - t1)

    print("Press ENTER to continue ...")
    getchar()

def test():
    """Test code"""

    session = CLI_session()
    
    DIR = "../../../Files/2019_TPL/21S/csv_obfuscated"
    compress_files(DIR, session)
    
if __name__ == "__main__":
    test()
    
