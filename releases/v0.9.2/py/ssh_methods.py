#!/usr/bin/env python3
"""
 * SSH_METHODS
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
__version__   = "0.9.2"
__copyright__ = "VDI Technologies, LLC"


import os
import sys
from sys import stdin, stdout, stderr, argv
import subprocess
from time import sleep
import signal
import re         # regex
import shlex      # quote
from helpers import is_win, is_posix

import paramiko
import stat
from getpass import getpass

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
    ...

decompress_files:
    Decompress gzip'ed files in the remote data folder

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

create_ssh_process:
    Creates a ssh process.

init_connection:
    Starts a new SSH connection.
    
disconnect:
    Close the current SSH connection.

run_ssh_command:
    Run a SSH command and print the output
"""

# File-scope (global) variables
stdin_fileno  = stdin.fileno()
stdout_fileno = stdout.fileno()
stderr_fileno = stderr.fileno()

ssh_process = None

def sigpipe_handler(signum, frame):
    """Custom handler to SIGPIPE: ignore
    This happens when the child ends and closes the pipe, and
    the signal is delivered to the parent
    """
    print(f"[{os.getpid()}] W: Received SIGPIPE. Event ignored.")

def rename_folder(ssh_client, old_path, new_path):
    """
    Rename an existing directory or file
    
    :param      ssh_client:  The ssh client
    :type       ssh_client:  paramiko.client.SSHCLient
    :param      old_path:    The current path to the folder (e.g. old/name/to/folder)
    :type       old_path:    str
    :param      new_path:    The new name/path to the folder (e.g. new/name/to/folder)
    :type       new_path:    str
    """

    if not ssh_client:
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: missing argument 'ssh_client'\n")
        return
    if not old_path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'old_path'\n")
        return
    if not new_path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'new_path'\n")
        return

    # check that the old directory exists, and the new_directory does NOT exist
    sftp = ssh_client.open_sftp()
    try:
        sftp.stat('work/' + old_path)
    except FileNotFoundError:
        print(f"Folder '{old_path}' does not exist in the working directory")
        folders = sftp.listdir('work')
        folders.sort()
        print("Note: folders in the working directory are:")
        if len(folders) > 0:
            for f in folders:
                if f != 'env':
                    print("  " + f)
        else:
            print("  <empty>")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: {str(e)}\n")
        return

    try:
        sftp.stat('work/' + new_path)
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
    cmd  = f"mv work/\"{old_path}\" work/\"{new_path}\""
    cmd += f" && echo \"... successfully changed '{old_path}' to '{new_path}'\""

    run_ssh_command(ssh_client, cmd)

    return

def remove_folder(ssh_client, path):
    """
    Remove an existing directory or file
    
    :param      ssh_client:  The ssh client
    :type       ssh_client:  paramiko.client.SSHCLient
    :param      path:        The path to the folder (e.g. path/to/folder)
    :type       path:        str
    """

    if not ssh_client:
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: missing argument 'ssh_client'\n")
        return
    if not path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'old_path'\n")
        return

    # check that the old directory exists, and the new_directory does NOT exist
    sftp = ssh_client.open_sftp()
    try:
        sftp.stat('work/' + path)
    except FileNotFoundError:
        print(f"Folder '{path}' does not exist in the working directory")
        folders = sftp.listdir('work')
        folders.sort()
        print("Note: folders in the working directory are:")
        if len(folders) > 0:
            for f in folders:
                if f != 'env':
                    print("  " + f)
        else:
            print("  <empty>")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: remove_folder: {str(e)}\n")
        return
    
    # Ask user to confirm before to proceed
    ans = input(f"Are you sure to completely remove the folder '{path}'? [y/n]: ")
    if not ans.lower() == 'y':
        return
    
    # Build a LINUX command to execute the sentences
    cmd  = f"rm -r work/\"{path}\""
    cmd += f" && echo \"... successfully deleted folder '{path}'\""

    run_ssh_command(ssh_client, cmd)

    return

def clean_csv(ssh_client, path):
    """
    Clean the content of the folder 'csv' into the given path.
    This utility can be used to clean the CSV files for a case-study.
    
    :param      ssh_client:  The ssh client
    :type       ssh_client:  paramiko.client.SSHCLient
    :param      path:        The path to the folder (e.g. path/to/folder)
    :type       path:        str
    """

    if not ssh_client:
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: missing argument 'ssh_client'\n")
        return
    if not path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: rename_folder: invalid argument 'old_path'\n")
        return

    # check that the directory exists
    sftp = ssh_client.open_sftp()
    try:
        sftp.stat('work/' + path + '/csv')
    except FileNotFoundError:
        print(f"Folder '{path}/csv' does not exist in the working directory")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: clean_csv: {str(e)}\n")
        return

    # Ask user to confirm before to proceed
    ans = input(f"Are you sure to completely remove the content of '{path}/csv'? [y/n]: ")
    if not ans.lower() == 'y':
        return
    
    # Build a LINUX command to execute the sentences
    cmd  = f"rm work/\"{path}\"/csv/*"
    cmd += f" && echo \"... files into '{path}/csv' were successfully deleted\""

    run_ssh_command(ssh_client, cmd)

    return

def decompress_files(ssh, path = "", session = None):
    """
    Decompress gzip'ed files in the remote data folder
    
    :param      ssh:        The ssh object
    :type       ssh:        paramiko.client.SSHCLient
    :param      path:       The path to the data files (e.g. XXXX_TPL/csv/.tmp)
    :type       path:       str
    :param      session:    optional, a session over what to log the operations
    :type       session:    object, CLI_session
    """

    if not ssh:
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: required argument 'ssh' (client)\n")
        return
    if not path: 
        return
    
    # set permissions
    cmd  = 'echo ..setting permissions; '
    cmd += f'chmod 640 "work/{path}"/*.csv.gz 2> /dev/null'
    cmd += f' && echo "  done";'
    #print(cmd)        # debug
    if session:
        session.log(f"setting permissions to {path} in remote")
    run_ssh_command(ssh, cmd)
    
    # prompt
    cmd  = 'echo ..decompressing in progress, please wait ...;'
    run_ssh_command(ssh, cmd)
    
    # run script
    cmd = f'source ~/.scripts/decompress work/{path}'
    #print(cmd)        # debug
    if session:
        session.log(f"decompressing files in remote")
    run_ssh_command(ssh, cmd)
    
    # list content
    cmd = f'echo; echo Content of {path}: && ls -l "work/{path}"'
    #print(cmd)        # debug
    if session:
        session.log(f"decompressing successful")
    run_ssh_command(ssh, cmd)

    # close & exit
    return

def inspect_wd(ssh_client, path = "", show_files = False):
    """
    Prints a 'tree' of the referred path.
    It is useful to get a view of a remote directory
    """

    if not ssh_client:
        stderr.write(f"Exception: {os.path.basename(__file__)}: inspect_wd: missing argument 'ssh_client'\n")
        return

    if not path: 
        stderr.write(f"Exception: {os.path.basename(__file__)}: inspect_wd: missing argument 'path'\n")
        return

    # check if the directory exists, and preemtively return if not
    sftp = ssh_client.open_sftp()
    try:
        sftp.stat('work/' + path)
    except FileNotFoundError:
        print(f"Folder '{path}' does not exist into the working directory")
        folders = sftp.listdir('work')
        folders.sort()
        print("Note: folders in the working directory are:")
        empty = True
        for f in folders:
            if f != 'env':
                r_st = sftp.lstat('work/' + f)
                if stat.S_ISDIR(r_st.st_mode):
                    print("  " + f)
                    empty = False
        if empty:
            print("  <empty>")
        return
    except Exception as e:
        # unknown error
        stderr.write(f"Exception: {os.path.basename(__file__)}: clean_csv: {str(e)}\n")
        return

    """ ***)NOTE: paramiko SSHClient DOES NOT execute .profile, .bash_login or .bash_profile
    as a normal connection does, so that we have to manually change to the root directory 'work'
    """
    if show_files:
        cmd = "cd work && tree {:s}".format(path)
    else:
        cmd = "cd work && tree -d {:s}".format(path)

    run_ssh_command(ssh_client, cmd)

    return

def create_directory(ssh_client, new_path = "", mode = 0o770,
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

    if not ssh_client:
        stderr.write(f"Exception: {os.path.basename(__file__)}: create_directory: missing argument 'ssh_client'\n")
        return
    
    # First, to check that the folder actually does not exist
    try:
        sftp = ssh_client.open_sftp()
        file_mode = sftp.stat(new_path)
        print(f"The path '{new_path}' already exists. Try deleting it first.")
        sftp.close()
        return
    except:
        pass
    
    """ ***)NOTE: paramiko SSHClient DOES NOT execute .profile, .bash_login or .bash_profile
    as a normal connection does, so that we have to manually change to working directory work
    """
    #new_path = 'work/' + new_path

    # creating remote directory
    cmd = f"mkdir -p \"{new_path}\" && echo created '{new_path}' ... success.\n".encode('utf-8')
    run_ssh_command(ssh_client, cmd)
    
    # setting mode/perms
    cmd = "chmod {:o} \"{:s}\" && echo mode changed to {:o} ... success.\n".format(
        mode, new_path, mode)
    run_ssh_command(ssh_client, cmd)

    if create_structure:
        # creating directory structure
        cmd  = "echo \"Creating directory structure ...\"; "
        run_ssh_command(ssh_client, cmd)
        # --> /csv
        cmd  = "echo -n \"--> creating {:s}/csv ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/csv\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/csv\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /log
        cmd  = "echo -n \"--> creating {:s}/log ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/log\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/log\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> output
        cmd  = "echo -n \"--> creating {:s}/output/ ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/output\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/output\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /output/report
        cmd  = "echo -n \"--> creating {:s}/output/report ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/output/report\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/output/report\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /output/summary
        cmd  = "echo -n \"--> creating {:s}/output/summary ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/output/summary\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/output/summary\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)

        # --> plots
        cmd  = "echo -n \"--> creating {:s}/plots/ ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/plots\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/plots\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /plots/angle
        cmd = "echo -n \"--> creating {:s}/plots/angle ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/plots/angle\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/plots/angle\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /plots/volt
        cmd = "echo -n \"--> creating {:s}/plots/volt ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/plots/volt\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/plots/volt\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)
        # --> /plots/unstable
        cmd = "echo -n \"--> creating {:s}/plots/unstable ... \"; ".format(new_path)
        cmd += "mkdir -p \"{:s}/plots/unstable\"; ".format(new_path)
        cmd += "chmod 750 \"{:s}/plots/unstable\"; ".format(new_path)
        cmd += "(test $? -eq 0 && echo && echo \"    success\");"
        run_ssh_command(ssh_client, cmd)

        print()
        cmd = "echo \"Directory structure is:\"; "
        cmd += "tree -d {:s}".format(new_path)
        run_ssh_command(ssh_client, cmd)

    # close & exit
    print("Creating directory done.\n")
    return

def run_app(host, working_dir = "", verbose = False):
    """
    Run completely the app in the server side
    
    :param      host:         The host
    :type       host:         str
    :param      working_dir:  The folder/case over what to run the app (e.g. 2019_TPL/21S)
    :type       working_dir:  str
    :param      verbose:      Passes the option "-v" to the underlying ssh process
    :type       verbose:      bool
    """

    if not host: return
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
                "tst@" + host], 
                stdin=subprocess.PIPE
                #, stdout=sys.stdout, stderr=subprocess.STDOUT
                , creationflags = subprocess.CREATE_NEW_CONSOLE
                , close_fds=True
                )
        else:
            p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
                "tst@" + host], 
                stdin=subprocess.PIPE
                , stdout=sys.stdout, stderr=subprocess.STDOUT
                , close_fds=True
                )
    else:
        if is_win():
            cmd = "ssh -i .ssh/id_rsa tst@" + host
            cmd = "cmd /C " + "\"" + cmd + "\""
            p = subprocess.Popen(cmd
                , stdin=subprocess.PIPE
                #, stdout=sys.stdout, stderr=subprocess.STDOUT
                , creationflags=subprocess.CREATE_NEW_CONSOLE
                , close_fds=True
                )
        else:
            p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
                "tst@" + host], 
                stdin=subprocess.PIPE
                , stdout=sys.stdout, stderr=subprocess.STDOUT
                , close_fds=True
                )
    
    if not p: return

    pipe = p.stdin
    #s = ". ./run {:s} \n".format(working_dir)
    s = ". ~/.scripts/run {:s} \n".format(working_dir)
    pipe.write(s.encode('utf-8'))
    
    # close & exit
    if is_win():
        pipe.write("echo -e -n \"\\nTask done. Close this windows to terminate ...\"\n".encode('utf-8'))
        #pipe.write("while true; do sleep 30; done\n".encode('utf-8'))
    else:
        #pipe.close()
        pass

    return

def create_ssh_process(host = '', user = '', verbose = False):
    """
    Creates a ssh process.
    
    :param      host:     The host
    :type       host:     str
    :param      user:     The user
    :type       user:     str
    :param      verbose:  Passes the option "-v" to the ssh underlying process
    :type       verbose:  bool
    """
    if not host or not user:
        return

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
                "tst@" + host], 
                stdin=subprocess.PIPE
                , stdout=sys.stdout, stderr=subprocess.STDOUT
                , creationflags = subprocess.CREATE_NEW_CONSOLE
                , close_fds=True
                )
        else:
            p = subprocess.Popen(["ssh", "-v", "-i", ".ssh/id_rsa", 
                "tst@" + host], 
                stdin=subprocess.PIPE
                #, stdout=sys.stdout, stderr=subprocess.STDOUT
                , close_fds=True
                )
    else:
        if is_win():
            cmd = "ssh -i .ssh/id_rsa tst@" + host
            cmd = "cmd /C " + "\"" + cmd + "\""
            p = subprocess.Popen(cmd
                , stdin=subprocess.PIPE
                #, stdout=sys.stdout, stderr=subprocess.STDOUT
                , creationflags=subprocess.CREATE_NEW_CONSOLE
                , close_fds=True
                )
        else:
            p = subprocess.Popen(["ssh", "-i", ".ssh/id_rsa", 
                "tst@" + host], 
                stdin=subprocess.PIPE
                #, stdout=sys.stdout, stderr=subprocess.STDOUT
                , close_fds=True
                )
    
    if not p: return
    pipe = p.stdin

    cmd = "ls . \n"
    pipe.write(cmd.encode('utf-8'))
    print("wait 1 sec")
    sleep(1.0)
    pipe.close()

    return p

def init_connection(host = '', user = '', passwd = ''):
    """
    Starts a new SSH connection.
    
    :param      host:     The host
    :type       host:     str
    :param      user:     The user
    :type       user:     str
    :param      passwd:   The password
    :type       passwd:   str
    """

    global ssh_process

    if not host or not user:
        stderr.write(f"Exception: {os.path.basename(__file__)}: init_connection: missing arguments (host/user)\n")
        return (None, None)

    # opening a SSH connection, that will be later used to open a SFTP.
    client = paramiko.client
    ssh_client = client.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Quit this ..........................!!!
    if not passwd:
        passwd = getpass()

    try:
        print("Establishing a connection with host .... wait")
        ssh_client.connect(hostname = host, username = user, password = passwd, 
            timeout = 30, compress = True)

        #ssh_process = create_ssh_process(host, user, True)

        print("SSH connection started")
    except Exception as e:
        print("SSH connection failed. Unable to continue.")
        stderr.write(str(e) + '\n')
        return (None, None)

    # === test ===
    """stdin, stdout, stderr = ssh_client.exec_command('ls -l .')
    print(stdout.read().decode())
    print(stderr.read().decode())
    """
    
    try:
        sftp_client = ssh_client.open_sftp()
        print("SFTP client started")
    except Exception as e:
        print("STFP failed. Unable to continue.")
        stderr.write(str(e) + '\n')
        return (None, None)
    print("......................................\n")

    return (ssh_client, sftp_client)

def disconnect():
    """
    Closes the current SSH connection.
    """
    if not sftp_client is None:
        sftp_client.close()
    if not ssh_client is None:
        ssh_client.close()
    
def run_ssh_command(ssh_client, cmd = ''):
    """
    Run a SSH command and print the output
    
    :param      ssh_client:  The ssh client
    :type       ssh_client:  paramiko.client.SSHClient
    :param      cmd:         The command to be run
    :type       cmd:         str
    """
    if not cmd: return

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)
    print(ssh_stdout.read().decode())
    print(ssh_stderr.read().decode())

def test():
    """Test code"""

    # .................................. Warning: quit this later
    #host   = '54.38.79.195'
    host   = 'localhost'
    user   = 'tst'
    passwd = 'tst**'

    (ssh_client, sftp_client) = init_connection(host, user, passwd)
    if not ssh_client or not sftp_client:
        return

    session = CLI_session()

    #inspect_wd(ssh_client, '2019_TPL', True)
    #create_directory(ssh_client, 'work/2022_TPL/21S', create_structure=True)
    #decompress_files(ssh_client, '2019_TPL/21S/csv', session)
    #run_app(ssh_client, '2019_TPL/21S')
    #run_app(host, '2019_TPL/21S', False)
    #
    #rename_folder(ssh_client, 'f1', 'f2')
    #remove_folder(ssh_client, 'f1a')
    clean_csv(ssh_client, '2022/C')
    
    return 
    
if __name__ == "__main__":
    test()
    
