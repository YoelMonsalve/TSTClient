#!/usr/bin/env python

"""
 *******************************************************************
 * SERVER_SYNC_PY
 * This script is to sync the local folder with the files
 * being generated in the remote host.
 *
 * =================================================================
 *
 * Freelancer: Yoel Monsalve | yymonsalve@gmail.com
 * Web:        www.yoelmonsalve.net  (under construction)
 * ------------------------------------------------------
 *
 * (C) 2019-2021 Yoel Monsalve. All rights reserved.
 *******************************************************************
"""

__author__   = "Yoel Monsalve"
__email__    = "yymonsalve@gmail.com"
__date__     = "July, 2021"
__modified__ = "2021/07/11"

import os
import sys
from sys import stdin, stdout, stderr, argv
from time import sleep
from datetime import datetime, timedelta
import json
import subprocess
import traceback 
import signal
import threading
import paramiko        # ssh, sftp
import stat            # stat.S_ISDIR, stat.S_ISREG
from getpass import getpass

from functions import getchar

ssh_client  = None
sftp_client = None

def create_file(remote_path, local_path, sftp_client):
    sftp_client.get(remote_path, local_path)

def update_file(remote_path, local_path, sftp_client):
    local_st  = os.stat(local_path)
    remote_st = sftp_client.stat(remote_path)

    #print("local:", datetime.fromtimestamp(local_st.st_mtime), local_st.st_size)
    #print("remote:", datetime.fromtimestamp(remote_st.st_mtime), remote_st.st_size)

    if (remote_st.st_size > local_st.st_size) or \
    (remote_st.st_mtime > local_st.st_mtime):
        print("... updating file: " + local_path)
        create_file(remote_path, local_path, sftp_client)

def init_conn():
    global ssh_client, sftp_client

    # opening a SSH connection, that will be later used to open a SFTP.
    client = paramiko.client
    ssh_client = client.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    host   = '54.38.79.195'
    #host   = 'localhost'
    user   = 'binance'

    # Quit this ..........................!!!
    #passwd = getpass()
    passwd = 'binance!'
    
    ssh_client.connect(hostname = host, username = user, password = passwd, compress = True)
    stdin, stdout, stderr = ssh_client.exec_command('cd binance')
    
    #stdin, stdout, stderr = ssh_client.exec_command('ls -l .')
    #print(stdout.read().decode())
    #print(stderr.read().decode())

    sftp_client = ssh_client.open_sftp()
    sftp_client.chdir('binance')        # changing to remote folder 'binance'

    return ssh_client, sftp_client

def close_conn():
    if not sftp_client is None:
        sftp_client.close()
    if not ssh_client is None:
        ssh_client.close()

def sync(date = datetime.utcnow()):
    global ssh_client, sftp_client

    if sftp_client is None:
        (ssh_client, sftp_client) = init_conn()
    
    DIR = 'data'
    remote_folders = sftp_client.listdir(DIR)
    for f in remote_folders:
        file_mode = sftp_client.stat(DIR + '/' + f).st_mode
        if stat.S_ISDIR(file_mode):
            folder  = DIR + '/' + f
            folder += "/{:02d}/{:02d}/{:d}".format(date.year, date.month, date.day)
            print(folder)

            # update folder in the local host
            inspect(folder)

    DIR = 'log'
    remote_folders = sftp_client.listdir(DIR)
    for f in remote_folders:
        file_mode = sftp_client.stat(DIR + '/' + f).st_mode
        if stat.S_ISDIR(file_mode):
            folder  = DIR + '/' + f
            folder += "/{:02d}/{:02d}/{:d}".format(date.year, date.month, date.day)
            print(folder)

            # update folder in the local host
            inspect(folder)

    return

def inspect(base_dir = ''):

    global ssh_client, sftp_client

    if not base_dir: return
    if sftp_client is None:
        (ssh_client, sftp_client) = init_conn()
    
    local_folder  = base_dir
    remote_folder = base_dir
    if not os.path.exists(local_folder) or not os.path.isdir(local_folder):
        os.makedirs(local_folder, exist_ok = True)

    local_files  = os.listdir(local_folder)
    try:
        remote_files = sftp_client.listdir(remote_folder)
    except Exception as e:
        # unable to inspect remote folder (possibly does not exist in the remote)
        sys.stderr.write("unable to inspect remote: '" + remote_folder + "'\n")
        sys.stderr.write(str(e) + '\n')
        return

    #remote_attr = sftp_client.listdir_attr(remote_folder)

    #print(local_files)
    #print("remote files:")
    #print(remote_files)
    print("Updating content to folder: " + local_folder)
    for file in remote_files:
        file_mode = sftp_client.stat(remote_folder + '/' + file).st_mode
        if stat.S_ISREG(file_mode):
            # is a regular file
            if file not in local_files:
                print("creating: " + local_folder + '/' + file)
                create_file(remote_folder + '/' + file, local_folder + '/' + file, sftp_client)
            else:
                update_file(remote_folder + '/' + file, local_folder + '/' + file, sftp_client)
            
            pass
        elif stat.S_ISDIR(file_mode):
            # is a directory, proceed recursively
            subdir = remote_folder + '/' + file
            inspect(subdir)
            pass

def main():

    date = input("Introduzca la fecha a sincronizar (aaaa/mm/dd) [o dejar en blanco para tomar la fecha actual]: ")
    if date:
        date = datetime.strptime(date, "%Y/%m/%d")
        sync(date)
    else:
        sync()

    init_conn()

    #inspect('log/1INCHUSDT/2021/07/13')
    #sync()
    close_conn()

if __name__ == "__main__":
    main()

