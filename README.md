# EnSySim

Generic, statistics based energy system modell for testing and validation of control algorithms for smart grids. While the model set up is implemented in python the performance critical model components are written in rust.

# Getting started

Since compiled files are not beeing synced for this repository, you'll have to build them your own. Here's how:
__At this point I'm explaining the toolchain used by us. Of course you asre free to use different IDEs and compilers__

1. Download and install vs code and vs code buildtools from [here](https://visualstudio.microsoft.com/de/downloads/) and [here](https://visualstudio.microsoft.com/de/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16). Also install the Marketplace extension for Jupyter notebooks.
2. Clone the repository to your hard drive
3. create a new conda environment and install
    - numpy
    - pandas
    - plotly
    - pytables (+nbformat)
4. Download and install rustup from [here](https://www.rust-lang.org/learn/get-started)
5. Change to nightly build with `rustup default nightly`
6. build with `cargo +nightly build --release`, make sure to rename the compiled .dll to .pyd and move it to the \SystemComponentsFast folder. For this you can have a look at the ReleaseExample.cmd 
7. Try to execute the TestGenericCell.ipynb to see if everything works.
