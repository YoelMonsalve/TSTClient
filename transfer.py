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

import os
import sys
from sys import stdin, stdout, stderr, argv
import subprocess
from time import sleep
import signal
import re         # regex
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


def transfer_files_posix(HOST = "", local_path = "", remote_path = "", verbose = False):
    
    if not HOST: return
    if not local_path: return
    if not remote_path: return
    
    # create a pipe to communicate the processes
    (r,w) = os.pipe()
    pid = os.fork()

    if pid == 0:
        # the child
        os.close(w)     # close the write-end
        
        #os.close(stdin_fileno)
        #os.dup(r)
        os.dup2(r, stdin_fileno)
        
        if verbose:
            # verbose option
            cpid = os.spawnlp(os.P_NOWAIT, "sftp", "sftp", "-v", "-i", ".ssh/id_rsa", 
            "tst@" + HOST)
            
        else:
            # non-verbose
            cpid = os.spawnlp(os.P_NOWAIT, "sftp", "sftp", "-i", ".ssh/id_rsa", 
            "tst@" + HOST)
        
        # close pipe, and exit
        os.close(r)
        exit(0)
        
    elif pid > 0:
        # the parent
        
        # define SIGPIPE handler
        signal.signal(signal.SIGPIPE, sigpipe_handler)
        
        os.close(r)     # close the read-end
        
        #os.dup2(w, stdout_fileno)
        #os.write(w, 'foooo\n'.encode('utf-8'))
        #stdout.write('foo\n')
        
        print("SFTP connection started, please wait ...")
        
        # see local path
        os.write(w, "!pwd\n".encode('utf-8'))
        
        # see remote path
        os.write(w, "pwd\n".encode('utf-8'))
        
        # changing local directory
        os.write(w, f"lcd {local_path}\n".encode('utf-8'))
        
        # changing remote directory
        os.write(w, f"cd {remote_path}\n".encode('utf-8'))
        
        # files to be transferred
        os.write(w, "!ls *.csv.gz\n".encode('utf-8'))
        
        # putting the files
        matcher = re.compile(r".*\.csv\.gz$")
        for f in os.listdir(local_path):
            if matcher.match(f):
                os.write(w, (f"put -a \"{f}\"\n").encode('utf-8'))
                #break
        
        # listing the remote content
        os.write(w, "ls\n".encode('utf-8'))
        # exiting from sftp
        os.write(w, "exit\n".encode('utf-8'))
        
        # close pipe, and exit
        os.close(w)

def transfer_files_win(HOST = "", local_path = "", remote_path = "", verbose = False):
    
    if not HOST: return
    if not local_path: return
    if not remote_path: return
    
    # define SIGPIPE handler (UNIX)
    if is_posix():
        signal.signal(signal.SIGPIPE, sigpipe_handler)

    # In Windows, we use the more suitable method subprocess, instead of the low-level
    # methods fork() + spawn()
    if verbose:
        p = subprocess.Popen(["sftp", "-v", "-i", ".ssh/id_rsa", 
            "tst@" + HOST]
            , stdin=subprocess.PIPE
            , creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
    else:
        p = subprocess.Popen(["sftp", "-i", ".ssh/id_rsa", 
            "tst@" + HOST]
            , stdin=subprocess.PIPE
            , creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
        
    if not p: return

    # The parent: send commands to child
    pipe = p.stdin

    # see local path
    pipe.write("!pwd\n".encode('utf-8'))
    
    # see remote path
    pipe.write("pwd\n".encode('utf-8'))
    
    # changing to local directory
    pipe.write(f"lcd \"{local_path}\"\n".encode('utf-8'))
    
    # changing to remote directory
    pipe.write(f"cd \"{remote_path}\"\n".encode('utf-8'))
    
    # files to be transferred
    pipe.write("!dir *.csv.gz\n".encode('utf-8'))
    
    # putting the files
    matcher = re.compile(r".*\.csv\.gz$")
    for f in os.listdir(local_path):
        if matcher.match(f):
            pipe.write((f"put \"{f}\"\n").encode('utf-8'))
            #break
            pass
    
    # listing the remote content
    s = "echo \"Content of remote folder {:s}:\"\n".format(remote_path)
    pipe.write("ls -l .\n".encode('utf-8'))
    
    # exiting from sftp
    pipe.write("exit\n".encode('utf-8'))
    
def download_files_win(HOST = "", remote_path = "", local_path = "", verbose = False):
    
    if not HOST: return
    if not local_path: return
    if not remote_path: return
    
    # define SIGPIPE handler (UNIX)
    if is_posix():
        signal.signal(signal.SIGPIPE, sigpipe_handler)

    # In Windows, we use the more suitable method subprocess, instead of the low-level
    # methods fork() + spawn()
    if verbose:
        p = subprocess.Popen(["sftp", "-v", "-i", ".ssh/id_rsa", 
            "tst@" + HOST]
            , stdin=subprocess.PIPE
            , creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
    else:
        p = subprocess.Popen(["sftp", "-i", ".ssh/id_rsa", 
            "tst@" + HOST]
            , stdin=subprocess.PIPE
            , creationflags=subprocess.CREATE_NEW_CONSOLE
            , close_fds=True
            )
        
    if not p: return

    # The parent: send commands to child
    pipe = p.stdin

    # creating local directories
    pipe.write(f"!mkdir \"{local_path}\"/output\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/output/report\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/output/summary\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/plots\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/plots/angle\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/plots/volt\n".encode('utf-8'))
    pipe.write(f"!mkdir \"{local_path}\"/plots/unstable\n".encode('utf-8'))
    
    # transfer to local path
    pipe.write(f"mget \"{remote_path}\"/output/report/* \"{local_path}\"/output/report\n".encode('utf-8'))
    pipe.write(f"mget \"{remote_path}\"/output/summary/* \"{local_path}\"/output/summary\n".encode('utf-8'))
    pipe.write(f"mget \"{remote_path}\"/plots/angle/* \"{local_path}\"/plots/angle\n".encode('utf-8'))
    pipe.write(f"mget \"{remote_path}\"/plots/volt/* \"{local_path}\"/plots/volt\n".encode('utf-8'))
    pipe.write(f"mget \"{remote_path}\"/plots/unstable/* \"{local_path}\"/plots/unstable\n".encode('utf-8'))

    # exiting from sftp
    pipe.write("exit\n".encode('utf-8'))
    
def transfer_files(HOST = "", local_path = "", remote_path = "", verbose = False):
    if is_win():
        transfer_files_win(HOST, local_path, remote_path, verbose)
    else:
        transfer_files_posix(HOST, local_path, remote_path, verbose)

def download_files(HOST = "", remote_path = "", local_path = "", verbose = False):
    if is_win():
        download_files_win(HOST, remote_path, local_path, verbose)
    else:
        #download_files_posix(HOST, remote_path, local_path, verbose)
        pass

def test():
    """Test code"""
    
    HOST = "54.38.79.195"
    #local_path = "../work/2021S_2/csv/.tmp/"
    local_path = "C:\\tst\\2019MDWG_DS33_RED_FINAL_22L\\OUTPUT"
    remote_path = "work/2020_TPL/22L/csv"
    transfer_files(HOST, local_path, remote_path)

    #local_wd = "..\\work\\2021S_2"
    #remote_wd = "work/2021S_2"
    #download_files(HOST, remote_wd, local_wd)
    exit(0)
    
if __name__ == "__main__":
    test()
    
