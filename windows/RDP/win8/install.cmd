@ECHO OFF

SETLOCAL ENABLEDELAYEDEXPANSION

SET WINVER=Windows 8 Build 9200
SET PRODUCTNAME="Windows 8"
SET CURRENTBUILD="9200"

TITLE Concurrent Remote Desktop Sessions For %WINVER%

:SHOWHELP
	IF /I *%1 == *-? GOTO PRINTHELP
	IF /I *%1 == *help GOTO PRINTHELP
	GOTO PERMISSIONCHK

:PRINTHELP

	ECHO This script enables concurrent remote desktop sessions
	ECHO for %WINVER%
	ECHO.
	ECHO This script must be run as an Administrator.
	ECHO To open an elevated command prompt with Administrator privileges
	ECHO press WinKey, typ cmd, and hit Ctrl+Shift+Enter.
	ECHO.
	ECHO.
	ECHO Available commandline switches:
	ECHO.
	ECHO -?       Show this help.
	ECHO help     Same as -?.
	ECHO blank    Enable remote logon for user accounts that are not password protected (not recomended).
	ECHO.
	GOTO END

:PERMISSIONCHK

echo OFF
cls
NET SESSION >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo #####################################
    echo ADMINISTRATOR PRIVILEGES DETECTED!!!!
    echo ##################################### 
) ELSE (
   echo ------------------------------------------------
   echo ######## ########  ########   #######  ########  
   echo ##       ##     ## ##     ## ##     ## ##     ## 
   echo ##       ##     ## ##     ## ##     ## ##     ## 
   echo ######   ########  ########  ##     ## ########  
   echo ##       ##   ##   ##   ##   ##     ## ##   ##   
   echo ##       ##    ##  ##    ##  ##     ## ##    ##  
   echo ######## ##     ## ##     ##  #######  ##     ##
   echo -------------------------------------------------
   echo.
   echo.
   echo ####### ERROR: ADMINISTRATOR PRIVILEGES REQUIRED ###############
   echo This script must be run as administrator to work properly!  
   echo If you're seeing this after executing a script file,
   echo then right click on it and select "Run As Administrator" option.
   echo ################################################################
   echo.
   PAUSE
   EXIT /B 1
)

:VERSIONCHECK

	FOR /F "tokens=3*" %%A IN ('REG QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName ^| FIND "ProductName"') DO SET PRODUCTNAME=%%A %%B
	
        FOR /F "tokens=3" %%A IN ('REG QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "EditionID"') DO SET EDITIONID=%%A
	IF /I NOT "%EDITIONID:~0,11%" == "ProfessionalWMC" IF /I NOT "%EDITIONID:~0,10%" == "Enterprise" IF /I NOT "%EDITIONID:~0,12%" == "Professional" GOTO UNSUPPORTED

	FOR /F "tokens=3" %%A IN ('REG QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "CurrentBuild"') DO SET CURRENTBUILD=%%A
	IF /I NOT "%CURRENTBUILD%" == %SET_CURRENTBUILD%  GOTO UNSUPPORTED

	GOTO START

:UNSUPPORTED
	ECHO.
	ECHO Your operating system is not supported.
	ECHO Only for %WINVER%
	GOTO END

:START
	CLS
	IF /I EXIST %SystemRoot%\SysWOW64 (SET BIT=64) ELSE (SET BIT=32)

:DETECTARGUMENTS

        SET BLANK=1
	IF /I *%1 == *BLANK SET BLANK=0
	IF /I *%2 == *BLANK SET BLANK=0

:SETSOURCEFOLDER

	REM This will get the folder the batch file was launched from since the current
	REM directory will change if launched from a network share
	SET SOURCEFOLDER=%~dp0
	ECHO Source Folder is %SOURCEFOLDER%
	ECHO.

:TAKEOWNERSHIP

	ECHO Taking ownership of %SystemRoot%\System32\termsrv.dll
	takeown /a /f %SystemRoot%\System32\termsrv.dll
	ECHO Granting Administrators rights
	ICACLS %SystemRoot%\System32\termsrv.dll /Grant Administrators:F

:CHECK TermService SERVICE STATE AND ENABLE IF STOPPED

for /F "tokens=3 delims=: " %%H in ('sc query "TermService" ^| findstr "STATE"') do (
   if /I "%%H" NEQ "RUNNING" (
    net start "TermService"
  )
)

:STOPTERMINALSERVICES

	ECHO Stopping Remote Desktop Services
	NET stop "TermService" /y

:BACKUPTERMSRVDLL

	IF /I EXIST %SystemRoot%\System32\termsrv.dll.bak GOTO PATCHED
	COPY "%SystemRoot%\System32\termsrv.dll" "%SystemRoot%\System32\*.*.bak"

:COPYTERMSRVDLL

	IF /I NOT EXIST "%SOURCEFOLDER%%BIT%_termsrv.dll" (
		ECHO.
		ECHO The %BIT% version of termsrv.dll is not present
		ECHO.
		ECHO Use switch -? to show help.
		ECHO.
		GOTO END
	)

	ECHO Copying "%SOURCEFOLDER%%BIT%_termsrv.dll" to "%SystemRoot%\System32\termsrv.dll"
	COPY /Y "%SOURCEFOLDER%%BIT%_termsrv.dll" "%SystemRoot%\System32\termsrv.dll"

	GOTO IMPORTREGKEYS

:PATCHED

	ECHO ######################################
	ECHO # Patched Already , Check it...      #
	ECHO ######################################

:IMPORTREGKEYS

	ECHO Enabling RDP
	REG ADD "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f

:SETSINGLESESSIONSETTING

	ECHO Setting fSingleSessionPerUser to %SINGLESESSION%
	REG ADD "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fSingleSessionPerUser /t REG_DWORD /d 0 /f

:SETBLANKPASSWORDPOLICY

	ECHO Setting LimitBlankPasswordUser to %BLANK%
	REG ADD "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d %BLANK% /f

:CONFIGUREFIREWALL

	ECHO Configuring Remote Desktop in Windows Firewall
	NETSH advfirewall firewall set rule group="remote desktop" new enable=Yes

:STARTTERMINALSERVICES

	ECHO Starting Remote Desktop Services
	NET START "TermService"

:PAUSE5SECONDS

	ECHO Pausing 5 seconds to give service time to start listening
	CHOICE /n /c y /d y /t 5 > nul

:CHECKIFSERVICELISTENING
	ECHO Checking if Service is listening on port 3389
	SUBST
	NETSTAT -a | find /i "3389"
	IF ERRORLEVEL 1 GOTO SERVICENOTLISTENING

:SERVICEISLISTENING

	ECHO Service is listening
	ECHO Done
	GOTO END

:SERVICENOTLISTENING

	ECHO Service is not listening

:CONTINUE

	ECHO Done
	
:END
PAUSE