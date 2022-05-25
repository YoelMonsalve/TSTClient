# This script will install the environment and all the requirements
# to run the client into your PC. Requires python3.
#
# INSTRUCTIONS
#
# 1. Enable execution mode for the script: 
#
#    $ chmod u+x setup.sh
#
# 2. Run
#
#    $ ./setup.sh
#
# ============================================
# This product is protected under U.S. Copyright Law.
# Unauthorized reproduction is considered a criminal act.
# (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
#
# Date:     2021-12-11
# Modified: 2021-12-11

# install the virtual environment
cmd="python -m venv env"
echo $cmd     # prompt command to user
eval $cmd || {
	echo Fatal error in last command. Terminating.
   exit 1
}

# declare environmental python path
py_=env/bin/python3

# upgrade pip
cmd="$py_ -m pip install --upgrade pip"
echo $cmd     # prompt command to user
eval $cmd || {
	echo Fatal error in last command. Terminating.
	exit 1	
}

# install pipreqs
cmd="$py_ -m pip install pipreqs"
echo $cmd     # prompt command to user
eval $cmd || {
	echo Fatal error in last command. Terminating.
	exit 1	
}

# install requirements
cmd="$py_ -m pip install -r requirements.txt"
echo $cmd     # prompt command to user
eval $cmd || {
	echo Fatal error in last command. Terminating.
	exit 1	
}

# prompt user to finish
echo 
echo "TST Client installed successfully (v0.9.2)"
echo "Proudly by VDITechnologies, LLC. Visit us at www.vditech.us"

exit 0    # success