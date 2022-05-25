:: This script will install the environment and all the requirements
:: to run the client into your PC. Requires python3.
:: 
:: ============================================
:: This product is protected under U.S. Copyright Law.
:: Unauthorized reproduction is considered a criminal act.
:: (C) 2018-2021 VDI Technologies, LLC. All rights reserved. 

:: install the virtual environment
@echo on
py -m venv winenv
:: declare python path
SET py_=winenv\Scripts\python.exe
@echo off
if %ERRORLEVEL% NEQ 0 (
	echo Fatal error in last command. Terminating.
	@pause
	EXIT /B 1
)
@echo on

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

:: prompt user to continue
@echo off
echo.
echo TST Client installed successfully (v0.9.2)
echo Proudly by VDITechnologies, LLC. Visit us in www.vditech.us
echo.
@pause
EXIT /B 0
