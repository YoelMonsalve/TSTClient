# This script will run the TST Client APP on your
# system (Linux). Requires python3.
#
# INSTRUCTIONS
#
# 1. Enable execution mode for the script: 
#
#    $ chmod u+x run.sh
#
# 2. Run
#
#    $ ./run.sh
#
# ============================================
# This product is protected under U.S. Copyright Law.
# Unauthorized reproduction is considered a criminal act.
# (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
#
# Date:     2021-12-11
# Modified: 2021-12-11

# check for the environment
if [ ! -d env ]
then
	echo "Fatal error. A virtual environment has not been installed."
	echo "Please first install the virtual environment (run setup.sh)"
	exit 1
fi

# declare environmental python path
py_=env/bin/python3

$py_ py/client.py
sleep 1
exit 0