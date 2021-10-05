# EnSySim

Generic, statistics based energy system modell for testing and validation of control algorithms for smart grids. While the model set up is implemented in python the performance critical model components are written in rust.

# Getting started

Since compiled files are not beeing synced for this repository, you'll have to build them on your own. Here's how:
__At this point I'm explaining the toolchain used by us. Of course you asre free to use different IDEs and compilers__


1. Download and install vs code and vs code buildtools from [here](https://visualstudio.microsoft.com/de/downloads/) and [here](ttps://visualstudio.microsoft.com/de/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16). Also install the Marketplace extension for Python/Jupyter notebooks.
1. Git Clone the repository to your hard drive
1. install miniconda from [here](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwj-po7-g6HzAhX3RPEDHZxFA2gQFnoECA4QAw&url=https%3A%2F%2Fconda.io%2Fminiconda.html&usg=AOvVaw0mHTnCzKwOB8I7G-8HMT_V)
1. create a new conda environment and install (conda create -n env)
    - numpy
    - pandas
    - plotly
    - pytables (+nbformat)
    - cuplinks
1. Download and install rustup from [here](https://www.rust-lang.org/learn/get-started)
1. Change to nightly build with `rustup default nightly` (needed for pyo3-python connection)
1. build with `cargo +nightly build --release`, make sure to rename the compiled .dll to .pyd and move it to the \SystemComponentsFast folder. For this you can have a look at the ReleaseExample.cmd 
1. Try to execute the TestGenericCell.ipynb to see if everything works.
    - Set the current working directory to the root directory
1. make sure to install the vs code extensions (python, jupyter)
1. "jupyter.notebookFileRoot": "${workspaceFolder}"
1. choose the right python environment for jupyter (blue bar bottom)
1. conda config --env --add channels conda-forge (weil python kernel version)


<a href=""></a>



