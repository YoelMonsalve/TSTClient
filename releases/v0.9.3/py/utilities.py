#!/usr/bin/env python3
"""
 * UTILITIES
 * Utilities to be perfomed via SSH (inspect or create directories, 
 * rename directories, etc)
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "July, 2021"
__modified__  = "2021-11-06"
__version__   = "0.9.3"
__copyright__ = "VDI Technologies, LLC"


import os
import sys
from sys import stdin, stdout, stderr, argv
import subprocess
from datetime import datetime, timedelta
from time import sleep
import signal
import re         # regex
from helpers import is_win, is_posix
from shutil import copy, move, rmtree        # file operations

import stat

# helpers
from helpers import getchar

# session
from session import CLI_session

# INDEX OF FUNCTIONS
# ================================
""" 
sigpipe_handler:
    Custom handler to SIGPIPE: ignore
    This happens when the child ends and closes the pipe, and
    the signal is delivered to the parent

rename_folder:
    Rename an existing directory or file
    
remove_folder:
    Remove an existing directory or file

clean_csv:
    Clean the data files

inspect_wd:
    Prints a 'tree' of the referred path.
    It is useful to get a view of a remote directory

create_directory:
    Creates a directory.

    Structure
    ===========================

    `-- csv
    `-- output
        `-- report
        `-- summary
    `-- plots
        `-- angle
        `-- volt
        `-- unstable
    `-- log

run_app:
    Run completely the app in the server side

"""

def create_directory(new_path = "", mode = 0o770,
    create_structure = False):
    """
    Creates a directory.
    
    :param      new_path:          The new path
    :type       new_path:          str
    :param      mode:              The mode
    :type       mode:              octal
    :param      create_structure:  Create or not a substructure
    :type       create_structure:  bool

    Structure
    ===========================

    `-- csv
    `-- output
        `-- report
        `-- summary
    `-- plots
        `-- angle
        `-- volt
        `-- unstable
    `-- log
    """
    
    if not new_path: return

    # First, to check that the folder actually exist
    if not os.path.exists(new_path):
        stderr.write(f"The path '{new_path}' does not exist. You need to create it first.\n")
        return
    elif not os.path.isdir(new_path):
        stderr.write(f"The path '{new_path}' is not a directory.\n")
        return

    # setting mode/perms
    try:
        os.chmod(new_path, mode)
    except Exception as e:
        stderr.write("chmod: " + str(e) + '\n')
        return
    print(f"mode of '{new_path}' changed to {mode:o} ... success.")
    
    if create_structure:
        # creating directory structure
        print("Creating directory structure ...")
        # --> /csv
        path = f"{new_path:s}/csv"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /log
        path = f"{new_path:s}/log"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> output
        path = f"{new_path:s}/output"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /output/report
        path = f"{new_path:s}/output/report"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /output/summary
        path = f"{new_path:s}/output/summary"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")

        # --> plots
        path = f"{new_path:s}/plots"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /plots/angle
        path = f"{new_path:s}/plots/angle"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /plots/volt
        path = f"{new_path:s}/plots/volt"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")
        # --> /plots/unstable
        path = f"{new_path:s}/plots/unstable"
        print(f"--> creating '{path}' ...")
        if not os.path.exists(path):
            os.mkdir(path, 0o750);
            print("    success")
        else:
            print("    already exists")

        print()

    # close & exit
    print("Create directory done.")
    return

def rename_folder(old_path, new_path):
    """
    Rename an existing directory or file
    
    :param      old_path:    The current path to the folder (e.g. old/name/to/folder)
    :type       old_path:    str
    :param      new_path:    The new name/path to the folder (e.g. new/name/to/folder)
    :type       new_path:    str
    """

    if not old_path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'old_path'\n")
        return
    if not new_path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'new_path'\n")
        return

    # check that the old directory exists, and the new_directory does NOT exist
    try:
        os.stat(old_path)
    except FileNotFoundError:
        print(f"Folder '{old_path}' does not exist in the working directory")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: {str(e)}\n")
        return

    try:
        os.stat(new_path)
        print(f"The new name '{new_path}' cannot be an existing file/folder in the working directory")
        return
    except FileNotFoundError:
        # if it does not exist, it's OK
        pass
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: {str(e)}\n")
        return

    # Build a LINUX command to execute the sentences
    os.rename(old_path, new_path)
    print("Rename folder done.")

    return

def remove_folder(path):
    """
    Remove an existing directory or file
    
    :param      path:        The path to the folder (e.g. path/to/folder)
    :type       path:        str
    """

    if not path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: remove_folder: invalid argument 'path'\n")
        return

    # check that the directory exists
    try:
        os.stat(path)
    except FileNotFoundError:
        print(f"Folder '{path}' does not exist in the working directory")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: remove_folder: {str(e)}\n")
        return
    
    # Ask user to confirm before to proceed
    ans = input(f"Are you sure to completely remove the folder '{path}'? y/[n]: ")
    if not ans.lower() == 'y':
        return
    
    # Build a LINUX command to execute the sentences
    rmtree(path)
    print("Remove folder done.")

    return

def clean_csv(path):
    """
    Clean the content of the folder 'csv' into the given path.
    This utility can be used to clean the CSV files for a case-study.
    
    :param      path:        The path to the folder (e.g. path/to/folder)
    :type       path:        str
    """

    if not path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: clean_csv: invalid argument 'path'\n")
        return

    # check that the directory exists
    try:
        os.stat(path + '/csv')
    except FileNotFoundError:
        stderr.write(f"Folder '{path}/csv' does not exist in the working directory\n")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: clean_csv: {str(e)}\n")
        return

    # Ask user to confirm before to proceed
    ans = input(f"Are you sure to completely remove the folder '{path}/csv'? y/[n]: ")
    if not ans.lower() == 'y':
        return
    
    # Build a LINUX command to execute the sentences
    rmtree(path + "/csv")
    stderr.write(f"Folder '{path}/csv' were successfully deleted\n")
    return

def run_app(working_dir):
    """
    Run completely the app in the 'LOCAL' side
    
    :param      working_dir:  The folder/case over what to run the app (e.g. 2019_TPL/21S)
    :type       working_dir:  str
    """

    if not working_dir: 
        print("run_app: working_dir is empty")
        return
    PATH_TO_APP = 'app'

    # STEP 1.- Verify the working directory
    # checking directories
    DIR = working_dir
    if not os.path.isdir(DIR + '/csv'):
        stderr.write(f"There is not a directory '{DIR}/csv'" \
        + "\nNothing changed. Exiting.\n")
        return 0        # this means no error

    csv_list = []
    for file in os.listdir(DIR + '/csv'):
        # filtering by csv's
        if len(file) > 4 and file[-4:] == '.csv':
            csv_list.append(file)
    if len(csv_list) == 0:
        stderr.writse(f"There is not CSV files into '{DIR}/csv'" \
        + "\nNothing changed. Exiting.\n")
        return 0

    # STEP 2.- Running the TST App
    ## log name
    t_now = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
    LOGNAME = f"{DIR}/log/TST_{t_now}.log"
    with open(LOGNAME, 'w') as f:
        pass    # this will blank the file

    if is_win():
        ds = "\\"   # DOS systems
    else:
        ds = "/"    # POSIX systems
        
    index_file = DIR + ds + 'index.lst'
    try:
        f = open(index_file, 'w')
    except Exception as e:
        stderr.write(f"Error while opening {index_file}: {str(e)}\n")
        return 1
    for file in csv_list:
        f.write(f"{DIR}/csv/{file}\t{DIR}/output/report/{file}.report\t{DIR}/output/summary/{file}.summary\n")
    f.close()

    p = None
    if is_win():
        cmd = f"{PATH_TO_APP}\\bin\\tst.exe {index_file}"
        p = subprocess.Popen(cmd
            , stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            #, creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
        )
    elif is_posix():
        PATH_TO_APP = './app'
        p = subprocess.Popen([f"{PATH_TO_APP}/bin/tst", index_file],
            stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            , close_fds=True
        )
    else:
        stderr.write(f"Unknown system. Unable to run subprocess.\n")
        return 1
    if not p: 
        # no process was created
        stderr.write(f"Could not create subsubprocess.\n")
        return 1

    # wait for the current process to terminate
    TIMEOUT = 30        # 30  mins
    try:
        ret = p.wait(timeout = 60 * TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr.write(f"TST App: timeout expired (after {TIMEOUT} minutes)\n")
        return 2
    except Exception as e:
        stderr.write(f"TST App: an exception has occurred: {str(e)}\n")
        p.kill()
        return 1
    if os.path.exists("./Failure-Report.csv") and os.path.isfile("./Failure-Report.csv"):
        copy("./Failure-Report.csv", DIR)
        os.remove("./Failure-Report.csv")
    
    # ---
    # prompt user to continue
    # ---
    input("Press ENTER to continue ...")

    # STEP 3.- Build Plots
    ## 3.1.- All plots
    stderr.write("\nPlotting figures, ... wait\n")
    sleep(1.0)

    list_file = 'list'
    try:
        f = open(list_file, 'w')
    except Exception as e:
        stderr.write(f"Error while opening '{list_file}': {str(e)}\n")
        return 1
    for file in csv_list:
        f.write(f"{DIR}/csv/{file}\n")
    f.close()    

    if is_win():
        # this is the Python path to the local environment
        py_ = "winenv\\Scripts\\python.exe"
        # plot-all2.py is the Windows version, not multiprocessed, for
        # the plotting program
        cmd = f"{py_} {PATH_TO_APP}/py/plot-all2.py {list_file} {DIR}{ds}plots"
        print(cmd)
        p = subprocess.Popen(cmd
            , stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            #, creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True)
    elif is_posix():
        #py_ = "env/bin/python"
        py_ = "python"
        p = subprocess.Popen([py_, f"{PATH_TO_APP}/py/plot-all.py", list_file, f"{DIR}/plots"],
            stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            , close_fds=True)
    else:
        stderr.write(f"Unknown system. Unable to run subprocess.\n")
        return 1
    
    # wait for the current process to terminate
    TIMEOUT = 30        # 30  mins
    try:
        ret = p.wait(timeout = 60 * TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr.write(f"Plot figures: timeout expired (after {TIMEOUT} minutes)\n")
        return 2
    except Exception as e:
        stderr.write(f"Plot figures: an exception has occurred: {str(e)}\n")
        p.kill()
        return 1
    os.remove(list_file)      # cleaning up

    
    # ---
    # prompt user to continue
    # ---
    input("Press ENTER to continue ...")

    ## 3.2.- Unstable plots
    stderr.write("\n***UNSTABLE CASES***\n")
    sleep(1.0)

    if is_win():
        # this is the Python path to the local environment
        py_ = "winenv\\Scripts\\python.exe"
        # plot-untable2.py is the Windows version, not multiprocessed, for
        # the plotting program
        cmd = f"{py_} {PATH_TO_APP}/py/plot-unstable2.py {DIR}{ds}Failure-Report.csv {DIR}{ds}plots{ds}unstable"
        print(cmd)
        p = subprocess.Popen(cmd
            , stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            #, creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
    elif is_posix():
        #py_ = "env/bin/python"
        py_ = "python"
        p = subprocess.Popen([py_, f"{PATH_TO_APP}/py/plot-unstable.py", f"{DIR}/Failure-Report.csv", 
            f"{DIR}/plots/unstable"],
            stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            , close_fds=True
            )
    else:
        stderr.write(f"Unknown system. Unable to run subprocess.\n")
        return

    # wait for the current process to terminate
    TIMEOUT = 30        # 30  mins
    try:
        ret = p.wait(timeout = 60 * TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr.write(f"Plot unstables: timeout expired (after {TIMEOUT} minutes)\n")
        return 2
    except Exception as e:
        stderr.write(f"Plot unstables: an exception has occurred: {str(e)}\n")
        p.kill()
        return 1

    # success
    stderr.write("\nRun App done. Success.\n")
    return 0        
    
def build_master_report(working_dir, xls_file = "Master-Report.xlsx"):
    """
    Generates a MasterReport for all the UNSTABLE cases in a exercise
    
    @param  exercise_dir  str  The directory corresponding to the exercise to process
    @param  xls_name      str  The desired name to the output Excel file (defaults to 'Master-Report.xlsx')
    """
    
    if not working_dir:
        print("build_master_report: working_dir is empty")
        return 1
    PATH_TO_APP = 'app'

    TEMPLATE_NAME = 'Master-Report(template).xlsx'
    REPORT_NAME   = 'Master-Report.xlsx'
    if not os.path.isfile(f"./templates/{TEMPLATE_NAME}"):
        print(f"build_master_report: error: file ./templates/{TEMPLATE_NAME} does not exist")
        return 1
    copy(f"./templates/{TEMPLATE_NAME}", f"{working_dir}/{REPORT_NAME}")

    p = None
    if is_win():
        # this is the Python path to the local environment
        py_ = "winenv\\Scripts\\python.exe"
        cmd = f"{py_} {PATH_TO_APP}/py/build_master_report.py {working_dir} {REPORT_NAME}"
        print(cmd)
        p = subprocess.Popen(cmd
            , stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            #, creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
    elif is_posix():
        #py_ = "env/bin/python"
        py_ = "python"
        p = subprocess.Popen([py_, f"{PATH_TO_APP}/py/build_master_report.py", working_dir, 
            REPORT_NAME],
            stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            , close_fds=True
            )
    else:
        stderr.write(f"Unknown system. Unable to run subprocess.\n")
        return

    # wait for the current process to terminate
    TIMEOUT = 1        # 1  mins
    try:
        ret = p.wait(timeout = 60 * TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr.write(f"Master-Report: timeout expired (after {TIMEOUT} minutes\n")
        return 2
    except Exception as e:
        stderr.write(f"Master-Report: an exception has occurred: {str(e)}\n")
        p.kill()
        return 1

    # success
    stderr.write("Generating Master Report done. Success.\n")
    return 0        

def build_judgement(working_dir, xls_file = "Judgment.xlsx"):
    """
    Generates a Judgement Excel file for all the UNSTABLE cases in a exercise
    
    @param  exercise_dir  str  The directory corresponding to the exercise to process
    @param  xls_name      str  The desired name to the output Excel file (defaults to 'Judgement.xlsx')
    """
    
    if not working_dir:
        print("build_judgement: working_dir is empty")
        return 1
    PATH_TO_APP = 'app'

    TEMPLATE_NAME = 'Judgement(template).xlsx'
    REPORT_NAME   = 'Judgement.xlsx'

    p = None
    if is_win():
        # this is the Python path to the local environment
        py_ = "winenv\\Scripts\\python.exe"
        cmd = f"{py_} {PATH_TO_APP}/py/discrimination.py {working_dir} {REPORT_NAME}"
        print(cmd)
        p = subprocess.Popen(cmd
            , stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            #, creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
    elif is_posix():
        #py_ = "env/bin/python"
        py_ = "python"
        p = subprocess.Popen([py_, f"{PATH_TO_APP}/py/discrimination.py", working_dir, 
            REPORT_NAME],
            stdin=subprocess.PIPE
            , stdout=sys.stdout, stderr=subprocess.STDOUT
            , close_fds=True
            )
    else:
        stderr.write(f"Unknown system. Unable to run subprocess.\n")
        return

    # wait for the current process to terminate
    TIMEOUT = 1        # 1  mins
    try:
        ret = p.wait(timeout = 60 * TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr.write(f"Judgement: timeout expired (after {TIMEOUT} minutes\n")
        return 2
    except Exception as e:
        stderr.write(f"Judgment: an exception has occurred: {str(e)}\n")
        p.kill()
        return 1

    # success
    stderr.write("\nGenerating Judgment Excel Report done. Success.\n")
    return 0        
    
# Driver code
if __name__ == "__main__":

    #run_app("/home/tst/work/2021_TPL/23L")
    #run_app("/home/yoel/vditech/tst/data/2019_TPL/21S")
    #run_app("z:/data/2019_TPL/21S")
    #run_app("z:\\data\\2019_TPL\\21S")
    #clean_csv("/home/yoel/vditech/tst/data/2019_TPL/21S")

    #build_master_report("/home/tst/work/2021_TPL")
    #build_master_report("z:/data/2019_TPL/21S")

    #build_judgement('/home/tst/work/2019_TPL', 'Judgement.xlsx')
    pass
