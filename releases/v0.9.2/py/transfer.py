#!/usr/bin/env python3
"""
 * TRANSFER_PY
 * Utility to upload the content of the gzip-ed files
 * into the folder csv/.tmp to the remote host.
 * Also, to download the results from the remote to the
 * local folder.
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "July, 2021"
__modified__  = "2021-11-11"
__version__   = "0.9.2"
__copyright__ = "VDI Technologies, LLC"


""" ___LEGACY CODE___
        p = subprocess.Popen(["sftp", "-v", "-i", ".ssh/id_rsa", 
            "tst@" + HOST]
            , stdin=subprocess.PIPE
            , creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
"""

import os
import sys
from sys import stdin, stdout, stderr, argv
import subprocess
from time import sleep
import signal
import re         # regex
import stat       # to parse stat structure, e.g. S_ISREG, S_ISDIR, etc
from pprint import pprint
from datetime import datetime, timedelta

# helpers
from helpers import is_win, is_posix, timestamp, getchar
from helpers import _create_dir

# session
from session import CLI_session

# SSH objects
from ssh_methods import init_connection, disconnect

stdin_fileno  = stdin.fileno()
stdout_fileno = stdout.fileno()
stderr_fileno = stderr.fileno()

def sigpipe_handler(signum, frame):
    """Custom handler to SIGPIPE: ignore
    This happens when the child ends and closes the pipe, and
    the signal is delivered to the parent
    """
    print(f"[{os.getpid()}] W: Received SIGPIPE. Event ignored.")

def upload_files(ssh, local_path = "", remote_path = "", session = None):
    """
    Transfer files between local and remote (upload).
    
    :param      ssh:          The SSHclient
    :type       ssh:          paramiko.client.SSHClient()
    :param      local_path:   The local path
    :type       local_path:   str
    :param      remote_path:  The remote path
    :type       remote_path:  str
    :param      session:      optional, a session over what to log the operations
    :type       session:      object, CLI_session
    """
    
    if not ssh:
        stderr.write(f"{os.path.basename(__file__)}: upload_files: required argument 'ssh' (client)\n")
        return
    if not local_path: 
        stderr.write(f"{os.path.basename(__file__)}: upload_files: required argument 'local_path'\n")
        return
    if not remote_path: 
        stderr.write(f"{os.path.basename(__file__)}: upload_files: required argument 'remote_path'\n")
        return
    
    sftp = ssh.open_sftp()
    if not sftp:
        stderr.write(f"{os.path.basename(__file__)}: upload_files: unable to start a SFTP connection\n")
        return    

    # see local path
    print(f"local directory: {os.getcwd()}")
    
    # changing remote directory
    print(f"  changing to remote directory '{remote_path}'")
    remote_path = remote_path
    sftp.chdir('work/' + remote_path)
    print(f"remote directory: {sftp.getcwd()}\n")
    
    # changing local directory
    cwd = os.getcwd()
    # (to avoid confusions) delete trailing '/'
    if local_path[-1] == '/': local_path = local_path[:-1]
    if remote_path[-1] == '/': remote_path = remote_path[:-1]
    try:
        # calculating total of files to be transferred
        local_files = os.listdir(local_path)
        local_files.sort()
        matcher = re.compile(r".*\.csv\.gz$")
        total = 0
        for f in local_files:
            if matcher.match(f):
                total += 1
        
        # putting the files
        count = 1
        for f in local_files:
            if matcher.match(f):
                # .................................. quit later !
                #if count > 11: break

                # prompting
                stdout.write(f"[{count}/{total}] checking {f}")

                # check if the file actually exists. If yes, look for sizes.
                # If not, then transfer.
                try:
                    remote_st = sftp.stat(f)

                    local_st = os.stat(local_path + '/' + f)
                    if remote_st.st_size < local_st.st_size:
                        print(f"\n{timestamp()}\n    >> remote and local sizes differ, updating {f}")
                        sftp.put(local_path + '/' + f, f, callback = None, confirm = True)    

                        if session:
                            session.log(f"uploading (put) file `{local_path}/{f}` [sizes differ]")
                    else:
                        #print(f"{timestamp()} {f} is correct.")
                        print(" ... OK")
                except:
                    # does not exist (or unable to stat, e.g. permissions)
                    print(f"\n{timestamp()}\n    >> does not exist in remote, uploading {f}")
                    sftp.put(local_path + '/' + f, f, callback = None, confirm = True)

                    if session:
                        session.log(f"uploading (put) file `{local_path}/{f}` [not in remote]")
                
                count += 1
        
        # listing the remote content
        print("\nRemote content after transferring")
        print(f"{'size':<10s}{'modified':<24s}{'name'}")
        print("======================================================================")
        remote_files = sftp.listdir('.')
        remote_files.sort()
        for f in remote_files:
            r_st = sftp.stat(f)
            print(f"{r_st.st_size:<10d}{datetime.fromtimestamp(r_st.st_mtime).__str__():<24s}{remote_path}/{f}")

            # delete in local, if it already exists in remote
            # .......................................................
            if os.path.exists(local_path + '/' + f):
                l_st = os.stat(local_path + '/' + f)
                if r_st.st_size == l_st.st_size:
                    os.remove(local_path + '/' + f)

                    if session:
                        session.log(f"deleting file `{local_path}/{f}` [already in remote]")
        
    except Exception as e:
        stderr.write(f"Exception: {os.path.basename(__file__)}: transfer_files: {str(e)}\n")
    
def download_files(ssh, remote_path = "", local_path = ""):
    """
    Replicate the structure for a remote working directory into the local host,
    and populate it with the respective files.
    
    :param      ssh:          The SSHclient
    :type       ssh:          paramiko.client.SSHClient()
    :param      remote_path:  The remote directory to replicate
    :type       remote_path:  str
    :param      local_path:   The local path into what to copy the structure
    :type       local_path:   str
    """
    
    if not ssh:
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: required argument 'ssh' (client)\n")
        return
    if not local_path: 
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: required argument 'local_path'\n")
        return
    if not remote_path: 
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: required argument 'remote_path'\n")
        return
    
    # open a SFTP channel, from the SSH session provided
    sftp = ssh.open_sftp()
    if not sftp:
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: unable to start a SFTP connection\n")
        return    
 
    # Creating the local structure
    # ..............................................
    """
    `-- log
    `-- output
        `-- report
        `-- summary
    `-- plots
        `-- angle
        `-- volt
        `-- unstable
    """

    if not _create_dir(f"{local_path}/log", 0o755):
        return
    if not _create_dir(f"{local_path}/output", 0o755):
        return
    if not _create_dir(f"{local_path}/output/report", 0o755):
        return
    if not _create_dir(f"{local_path}/output/summary", 0o755):
        return
    if not _create_dir(f"{local_path}/plots", 0o755):
        return
    if not _create_dir(f"{local_path}/plots/angle", 0o755):
        return
    if not _create_dir(f"{local_path}/plots/volt", 0o755):
        return
    if not _create_dir(f"{local_path}/plots/unstable", 0o755):
        return
    
    # Transfering to the local path
    # ..............................................
    _mirror_dir(sftp, f"{remote_path}/log", f"{local_path}/log")
    sftp.get(remote_path + '/Failure-Report.csv', local_path + '/Failure-Report.csv')
    _mirror_dir(sftp, f"{remote_path}/output", f"{local_path}/output")
    _mirror_dir(sftp, f"{remote_path}/plots", f"{local_path}/plots")

    # Master Report
    stdout.write("Downloading Master Report")
    try:
        sftp.stat(remote_path + '/../Master-Report.xlsx')
        sftp.get(remote_path + '/../Master-Report.xlsx', local_path + '/../Master-Report.xlsx')
        print(" ... done")
    except:
        print(" ... ? not found")

    # exiting from sftp
    sftp.close()

# Auxiliary function    
def _mirror_dir(sftp, remote_path, local_path):
    """
    Replicate (mirror) a remote directory into a local path.
    Check each file into the remote path, and (if it also exists) in the local path.
    It only tranfers if the size in local is less than the size in remote, or if does not
    exist in local.
    It also descends recursively into subdirectories.
    
    :param      ssh:          The SFFTPclient
    :type       ssh:          paramiko.sftp_client.SFTPClient()
    :param      remote_path:  The remote directory to replicate
    :type       remote_path:  str
    :param      local_path:   The local path that will be the copy of the remote
    :type       local_path:   str
    """

    # verifying arguments
    if not sftp:
        stderr.write(f"{os.path.basename(__file__)}: transfer_files: unable to start a SFTP connection\n")
        return False
    if not remote_path or not local_path:
        return False
    
    # verifying that both paths are directories
    if not os.path.isdir(local_path):
        stderr.write(f"{os.path.basename(__file__)}: _mirror_dir: local path '{local_path}' is not a directory\n")
        return False
    try:
        r_st = sftp.stat(remote_path).st_mode
        if not stat.S_ISDIR(r_st):
            stderr.write(f"{os.path.basename(__file__)}: _mirror_dir: remote path '{remote_path}' is not a directory\n")
            return False
    except FileNotFoundError:
        stderr.write(f"{os.path.basename(__file__)}: _mirror_dir: remote path '{remote_path}' does not exist\n")
        return False
    except Exception as e:
        stderr.write(f"{os.path.basename(__file__)}: _mirror_dir: unable to stat remote path '{remote_path}'\n")
        stderr.write(f"{str(e)}\n")
        return False

    n_success = 0
    n_failed  = 0
    failed = []

    # calculate the number of files to be transferred
    remote_files = sftp.listdir(remote_path)
    n_files = 0
    for f in remote_files:
        r_st = sftp.stat(remote_path + '/' + f)               # stat to remote file
        if stat.S_ISREG(r_st.st_mode): 
            n_files += 1

    # now, fetch the files and descend recursively into subdirectories
    count = 0
    for f in remote_files:
        r_st = sftp.stat(remote_path + '/' + f)               # stat to remote file
        if stat.S_ISREG(r_st.st_mode):
            count += 1
            print(f"[Overvall progress to folder {remote_path}] .......... [{count:4d}/{n_files}] .......... ({100.0*count/n_files if n_files>0 else 0 :6.2f}%)")
            try:
                # file exists in local: check sizes
                l_st = os.stat(local_path + '/' + f)                  # stat to local file
                if l_st.st_size < r_st.st_size:
                    print(f"{timestamp()}  fetch {remote_path}/{f} into {local_path}/{f}")
                    sftp.get(remote_path + '/' + f, local_path + '/' + f)
                else:
                    print(f"  {local_path}/{f} is OK")

            except FileNotFoundError:
                # file does not exist: get it
                print(f"{timestamp()}  fetch {remote_path}/{f} into {local_path}/{f}")
                sftp.get(remote_path + '/' + f, local_path + '/' + f)
            
            except Exception as e:
                # unexpected error trying to stat
                stderr.write(f"{os.path.basename(__file__)}: _mirror_dir: unable to stat local path '{local_path}'\n")
                stderr.write(f"{str(e)}\n")
                continue

            # check files after transferring
            stdout.flush()
            stderr.flush()
            transfer_callback(os.stat(local_path + '/' + f).st_size, r_st.st_size)
            if os.stat(local_path + '/' + f).st_size == r_st.st_size:
                n_success += 1
            else:
                n_failed += 1
                failed.append(local_path + '/' + f)

        elif stat.S_ISDIR(r_st.st_mode):
            print(f"  descending into {remote_path + '/' + f}")
            _mirror_dir(sftp, remote_path + '/' + f, local_path + '/' + f)

    n_total = n_success + n_failed
    if n_total > 0:
        print(f"\nChecking directory '{local_path}\n------------------------------------------------")
        print(f"  {n_success:4d} files succeeded [{1.0*n_success/n_total*100 :5.1f}%]")
        print(f"  {n_failed:4d} files failed    [{1.0*n_failed/n_total*100 :5.1f}%]")
        print(f"  Total: {n_success + n_failed}\n")

def transfer_callback(n, m):
    msg = f"  transferred: {n}/{m} bytes  [{1.0*n/m * 100 if m else 0:.2f}%]"
    if n >= m:
        msg += " .. OK"
    else:
        msg += "    incomplete!"
    print(msg)

# Auxiliary function
def _remote_file_exists(sftp, path):
    """
    Determines if a remote file exists.
    
    :param      ssh:   The SFTP client
    :type       ssh:   paramiko.sftp_client.SFTPClient()
    :param      path:  The path to the file, in the remote host
    :type       path:  str
    :return     True is the file exists, False if not.
                None, if the SFTP transaction failed due to an error.
    :type       bool
    """
    if not path: return
    try:
        st = sftp.stat(path)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        stderr.write(f"{os.path.basename(__file__)}: _remote_file_exists: {str(e)}\n")
        return None

def test():
    """Test code"""
    
    host = "54.38.79.195"
    #host = "localhost"
    user = 'tst'
    passwd = 'tst**'
    #local_path = "..."
    #remote_path = "..."
    
    (ssh_client, sftp_client) = init_connection(host, user, passwd)

    session = CLI_session()

    #upload_files(ssh_client, local_path, remote_path, session)
    download_files(ssh_client, 'work/' + 'sample_data/folder_001a', 
        '../../../data/sample_data/folder_001a')
    
    exit(0)
    
if __name__ == "__main__":
    test()
    
