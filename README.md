# EnSySim

Generic, statistics based energy system modell for testing and validation of control algorithms for smart grids. While the model set up is implemented in python the performance critical model components are written in rust.

# Getting started

Since compiled files are not beeing synced for this repository, you'll have to build them on your own. Here's how:
__At this point I'm explaining the toolchain used by us. Of course you are free to use different IDEs and compilers, also there´s no need to use the interactive jupyter notebooks__


1. Download and install vs code and vs code buildtools from [here](https://visualstudio.microsoft.com/de/downloads/) and [here](https://visualstudio.microsoft.com/de/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16). Also install the Marketplace extension for Python/Jupyter notebooks.
1. Git Clone the repository to your hard drive
1. install miniconda from [here](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwj-po7-g6HzAhX3RPEDHZxFA2gQFnoECA4QAw&url=https%3A%2F%2Fconda.io%2Fminiconda.html&usg=AOvVaw0mHTnCzKwOB8I7G-8HMT_V)
1. Create a new conda environment and install the packages listed in requirements.txt using the forge channel (`conda config --env --add channels conda-forge`). For this you can use the configure_conda.cmd executed in an Anaconda Prompt (see start menu).
1. For using jupyter notebooks and interactive plotly visualization directly in visual studio code install the python extension (settings -> extensions -> python). For the test cases to work create a settings.json file under .vscode folder and add following line in curly brackets: `"jupyter.notebookFileRoot": "${workspaceFolder}"`
1. Download and install rustup from [here](https://www.rust-lang.org/learn/get-started)
1. Change to nightly build with shell command `rustup default nightly` (needed for pyo3-python connection)
1. build with `cargo +nightly build --release`, make sure to rename the compiled .dll to .pyd and move it to the \SystemComponentsFast folder. For this you can use the ReleaseExample.cmd, rename it to Release.cmd and replace the placeholders concerning the path to activate.bat (in your conda installation path under Scripts/) and conda environment name. For building you can use Ctrl+Shift+P -> Run Task -> SCfast release.
1. Try to execute the different scenarios under Tests/ to see if everything works. This should be done using the jupyter cell commands (Run Cell / Run Below)
    - Set the current working directory to the root directory
1. make sure to install the vs code extensions (python, jupyter)
1. 
1. choose the right python environment for jupyter (blue bar bottom)
1. 
