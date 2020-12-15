call C:/Miniconda3/Scripts/activate jupyterForge
cargo +nightly build --release
ren .\target\release\SystemComponentsFast.dll SystemComponentsFast.pyd
move .\target\release\SystemComponentsFast.pyd ..\SystemComponentsFast.pyd