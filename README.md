# Instructions for the ttb-jets MC event production with POWHEG-BOX-RES
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

Install `yaml` package for python3:
```
pip3 install --user pyyaml
```

### Set up a CMSSW_10_2_14 environment 
This CMSSW version is only available for CentOs 7, so the installation needs to be done inside the Singularity environment

First, launch the singularity environment by using the command:
```
cmssw-el7
```
Then, inside the singularity environment run the following commands:
```
cd $base
scram project CMSSW_10_2_14
cd $base/CMSSW_10_2_14/src
cmsenv
cd $base
```

### Install POWHEG-BOX-RES
```
cd $base
svn checkout --revision 3604 --username anonymous --password anonymous svn://powhegbox.mib.infn.it/trunk/POWHEG-BOX-RES
```
We are using revision 3604, which is the stable release version. More recent revisions have not been tested yet.

Get the code for the ttbb process:
```
cd $base/POWHEG-BOX-RES
git clone ssh://git@gitlab.cern.ch:7999/tjezo/powheg-box-res_ttbb.git ttbb
```
Enter the ttbb directory and check out the appropriate commit that fits to r3604 of the POWHEG-BOX-RES code:
```
cd $base/POWHEG-BOX-RES/ttbb
git checkout 128aefb6061b72714d34e5f1d4798967f76f9585
```
Then compile the fortran code of POWHEG:

(NOTE:The compilation must be done with the CMSSW loaded, so the Singularity environment is again needed.)  
```
cd $base
cmssw-el7
cd $base/CMSSW_10_2_14/src
cmsenv
cd $base/POWHEG-BOX-RES/ttbb
make pwhg_main
make lhef_decay
```

The ttbb POWHEG code is now in principle ready to run. We can now also install this repository to ease the event generation and submit to HTCondor.

### Install this repository
```
cd $base
git clone https://github.com/nplastir/POWHEG-MC-Event-generation.git
```

For a new production it is recommended to create a new directory now in which you can store everything needed for that production, e.g.
```
cd $base
mkdir production_test
cd production_test
production=$PWD
```

In `$base/POWHEG-MC-Event-generation/ttbb_powheg_inputs/` a few `powheg.input` files are stored which can be used as examples for event production. The settings of course can be adjusted based on what configuration is supposed to be generated.

## Setup for postprocess 

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

# Event Generation

## Setting up a run

In `POWHEG-MC-Event-generation` three stages are supported for running all of the powheg parallel stages. 
To start a run from scratch, first an intialization has to be performed where a working directory is created and settings are determined.
Then, parallelstages can be run (i.e. submitted to HTCondor).
After one stage has finished, the output of the previous stage can be validated.

**Important: For the following commands, the CMSSW environment is required, so launch Singularity and run everything inside it**
```
cmssw-el7
cd $base/CMSSW_10_2_14/src
cmsenv
```

### Initialization

Initialize a new run via:
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py --init -p ../POWHEG-BOX-RES/ttbb -i ../POWHEG-MC-Event-generation/ttbb_powheg_inputs/powheg.input_nominal -t [NAME] (--mur [MUR])(--muf [MUF])(--mass [MASS])(--pdf [PDF])
```
This will create a folder `[NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF]` in `$production` with the necessary files, as well as a run folder inside the `POWHEG-BOX-RES/ttbb` directory.

Use the help function of `POWHEG-MC-Event-generation/run.py` for more details on the options.
In summary:
- `-p` the path to the process directory in your `POWHEG-BOX-RES` has to be given.
- `-i` specifies a `powheg.input` file to use for this production. Make sure that you are using the correct one. Options:
   - `powheg.input_nominal`
   - `powheg.input_hdampUP`
   - `powheg.input_hdampDOWN`
- `-t` specifies a name tag for the run to differentiate it from other productions.

In addition, in this initialization step, the following factors can be changed:
- `--mur` specifies the renormalization scale.
- `--muf` specifies the factorization scale.
- `--mass` specifies the mass of the top quark.
- `--pdf` specifies the pdf of the proton.

If these factors are not explicitly set, then, the run will initialize with the default values: `--muf 1.0 --mur 1.0 --pdf 320900 --mass 172.5`.

**Example:**
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py --init -p ../POWHEG-BOX-RES/ttbb -i ../POWHEG-MC-Event-generation/ttbb_powheg_inputs/powheg.input_nominal -t test
```
where this command will create a work directory called `test__r1.0_f1.0_m172.5_p320900` 

----------
After the initialization of the run, [parallel stages 1-3](#parallel-stages-1-3) can be submitted in order to start a full production, or if the inputs for producing LHE files are already available, only [stage 4](#lhe-file-production) has to be run

----------


### Parallel Stages 1-3
After initialization of the run, parallel stages can be submitted:

1. **Stage 1**

```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 1 -n [NBATCHES]
```
- Here, `-w` specifies the path to the previously created work directory (e.g. `-w ./test__r1.0_f1.0_m172.5_p320900`)
- With `-n` you can create the number of jobs to be submitted, e.g. `-n 1000` for 1000 submitted jobs.
- The parameters `-S` and `-X` specify the parallel stage (`-S`) and xgriditeration (`-X`) to run.

The number of jobs here will determine the number of ubound files we have in the end. (<ins>Recommended 100-200 jobs</ins>)

**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage1_it1.sub
```

After the jobs of one parallel stage are done the output can be validated before the next step has to be run:
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 1 -n [NBATCHES] --validate
```

If validation was successful then the next step is to run again stage 1 but with different xgriditeration in order to refine the grid integration:

```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 2 -n [NBATCHES]
```
**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage1_it2.sub
```

After these jobs are completed we validate them:
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 2 -n [NBATCHES] --validate
```
and then run it again with `-X 3`:

```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 3 -n [NBATCHES]
```
**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage1_it3.sub
```

and again validation:

```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 1 -X 3 -n [NBATCHES] --validate
```

The first parallelstage has to be run at least three times as indicated above but can be continued with more xgridintegrations if needed. (<ins>Recommended 5 xgriditerations</ins>)

2. **Stage 2**

For this stage, it is only required to be run once and with the same number of jobs as in stage 1
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 2 -n [NBATCHES]
```
**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage2.sub
```

This stage will take a while to finish. When all jobs are completed, you need to validate them before moving to the next stage. 
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 2 -n [NBATCHES] --validate
```

3. **Stage 3**

After stage 2 has finished, submit again with the same number of jobs as in previous stages 
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 3 -n [NBATCHES]
```
**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage3.sub
```

This stage will only take a couple minutes in order to finish. When it is finished, validate:
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 3 -n [NBATCHES] --validate
```
If the validation was successful, you can now proceed to the LHE production.

----------

### LHE file production

For this stage, make sure that you have initialized the working directory with the appropriate generator settings (mur,muf,mass,pdf).

Then, proceed to copy all the grid files for the LHE run to the run directory `run__[NAME]__r[MUR]_f[MUF]_m[MASS]_p[PDF]` that has been created inside the `POWHEG-BOX-RES/ttbb/`. 
Availiable grids:
- muR=1.0, muF=1.0:
```
cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/grids_nominal/muR1.0_muF1.0/*
```
- muR=1.0, muF=2.0:
```
cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/grids_nominal/muR1.0_muF2.0_v2/*
```
- muR=1.0, muF=1.0 for hdampUp:
```
cp /afs/cern.ch/user/n/nplastir/public/grids_hdampUP/muR1.0_muF1.0/*
```
or
```
cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/grids_hdampUP/muR1.0_muF1.0/*
```
- muR=1.0, muF=2.0 for hdampUp:
```
cp /afs/cern.ch/user/n/nplastir/public/grids_hdampUP/muR1.0_muF2.0/*
```
- muR=1.0, muF=1.0 for hdampDOWN:
```
cp /afs/cern.ch/user/n/nplastir/public/grids_hdampDOWN/muR1.0_muF1.0/*
```
or
```
cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/grids_hdampDOWN/muR1.0_muF1.0/*
```
- muR=1.0, muF=2.0 for hdampDOWN:
```
cp /afs/cern.ch/user/n/nplastir/public/grids_hdampDOWN/muR1.0_muF2.0/*
```

(e.g. `cp /afs/cern.ch/work/v/vanderli/public/ttbb-lhe-inputs/grids_nominal/muR1.0_muF2.0/* $base/POWHEG-BOX-RES/ttbb/run__test__r1.0_f1.0_m172.5_p320900`).

After everything has been copied inside the run directory, the jobs for the LHE production can be submitted via 
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w [PATH_TO_WORKDIR] -S 4 -n [NBATCHES] -N [NEVENTSPERJOB] --decay [DECAYCHANNEL] -f
```
**NOTE: Because we are running everything inside the Singularity environment, the automatic job submission to condor is not possible. Therefore, in an another lxplus9 node, go to the newly generated folder and submit the jobs manually. E.g.**
```
cd $production/test__r1.0_f1.0_m172.5_p320900/submit/
condor_submit stage4.sub
```

You have to append the option `-f` to force the submission of batch jobs as otherwise this is blocked as parallel stages 1-3 were skipped.
Two additional options are required for this step, `-N` and `--decay`. The first specifies the number of events per job (defaults to 1000), and the second specifies the ttbar decay channel.
This option is mandatory and has to be specified. The options are:
- `1L`: for semileptonic ttbar decays
- `0L`: for fully hadronic ttbar decays
- `2L`: for dileptonic ttbar decays
- `incl`: for inclusive ttbar decays

**Example:**
```
cd $production
python3 ../POWHEG-MC-Event-generation/run.py -w ./test__r1.0_f1.0_m172.5_p320900 -S 4 -n 1000 -N 1000 --decay 2L -f
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
mv test__r1.0_f1.0_m172.5_p320900 /eos/user/n/nplastir/ttH/MCProduction/production_test/

cd $base/POWHEG-BOX-RES/ttbb
mv run__test__r1.0_f1.0_m172.5_p320900 /eos/user/n/nplastir/ttH/MCProduction/POWHEG-BOX-RES/ttbb/
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
