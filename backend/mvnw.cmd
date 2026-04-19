@REM ----------------------------------------------------------------------------
@REM Licensed to the Apache Software Foundation (ASF)
@REM Maven Wrapper startup batch script
@REM ----------------------------------------------------------------------------
@echo off

@setlocal

set WRAPPER_JAR="%~dp0.mvn\wrapper\maven-wrapper.jar"

"%JAVA_HOME%\bin\java.exe" %MAVEN_OPTS% ^
  -jar %WRAPPER_JAR% %*
if ERRORLEVEL 1 goto error
goto end

:error
set ERROR_CODE=1

:end
@endlocal & set ERROR_CODE=%ERROR_CODE%
exit /B %ERROR_CODE%
