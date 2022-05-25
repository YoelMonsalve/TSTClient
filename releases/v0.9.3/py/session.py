#!/usr/bin/env python3
"""
 * SESSION_PY
 * This module is to define a client session.
 *
 * =================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "October, 2019"
__modified__  = "2021-11-05"
__version__   = "0.9.3"
__copyright__ = "VDI Technologies, LLC"

import helpers

class CLI_session():
    """
    This is an allowed session per a single user, over a host.
    """
    def __init__(self):
        self.host = ""
        self.user = ""

        self.logfile = helpers.create_logfile()
        self.logfile_name = self.logfile.name
        self.log("Session started")

    def log(self, msg=''):
        """
        log a new action for the current session
        
        :param      msg:  The message
        :type       msg:  str
        """
        helpers.log(self.logfile_name, msg)
