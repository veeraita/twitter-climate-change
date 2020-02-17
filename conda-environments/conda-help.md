# Quick Guide to Using Jupyter Notebook and Conda environments
**Motivation:** The usefulness of Conda environments is particularly emphasized in larger group projects where several people need to work on the same set of *Jupyter Notebooks* and thus *python* libraries. In this case, it is useful that two users **A** and **B** have the same python libraries available for use (each jupyter notebook or python file always declare their dependencies at the beginning via import commands: `import libraryname`) and preferably also the same versions of these libraries. This ensures that all methods / functions inside libraries are available to both users. Installing libraries without separate environments is a bad solution over the long run.

Many libraries such as **pandas** (well-known data manipulation library) or **seaborn** (well-known visualization library) are dependent on multiple other libraries like numpy and matplotlib which are again dependent on others "lower level" libraries. All of these libraries are constantly updated and developed, which also causes changes to the dependent libraries. Because of these numerous dependencies and cascading changes in the software ecosystem, as the number of installed Python libraries build up on your machine, the number of possible compatibility issues will also increase exponentially. This complexity can be managed by creating many different conda environments with well-defined set of (only the necessary) libraries fit for their purpose.

The idea with **conda environments** is to create a distinction between different coding environments in the same style as project-specific git repositories create distinction between different projects. For example, one common environment `aalto-sci-project` could be used in this project, but environments can also be divided, for example by subgroups. Example:
1. ** Data preparation environment ** (includes only numpy and tweepy libraries with dependencies)
1. ** Machine learning environment ** (includes machine learning libraries such as sklearn, nltk, pytorch and the required visualization libraries with dependencies)
2. ** Network analysis environment ** (includes network analysis libraries such as networkx, scipy and the required visualization libraries with dependencies.)

Instructions are for conda on Mac and Linux. With Windows you can use the graphical interface to manage environments or alternatively `anaconda prompt`. 

#### Installing conda (Skip this if already installed)
1. Download [miniconda] (https://docs.conda.io/en/latest/miniconda.html) or anaconda `.sh` as a file with the extension.
   **Note:** Anaconda is easier to use thanks to its graphical user interface and contains more pre-built libraries than miniconda, but also takes up significantly more space.

2. Give the downloaded installation file permissions, there will be `permissions` in the file settings or a similar tab where you can set the file to executable or you can simply open up the terminal to the folder and run `sudo chmod +x filename.sh`. 

3. Open the terminal to the folder where the file is. Install with `./ <filename> .sh`, and answer the installation questions. In the end, the installer usually asks if the `conda` command should be added to the PATH 
 * By answering **yes**, you can in the future execute `conda` commands within any opened terminal and file path.

4. Restart the terminal to update the `conda` command. Next, make sure that the `conda` command works in the terminal by typing` man conda`. The terminal should print the conda manual with all the available commands.

#### Installing the Environment (environment)
With environment files, conda can create identical environments for different machines.
1. Let's move on to installing the environment. Navigate to the git project folder called `aalto-lst-project`.

2. Update the repository to the latest one by doing a `git pull` in the terminal.

3. Now the `/ conda-environments` subfolder should contain files with` .yml` extensions. A single file is a description of a single conda environment and contains information about all the python libraries in the environment and their versions.

[Examples of the environment file.](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually)


4. Open the terminal in the project folder and run the command: `conda env create -f filename.yml`. Conda installs all the libraries specified in the `.yml` file and compatible versions of these in a new stand-alone python environment, name of which is defined in the first row of the `filename.yml` file.

5. Now you can open up the Jupyter Notebook (or Jupyter Lab) with the command `jupyter notebook` (or` jupyter lab`), and you can choose from the 'Kernel -> Change Kernel ...' menu to activate your newly installed conda environment (or any other environment you want).
  **Note!** If for some reason the environment does not appear in the `Change Kernel` menu, you can do the following:
  * Close the jupyter with the `Ctrl + C` combination on the Notebook and respond with` y` for confirmation. Then run the following command:
  * `ipython kernel install --user --name = <environmentname>`
  * now you can reboot your jupyter notebook with `jupyter notebook` or Lab`` jupyter lab`.

If you want to use the environments outside the jupyter, you can also activate / deactivate them directly in the terminal:
* `conda info --envs` command lists all installed environments
* `conda activate environment_name` enables the environment called `environment_name`
* `conda deactivate` deactivates the environment and restores the default computer environment (contains the set of python libraries that you had installed on your computer before installing the conda).