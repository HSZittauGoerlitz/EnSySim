call C:/Miniconda3/Scripts/activate jupyterForge
cargo +nightly rustc --profile=check -- -Z unstable-options --pretty=expanded > ./src/expanded.rs
rustup run nightly rustfmt ./src/expanded.rs
