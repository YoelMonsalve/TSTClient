#!/usr/bin/env python3
"""
 * HELPERS_PY
 * Module with auxiliary functions
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "January, 2019"
__modified__  = "2021-11-11"
__version__   = "0.9.2"
__copyright__ = "VDI Technologies, LLC"

import os
import sys
import signal
from datetime import datetime, timedelta
import traceback

# Makes a timestamp in the format: [%Y-%m-%d %H:%M:%S.%f]
# @utc_server_file: the output file used by the live UTC server
def timestamp( utc_server_file, enclose = True ):

    # Verifying arguments
    if not check_arg_type( utc_server_file, str ):
        sys.stderr.write( "functions.timestamp: argument 'utc_server_file' is not (convertible to) a string\n" )
        return ""

    if utc_server_file == "":
        sys.stderr.write( "functions.timestamp: argument 'utc_server_file' is empty string (\"\")\n" )
        return ""

    curr_time = utc.get_current_utc( utc_server_file )
    if not curr_time is None:
        if enclose:
            return datetime.strftime( curr_time, "[%Y-%m-%d %H:%M:%S.%f]" )
        else:
            return datetime.strftime( curr_time, "%Y-%m-%d %H:%M:%S.%f" )
    else:
        return "[unable to get time]"


# Prints a log message over the specified file.
# First, check if the file exists. If yes, appends to the file.
# Else, creates it and write over.
#
# @msg:             the message to log
# @utc_server_file: the output file used by the live UTC server
# @log_file:        the file over which to log
def logMsg( msg, utc_server_file, log_file ):

    # Verifying arguments
    if not check_arg_type( msg, str ):
        sys.stderr.write( "functions.logMsg: argument 'msg' is not (convertible to) a string\n" )
        return ""
    if not check_arg_type( utc_server_file, str ):
        sys.stderr.write( "functions.logMsg: argument 'utc_server_file' is not (convertible to) a string\n" )
        return ""
    if not check_arg_type( log_file, str ):
        sys.stderr.write( "functions.logMsg: argument 'log_file' is not (convertible to) a string\n" )
        return ""

    if log_file == "":
        # empty log file
        return ""   

    # Re-written to low-level methods os.open(), os.write(), os.close(),
    # to avoid issued with the built-in function open() when discharging
    # global objects, such as globalTracker.
    # 2020.12.15.- Yoel Monsalve.
    fd1 = 0
    try:
        if os.path.isfile( log_file ):
            fd1 = os.open( log_file, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o220 )
        else:
            fd1 = os.open( log_file, os.O_CREAT | os.O_WRONLY, 0o220 )
        if fd1 > 0:
            os.write( fd1, bytes("%s %s\n" % (timestamp( utc_server_file ), msg ), 'utf-8' ) )
            os.close(fd1)
            
    except Exception as ex:
        sys.stderr.write( "Unable to log to '{:s}' the message:\n\t{:s} {:s}\n". 
          format( log_file, timestamp( utc_server_file ), msg ) )
        sys.stderr.write( traceback.format_exc() + '\n' )

# True if the arg is of type __type, or it is convertible to such a type
def check_arg_type( arg, __type ):

    if not type(arg) is __type:
        try:
            __type( arg )
            return True
        except:
            return False
    else:
        return True

# A simple implementation of getchar( )
def getchar( ):
    
    sys.stdin.read( 1 )
    
# Try to parse as a float, or zero otherwise
def parseFloat( s ):

    try:
        return float( s )
    except:
        return 0.0

# Creates a directory, if it doesn't exist
def create_dir( dirname ):

    if dirname == "": return

    if not os.path.isdir( dirname ):
        try:
            # exists_ok is only for 3.2+
            #os.makedirs( dirname, exist_ok = True )
            os.makedirs( dirname )
        except OSError as e:
            if e.errno != e.EEXIST:
                raise

""" 
Attempts to add a signal if it doesn't exist
@param signame: string, name of the new signal, e.g. mySIG
@param signum:  (optional) int, the value desired for signame, e.g. 10
          If the value already is assigned to another existing signal, 
          tries to assign another value, and returns it
@return   the value for the new signal, possibly reassigned

@author: Yoel Monsalve.
@date:   2019.
"""
def __add_signal( signame, signum = 0 ) :

    if signame in signal.Signals.__members__:
        return signal.Signals[signame]

    MAX_VALUE = int(0)
    EXISTS = False

    # try to assign with a non-existing value
    for s in signal.Signals:
        sigval = int( s.value )
        if sigval == signum:
            EXISTS = True

        if sigval > MAX_VALUE:
            MAX_VALUE = sigval

    print( "MAX_VALUE is " + str(MAX_VALUE) )
    if signum == 0 or EXISTS:
        signum = MAX_VALUE + 1

    #signal.Signals[signame] = signum
    return signum

"""
Converts a timedelta less than 1 day, into a human readable time in
the format hh:mm:ss

NOTE: another simpler, and pythonic form, is just ==> str(d)  (!!!)
"""
def timedelta_to_human( d ):

    days = d.days
    secs = d.seconds

    # taking all to a consistent time in seconds
    secs = days * 86400 + secs

    if secs < 0:
        minus = True
        secs = -secs
    else:
        minus = False

    hours = int( secs / 3600 )

    # the fraction of 1 hour
    secs -= hours * 3600

    mins = int( secs / 60 )

    # the fraction of 1 min
    secs -= mins * 60

    s = "-" if minus else ""
    s = s + "%02d:%02d:%02d" % (hours, mins, secs)
    return s

def timestamp():
    return f"[{datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}]"

def is_win():

    if sys.platform.lower() == "win32" or sys.platform.lower() == "win64":
        return True
    else:
        return False

def is_posix():

    if os.name.lower() == "posix":
        # Note: this includes Linux as well
        return True
    else:
        return False

def csv_print_row(f, row, delimiter=','):
    """Prints out a row in CSV file, using the given delimiter (',' by default)
    It is similar to the method writerow of the csv writer given in the python 
    library csv.

    :param f: file object, as returned by the built-in method open()
    :type f: the type returned by open()
    :param row: row to be printed
    :type row: list (array)
    :param delimiter: delimiter character
    :type delimiter: string

    :returns: True if success, False otherwise
    """
    line = ''
    for i in range(len(row)):
        if i > 0: line += delimiter
    line += str(row[i])
    try:
        f.write(line + "\n")
    except Exception as e:
        sys.stderr.write("matchTracker.print_row: Exception: " + str(e) + "\n" )
        return False
    # success
    return True

def secureSecretFile(filename = '', mode = 0o640):
    """
    This implements a secure policy for a secret file (not allowed to be
    read by thirds):
    a) If the file already exists, change it to specified mode (default 640).
    b) If does not exist, create it with the given mode

    @return True if the file actually existed, False otherwise
    """
    try:
        # file actually does not exist
        fd = os.open(filename, os.O_CREAT | os.O_EXCL, mode)
        os.close(fd)
        return False
    except Exception as e:
        # file exists, changing permissions
        os.chmod(filename, mode)
        return True 

def _create_dir(path, mode=0o750):
    """
    Creates a local dir. Check if the file already exists and if it is a directory.
    
    :param      path:  The path
    :type       path:  str
    
    :returns:   True if the file does not exist (and could create it successfully),
                or if it already exists and it is a directory. False Otherwise, or
                if an error occurred (e.g. permissions)
    :rtype:     bool
    """
    __path = ''
    ds = '/'
    for f in path.split(ds):
        __path += f
        #print("checking " + __path)
        if not os.path.exists(__path):
            print(f"creating '{__path}'")
            try:
                os.mkdir(__path, mode)
                __path += ds
            except Exception as e:
                stderr.write(f"{os.path.basename(__file__)}: _create_dir: {str(e)}\n")
                return False
        elif not os.path.isdir(__path):
            print(f"conflict with existing file: '{__path}'")
            print("Delete it first, and try later")
            return False
        else:
            # already exists, and it is a directory. All OK
            __path += ds
            pass

    return True

def create_logfile_name():
    """
    Defines a name for a logfile based in the current timestamp
    """
    d_now = datetime.now()

    log_dir = f"log/{d_now.strftime('%Y')}/{d_now.strftime('%m')}/{d_now.strftime('%d')}"
    if not os.path.exists(log_dir) or not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    return log_dir + f"/{datetime.now().strftime('%Y_%m_%dT%H_%M_%S')}.log"

def create_logfile():
    """
    Creates a logfile, which name is the one given by the function 
    create_logfile_name()
    """
    filename = create_logfile_name()
    secureSecretFile(filename=filename, mode = 0o640)
    f = open(filename, 'w')
    return f

def log(filename='', msg=''):
    """
    Log a message into a file
    
    :param      filename:    the file name
    :type       filename:    str
    :param      msg:         The message
    :type       msg:         str
    """
    if not filename: return
    os.chmod(filename, 0o640)
    with open(filename, 'a') as f:
        f.write(f"{timestamp()} {msg}\n")

