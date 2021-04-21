call PATH_TO_CONDA_ACTIVATE PYTHON_ENV_NAME
cargo +nightly build
ren .\target\debug\SystemComponentsFast.dll SystemComponentsFast.pyd
move .\target\debug\SystemComponentsFast.pyd ..\SystemComponentsFast.pyd
move .\target\debug\SystemComponentsFast.pdb ..\SystemComponentsFast.pdb