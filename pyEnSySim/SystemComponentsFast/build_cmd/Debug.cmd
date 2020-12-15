call C:/Miniconda3/Scripts/activate jupyterForge
cargo +nightly build
ren .\target\debug\ts_props.dll ts_props.pyd
move .\target\debug\ts_props.pyd ..\ts_props.pyd