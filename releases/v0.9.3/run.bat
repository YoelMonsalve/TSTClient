:: This script will run the TST Client APP on your
:: system (Windows). Requires python3.
:: 
:: ============================================
:: This product is protected under U.S. Copyright Law.
:: Unauthorized reproduction is considered a criminal act.
:: (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
::
:: Date:     2021-12-11
:: Modified: 2021-12-11

@echo off
if exist winenv\ (
	SET py_=winenv\Scripts\python.exe
) else (
	@echo off
	echo Fatal error. A virtual environment has not been installed.
	echo Please first install the virtual environment ^(run setup.bat^)
	@pause
	EXIT /B 1
)

%py_% py\client.py
@pause
EXIT /B 0