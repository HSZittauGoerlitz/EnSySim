cd /D "%~dp0"
call conda config --env --add channels conda-forge
call conda create --name pyEnSySim --file requirements.txt