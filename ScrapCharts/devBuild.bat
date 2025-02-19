@echo off
setlocal enabledelayedexpansion

set "SOURCE_FOLDER=%~dp0"
set "TEMP_FOLDER=C:\TempCopy"
set "WSL_DEST=/mnt/docker-desktop-disk/data/docker/volumes/webodm_appmedia/_data/plugins/ScrapCharts"

if exist "!TEMP_FOLDER!" rmdir /S /Q "!TEMP_FOLDER!"
mkdir "!TEMP_FOLDER!"
mkdir "!TEMP_FOLDER!\public"
mkdir "!TEMP_FOLDER!\templates"

rem copy "!SOURCE_FOLDER!public\Chart.min.js" "!TEMP_FOLDER!\public\"
rem copy "!SOURCE_FOLDER!public\venobox.min.js" "!TEMP_FOLDER!\public\"
rem copy "!SOURCE_FOLDER!public\venobox.min.css" "!TEMP_FOLDER!\public\"
rem copy "!SOURCE_FOLDER!public\ChartColors.js" "!TEMP_FOLDER!\public\"
rem copy "!SOURCE_FOLDER!public\xlsc.full.min.js" "!TEMP_FOLDER!\public\"
copy "!SOURCE_FOLDER!templates\volume_graphs.html" "!TEMP_FOLDER!\templates\"
copy "!SOURCE_FOLDER!templates\volume_graphs_single.html" "!TEMP_FOLDER!\templates\"
copy "!SOURCE_FOLDER!templates\volume_error.html" "!TEMP_FOLDER!\templates\"
copy "!SOURCE_FOLDER!templates\volume_developer.html" "!TEMP_FOLDER!\templates\"
rem copy "!SOURCE_FOLDER!__init__.py" "!TEMP_FOLDER!\"
rem copy "!SOURCE_FOLDER!manifest.json" "!TEMP_FOLDER!\"
rem copy "!SOURCE_FOLDER!plugin.py" "!TEMP_FOLDER!\"
rem copy "!SOURCE_FOLDER!backend_api.py" "!TEMP_FOLDER!\"
rem copy "!SOURCE_FOLDER!config.py" "!TEMP_FOLDER!\"
rem copy "!SOURCE_FOLDER!webodm_access.py" "!TEMP_FOLDER!\"

wsl -d docker-desktop cp -rf /mnt/host/c/TempCopy/* "!WSL_DEST!/"
rmdir /S /Q "!TEMP_FOLDER!"