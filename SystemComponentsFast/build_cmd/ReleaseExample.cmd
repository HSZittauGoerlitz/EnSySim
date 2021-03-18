call PATH_TO_CONDA_ACTIVATE PYTHON_ENV_NAME
cargo +nightly build --release
ren .\target\release\SystemComponentsFast.dll SystemComponentsFast.pyd
move .\target\release\SystemComponentsFast.pyd ..\SystemComponentsFast.pyd