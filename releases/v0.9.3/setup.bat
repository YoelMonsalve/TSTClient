:: This script will install the environment and all the requirements
:: to run the client into your PC. Requires python3.
:: 
:: ============================================
:: This product is protected under U.S. Copyright Law.
:: Unauthorized reproduction is considered a criminal act.
:: (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 
::
:: Date:     2021-12-11
:: Modified: 2021-12-11

:: install the virtual environment
@echo on
py -m venv winenv
@echo off
if %ERRORLEVEL% NEQ 0 (
	echo Fatal error in last command. Terminating.
	@pause
	EXIT /B 1
)
@echo on

:: declare environmental python path
SET py_=winenv\Scripts\python.exe

:: upgrade pip
%py_% -m pip install --upgrade pip
@echo off
if %ERRORLEVEL% NEQ 0 (
	echo Fatal error in last command. Terminating.
	@pause
	EXIT /B 1
)
@echo on

:: install pipreqs
%py_% -m pip install pipreqs
@echo off
if %ERRORLEVEL% NEQ 0 (
	echo Fatal error in last command. Terminating.
	@pause
	EXIT /B 1
)
@echo on

:: install requirements
%py_% -m pip install -r requirements.txt
@echo off
if %ERRORLEVEL% NEQ 0 (
	echo Fatal error in last command. Terminating.
	@pause
	EXIT /B 1
)
@echo on

:: prompt user to finish
@echo off
echo.
echo TST Client installed successfully (v0.9.2)
echo Proudly by VDITechnologies, LLC. Visit us at www.vditech.us
echo.
@pause
EXIT /B 0
