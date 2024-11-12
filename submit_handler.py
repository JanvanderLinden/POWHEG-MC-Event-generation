import sys
import os

from make_seeds import make_seeds

batch_shell_template = """#!/bin/bash
echo "Running batch job number $1"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
alias cd='cd -P'

startdir=$PWD
cd {cmssw_base}
eval `scramv1 runtime -sh`
cd $startdir
echo 'CMSSW initialized'

#add the LHAPDF library path to PATH
PATH=$PATH:/cvmfs/cms.cern.ch/slc6_amd64_gcc630/external/lhapdf/6.2.1-fmblme/bin/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/cms.cern.ch/slc6_amd64_gcc630/external/lhapdf/6.2.1-fmblme/bin/
#add the FASTJET library path to PATH
PATH=$PATH:/cvmfs/cms.cern.ch/slc6_amd64_gcc630/external/fastjet/3.1.0/bin/
echo 'POWHEG initialized'

# running powheg
cd {run_dir}
"""

submitTemplate = """
universe = vanilla
max_retries = 3
retry_until = ExitCode == 0
request_cpus = 4
JobBatchName = {batchname}
+JobFlavour = {runtime}
executable = {arg}
arguments = $(ProcId)
initialdir = {dir}/{shell_name}
error  = {dir}/{shell_name}/run_$(Cluster)_$(ProcId).err
log    = {dir}/{shell_name}/run_$(Cluster)_$(ProcId).log
output = {dir}/{shell_name}/run_$(Cluster)_$(ProcId).out
run_as_owner = true
requirements = (Arch == "X86_64") && ( (OpSysAndVer =?= "AlmaLinux9") || (OpSysAndVer =?= "CentOS7") )
MY.WantOS    = "el7"
queue {n}
"""

def submit_handler(settings, nbatches, stage, iteration, nevt, ttbardecay, workdir, finalization=False):
    run_dir = settings["run_dir"]
    seed_file = make_seeds(nbatches, run_dir)

    if stage==4:
        # copy rwl file
        cmd = f"cp {settings['pwg-rwl']} {settings['run_dir']}"
        os.system(cmd)

    # copy powheg.input file and adjust for the current stage
    input_file = os.path.join(settings['run_dir'], 'powheg.input')
    cmd = f"cp {settings['powheg.input']} {input_file}"
    os.system(cmd)
    # add stage to input file
    n_lines = 6
    if int(stage) < 5: # different for decay stage
        cmd = f'echo "parallelstage {stage}" >> {input_file}'
        os.system(cmd)
        cmd = f'echo "xgriditeration {iteration}" >> {input_file}'
        os.system(cmd)
        n_lines += 2
    cmd = f'echo "numevts {nevt}" >> {input_file}'
    os.system(cmd)
    # add ttbar decay information and nevents per job to powheg config
    if int(stage) == 4:
        # cmd = f'echo "numevts {nevt}" >> {input_file}'
        # os.system(cmd)
        # ttdecay
        if ttbardecay == "0L":
            decay_id = "00022"
        elif ttbardecay == "1L":
            decay_id = "11111"
        elif ttbardecay == "2L":
            decay_id = "22200"
        else: #incl
            decay_id = "22222"
        cmd = f'echo "topdecaymode {decay_id}" >> {input_file}'
        os.system(cmd)
        n_lines += 2
        if ttbardecay == "1L":
            cmd = f'echo "semileptonic 1" >> {input_file}'
            os.system(cmd)
            n_lines += 1

    print("The following configuration is now in the powheg.input file:\n")
    os.system(f"tail -n {n_lines} {input_file}")

    # generate a shell script for the batch submit
    cmssw_base = os.path.join(os.environ["CMSSW_BASE"], "src")
    
    shell_code = batch_shell_template.format(
        cmssw_base=cmssw_base, run_dir=run_dir)

    if int(stage)==5:
        # decay stage is different
        shell_code += 'jobid=$(printf "%04d" $1) \n'
        shell_code += 'echo pwgevents-${jobid}.lhe | ./../lhef_decay \n'
        shell_code += 'echo "Done with lhef_decay routine, starting to zip lhe files" \n'
        shell_code += 'echo "</LesHouchesEvents>" | gzip - | cat - >> pwgevents-${jobid}-decayed.lhe \n'
    else:
        shell_code += "echo $1 | ./../pwhg_main"

    shell_name = f"stage{stage}"
    if stage==1:
        shell_name += f"_it{iteration}"
    if stage==4:
        shell_name += f"__{ttbardecay}"

    submit_dir = os.path.join(workdir, "submit")
    if not os.path.exists(submit_dir):
        os.mkdir(submit_dir)
    log_dir = os.path.join(submit_dir, "logs")
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    if not os.path.exists(os.path.join(log_dir, shell_name)):
        os.mkdir(os.path.join(log_dir, shell_name))

    shell_path = os.path.join(submit_dir, f"{shell_name}.sh")
    with open(shell_path, "w") as f:
        f.write(shell_code)
    os.system(f"chmod u+x {shell_path}")
    print(f"\nGenerated shell file for job submission at {shell_path}")
    
    # determine runtime (HTCondor accepts arguments only with "")
    runtimes = {
        1: (86400, '"tomorrow"'),
        2: (3*86400, '"nextweek"'),
        3: (86400, '"tomorrow"'),
        4: (2*86400, '"testmatch"'),
        5: (3600, '"longlunch"'),
        }
    runtime_int, runtime_str = runtimes[stage]
    

    # write condor submit script
    submit_path = os.path.join(submit_dir, f"{shell_name}.sub")
    # setup submit code
    batch_name = f"pwhg__{shell_name}__{settings['name']}"
    code = submitTemplate.format(
        arg=os.path.abspath(shell_path),
        dir=os.path.abspath(log_dir),
        initdir=os.path.abspath(run_dir),
        runtime=runtime_str,
        shell_name=shell_name,
        batchname=batch_name,
        n=nbatches)

    with open(submit_path, "w") as f:
        f.write(code)
    print(f"Generated submit script at {submit_path}")
    
    # submitting
    print(f"Submitting...")
    cmd = f"condor_submit {submit_path}"
    os.system(cmd)

