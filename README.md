# EnSySim

Generic, statistics based energy system modell for testing and validation of control algorithms for smart grids. While the model set up is implemented in python the performance critical model components are written in rust.

# Getting started

Since compiled files are not beeing synced for this repository, you'll have to build them on your own. Here's how:
__At this point I'm explaining the toolchain used by us. Of course you asre free to use different IDEs and compilers__

<ol>
<li>Download and install vs code and vs code buildtools from <a href="https://visualstudio.microsoft.com/de/downloads/">here</a> and <a href="https://visualstudio.microsoft.com/de/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16">here</a>. Also install the Marketplace extension for Jupyter notebooks.</li>
<li>Git Clone the repository to your hard drive</li>
<li>install miniconda from [here](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwj-po7-g6HzAhX3RPEDHZxFA2gQFnoECA4QAw&url=https%3A%2F%2Fconda.io%2Fminiconda.html&usg=AOvVaw0mHTnCzKwOB8I7G-8HMT_V)</li>
<li>create a new conda environment and install (conda create -n env)
    - numpy
    - pandas
    - plotly
    - pytables (+nbformat)
    - 
    - cuplinks</li>
<li>Download and install rustup from [here](https://www.rust-lang.org/learn/get-started)</li>
<li>Change to nightly build with `rustup default nightly` (needed for pyo3-python connection)</li>
<li>build with `cargo +nightly build --release`, make sure to rename the compiled .dll to .pyd and move it to the \SystemComponentsFast folder. For this you can have a look at the ReleaseExample.cmd </li>
<li>Try to execute the TestGenericCell.ipynb to see if everything works.
    - Set the current working directory to the root directory</li>
<li>make sure to install the vs code extensions (python, jupyter)</li>
<li>"jupyter.notebookFileRoot": "${workspaceFolder}"</li>
<li>choose the right python environment for jupyter (blue bar bottom)</li>
<li>conda config --env --add channels conda-forge (weil python kernel version)</li>
</ol>
