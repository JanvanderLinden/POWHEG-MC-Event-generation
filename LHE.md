# Instructions for the ttb-jets LHE production with POWHEG-BOX-RES
<!-- TOC -->

- [Setup](#setup)
    - [Setup for job submission](#setup-for-job-submission)
        - [Set up a CMSSW_10_2_14 environment](#set-up-a-cmssw_10_2_14-environment)
        - [Install POWHEG-BOX-RES](#install-powheg-box-res)
        - [Install this repository](#install-this-repository)
    - [Setup for postprocess](#setup-for-postprocess)
        - [Set up a CMSSW environment](#set-up-a-cmssw-environment)
        - [Install this repository](#install-this-repository)
        - [Create folders](#create-folders)
- [Event Generation](#event-generation)
    - [Setting up a run](#setting-up-a-run)
         - [Initialization](#initialization)
         - [Parallel Stages 1-3](#parallel-stages-1-3)
         - [LHE file production](#lhe-file-production)
- [Postprocess](#postprocess)
    - [Moving the files](#moving-the-files)
    - [Merging the files](#merging-the-files)
- [Useful tips and links](#useful-tips-and-links)
  
<!-- /TOC -->

**NOTE: lxplus7 is not longer available and lxplus9 does not support the CMSSW releases that are needed for POWHEG. To overcome this, we will use `Singularity` in order to run the CMSSW version needed. More info about Singularity can be found [here](https://cms-sw.github.io/singularity.html).**

# Setup

## Setup for job submission 
First set up a directory into the AFS space where the job submission will take place. 
(HTCondor submission works only in the AFS space. If you haven't already done it, extend the AFS space to the maximum _10 GB_. You can do that [here](https://resources.web.cern.ch/resources/Manage/AFS/Settings.aspx). _This link is also useful to keep track the amount of storage that is being used at any moment_)
```
mkdir MCProduction ; cd MCProduction
base=$PWD
```
All commands are given relative to this `$base`

Install `yaml` package for python3 if not available:
```
pip3 install --user pyyaml
```

### Set up a CMSSW_14_0_12 environment 

First, launch the singularity environment by using the command:
```
cmssw-el7
```
Then, inside the singularity environment run the following commands:
```
cd $base
scram project CMSSW_14_0_12
cd $base/CMSSW_14_0_12/src
cmsenv
cd $base
```

### Install POWHEG-BOX-RES and the ttbb process

We will use a pre-packaged version which contains the correct versions for the required packages
```
cd $base
cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/Run3_powheg/powhegboxRES_rev4041_date20231121.tar.gz .
tar -xf powhegboxRES_rev4041_date20231121.tar.gz
```

Unpack also the ttbb process:
```
cd $base/POWHEG-BOX/
tar -xf ttbb
```

Then compile the fortran code of POWHEG:
(NOTE: The compilation must be done with the CMSSW loaded, so the Singularity environment is again needed.)  
```
cd $base
cmssw-el7
cd $base/CMSSW_14_0_12/src
cmsenv
cd $base/POWHEG-BOX/ttbb
make pwhg_main
make lhef_decay
```

The ttbb POWHEG code is now in principle ready to run. We can now also install this repository to ease the event generation and submit to HTCondor.

### Install this repository
```
cd $base
git clone https://github.com/JanvanderLinden/POWHEG-MC-Event-generation.git -b Run3
```

For a new production it is recommended to create a new directory now in which you can store everything needed for that production, e.g.
```
cd $base
mkdir production
cd production
production=$PWD
```

## Setup for postprocess (only needed for post processing of LHE files)

Due to limited amount of storage inside the AFS space, it is suggested to move every job into the EOS space for the postprocessing.

Go to your EOS space and create a folder, preferably with the same name as the on in the AFS space.
```
mkdir MCProduction ; cd MCProduction
base_eos=$PWD
```
### Set up a CMSSW environment 
We do not need a specific release, but we want a version that is it supported by lxplus9:
```
scram project CMSSW_13_2_11
cd $base_eos/CMSSW_13_2_11/src
cmsenv
cd $base_eos
```

### Install this repository
```
cd $base_eos
git clone https://github.com/nplastir/POWHEG-MC-Event-generation.git
```

### Create folders
For the postprocess, POWHEG is not required but for convenience, it is better to create some folders that mimic the ones in the AFS space.
```
cd $base_eos
mkdir -p POWHEG-BOX-RES/ttbb
mkdir production_test
production_eos=$PWD
```


# LHE Event Generation

### Setting up a run

To start a run from scratch, first an intialization has to be performed where a working directory is created and settings are determined.
Then, parallelstages can be run (i.e. submitted to HTCondor).

**Important: For the following commands, the CMSSW environment is required, so launch Singularity and run everything inside it**
```
cmssw-el7
cd $base/CMSSW_14_0_12/src
cmsenv
```

### Initialization

Initialize a new run via:
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py --init -for-lhe -p ../POWHEG-BOX/ttbb -i /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/Run3_powheg/grids_nominal/muR1.0_muF2.0 -t [NAME] (--mur [MUR])(--muf [MUF])(--mass [MASS])(--pdf [PDF])
```
This will create a folder `[NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF]` in `$production` with the necessary files, as well as a run folder inside the `POWHEG-BOX/ttbb` directory.

Use the help function of `POWHEG-MC-Event-generation/run.py` for more details on the options.
In summary:
- `-p` the path to the process directory in your `POWHEG-BOX` has to be given.
- `-i` specifies a path to the necessary input files for LHE production. Make sure that you are using the correct one, matching your desired muR/muF scale choice/etc.
- `-t` specifies a name tag for the run to differentiate it from other productions.

In addition, in this initialization step, the following factors can be changed, but are set to the defaults for Run 3:
- `--mur` specifies the renormalization scale.
- `--muf` specifies the factorization scale.
- `--mass` specifies the mass of the top quark.
- `--pdf` specifies the pdf of the proton.

If these factors are not explicitly set, then, the run will initialize with the default values: `--muf 2.0 --mur 1.0 --pdf 325500 --mass 172.5`.

**Example:**
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py --init --for-lhe -p ../POWHEG-BOX/ttbb -i /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/Run3_powheg/grids_nominal/muR1.0_muF2.0 -t lhe_test
```
where this command will create a work directory called `lhe_test__r1.0_f2.0_m172.5_p325500` 


----------


### LHE file production


The jobs for the LHE production can be submitted via 
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 4 -n [NBATCHES] -N [NEVENTSPERJOB] --decay [DECAYCHANNEL] -f
```

The options `-N`, `-n` and `--decay` specify the number of events per job (defaults to 1000), the number of parallel jobs (defaults to 500) and the ttbar decay channel.
The last option is mandatory and has to be specified. The options are:
- `1L`: for semileptonic ttbar decays
- `0L`: for fully hadronic ttbar decays
- `2L`: for dileptonic ttbar decays
- `incl`: for inclusive ttbar decays

**Example:**
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w ./test__r1.0_f2.0_m172.5_p325500 -S 4 -n 500 -N 1000 --decay 2L -f
```

**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f2.0_m172.5_p325500/submit/
condor_submit stage4.sub
```

# Postprocess
## Moving the files
Ater the jobs have finished, we want to move everything into the EOS space.
```
cd $production
mv [NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF] /eos/user/<initial>/<username>/.../MCProduction/production_test/

cd $base/POWHEG-BOX-RES/ttbb
mv run__[NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF] /eos/user/<initial>/<username>/.../MCProduction/POWHEG-BOX-RES/ttbb/
```

e.g.
```
cd $production
mv test__r1.0_f2.0_m172.5_p325500 /eos/user/n/nplastir/ttH/MCProduction/production_test/

cd $base/POWHEG-BOX-RES/ttbb
mv run__test__r1.0_f2.0_m172.5_p325500 /eos/user/n/nplastir/ttH/MCProduction/POWHEG-BOX/ttbb/
```
After everything has been moved, we can proceed with the merging 

## Merging the files

Firstly, we need to change the paths for our script to work. We need to access the `settings.yml` file in each job folder
```
cd $production_eos
cd [NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF]
# Open the file with your editor, in this example I use VScode
code settings.yml
```
Now that we have opened the file `settings.yml`, we need to change the paths for:
- powheg.input: 
- pwg-rwl: 
- run_dir: 

If you are using the same names for the folders, you should basically need to replace `/afs/cern.ch/user/<initial>/<username>/MCProduction` with `/eos/user/<initial>/<username>/.../MCProduction`

After the change of the paths has been completed  we need to load the CMSSW enviroment
```
cd $base_eos/CMSSW_13_2_11/src
cmsenv
cd $base_eos
```
Then we are ready to merge the files
```
cd $production_eos
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 4 -n [NBATCHES] -N [NEVENTSPERJOB] --decay [DECAYCHANNEL] --lhe
```

**NOTE: This process takes several hours when the number of events is high. Run it in a tmux!**

-----------------
# Useful tips and links

- For the 10 GB in your AFS space, you can approximatelly run about 3 jobs (1000 jobs/1000 events each) simultaneously without having any storage problems.
- Do not merge two different files simutaneously! You need to wait for the script to move all the files and count the events for the first job and then go to the second one.
- During merging there is a possibility to stumbe across the error message `Input/Output error`. This can be solved by manually unziping the files `gzip -d "file.lhe.gz"`. If the file does not have the suffix `.gz` you can simply rename the files with the suffix and then unzip them.
- In order to have a persistent tmux session on lxplus9, you need to run `systemctl --user start tmux.service` and then `tmux a` to attach. (More info [here](https://hsf-training.github.io/analysis-essentials/shell-extras/persistent-screen.html))
- You can create an alias for the above command in your `~/.bashrc` file. Open it with your editor `code ~/.bashrc` and include the line `alias tmux9='systemctl --user start tmux.service'`. Then, when you want to launch a new tmux in lxplus9 you can simply type `tmux9` in order to launch it and then `tmux a` to attach.
- If you want to further process the LHE files, there is a [repository](https://github.com/nplastir/LHE-scripts) with all the necessary scripts.
- If you want to manually shower the LHE files, you can find instructions [here](https://gitlab.cern.ch/cms-top-tmg/tmg-code/-/tree/master/pLHE-to-GEN?ref_type=heads)
