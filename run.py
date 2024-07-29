import sys
import os
import yaml

import optparse
parser = optparse.OptionParser()
parser.add_option("--init", dest="init", default=False, action="store_true",
    help="If this is the first call to generate events with these setups, use the --init option to initialize directories, configs, etc.. Most of the following option do not have to be specified again after this step and are only needed for the first setup.")

init_opts = optparse.OptionGroup(parser, "Initialization Options")
init_opts.add_option("-p", dest="process", default="./POWHEG-BOX-RES/ttbb", help="path to process (only for --init)")
init_opts.add_option("-i", dest="input_file", default="./POWHEG-MC-Event-generation/ttbb_powheg_inputs/powheg.input_1L", help="path to powheg.input file to use (only for --init)")
init_opts.add_option("-t", dest="tag", default=None, help="give your generation a tag to differentiate it from other generations with the same settings (only for --init)")
init_opts.add_option("-m", dest="mass", default=172.5, help="top mass (only for --init)")
init_opts.add_option("--pdf", dest="pdf", default=320900, help="pdf set (only for --init)")
init_opts.add_option("--mur", dest="muR", default=1.0, help="muR factor (only for --init)")
init_opts.add_option("--muf", dest="muF", default=1.0, help="muF factor (only for --init)")
parser.add_option_group(init_opts)

lhe_opts = optparse.OptionGroup(parser, "LHE Options")
lhe_opts.add_option("-N", dest="nevents", default=1000, type=int, help="number of events per job")
lhe_opts.add_option("-d","--decay",dest="ttbar_decay_channel", default=None, help="speficy ttbar decay channel [0L/1L/2L/incl]")
lhe_opts.add_option("--process-lhe","--lhe",dest="process_lhe", default=False, action="store_true", help="process the output of the LHE step (4) after its completion")
parser.add_option_group(lhe_opts)

parser.add_option("-w", dest="workdir", default=None, help="path to workdir that is created after initialization (not needed for --init)")
parser.add_option("-S", dest="stage", default=1, help="parallel stage to run")
parser.add_option("-X", dest="iteration", default=1, help="iteration to run (relevant for stage 1)")
parser.add_option("-n", dest="nbatches", default=1000, help="number of batches")
parser.add_option("--force","-f", dest="force", default=False, action="store_true", help="force re-execution ")
parser.add_option("--validate","-v", dest="validate", default=False, action="store_true", help="Validate the specified stage/iteration")
(opts, args) = parser.parse_args()

if opts.process_lhe: 
    # set stage 4 and validate flags for LHE processing
    opts.stage = 4
    opts.validate = True
elif int(opts.stage) == 4:
    # make sure a ttbar decay channel is specified
    if opts.ttbar_decay_channel is None:
        raise ValueError(
            f"Need to specify a ttbar decay channel for LHE production [0L/1L/2L/incl]")
    elif not opts.ttbar_decay_channel in ["0L", "1L", "2L", "incl"]:
        raise ValueError(
            f"Invalid choice for ttbar decay channel ({opts.ttbar_decay_channel}). The options are [0L/1L/2L/incl]")

# Initialize in first call
if opts.init:
    print("\n##################\n  INITIALIZATION  \n##################\n")
    # check validity of some options:
    if not os.path.exists(opts.input_file):
        raise ValueError(
            f"Input file\n  {opts.input_file}\ndoes not exist")
    if not os.path.exists(opts.process):
        raise ValueError(
            f"Process directory\n  {opts.process}\nin POWHEG-BOX-RES does not exist")

    # determine workdir
    dir_name = f"r{opts.muR}_f{opts.muF}_m{opts.mass}_p{opts.pdf}"
    if opts.tag:
        dir_name = f"{opts.tag}__{dir_name}"

    dir_path = os.path.abspath(os.path.join(".", dir_name))
    if os.path.exists(dir_path):
        raise ValueError(
            f"Working directory\n  ./{dir_name}\nalready exists. If you want to re-initalize this setup delete the directory first to avoid overwriting existing working directories by accident")

    # determine workdir in powheg box
    run_name = f"run__{dir_name}"
    run_dir = os.path.abspath(os.path.join(opts.process, run_name))
    if os.path.exists(run_dir):
        raise ValueError(
            f"Run directory\n  {run_dir}\nalready exists. If you want to re-initalize this setup delete the directory first to avoid overwriting existing event generation by accident")

    print(f"\nCreating working directory at ./{dir_name}")
    os.mkdir(dir_path)
    print(f"\nCreating run directory at {run_dir}")
    os.mkdir(run_dir)

    # copy powheg input
    powheg_input_path = os.path.join(dir_path, "powheg.input")
    print(f"\nCopying powheg input file to working directory:\n\t{powheg_input_path}")
    os.system(f"cp {opts.input_file} {powheg_input_path}")

    # get pwg-rwl
    rwl_input_path = os.path.join(os.path.dirname(opts.input_file), f"pwg-rwl.dat_{opts.pdf}")
    if not os.path.exists(rwl_input_path):
        print(f"ERROR: pwg_rwl.dat file does not exist, expect it to be at\n\t{rwl_input_path}\nto match the given pdf set {opts.pdf}")
        exit()
    rwl_path = os.path.join(dir_path, "pwg-rwl.dat")

    # modify the rwl file according to the scale settings
    with open(rwl_input_path, "r") as f:
        lines = f.readlines()
    new_file = []
    in_head = False
    for l in lines:
        new_l = l
        if in_head:
            # modify header lines
            if "renscfact" in l and "facscfact" in l:
                new_l = []
                for elem in l.split(" "):
                    if "renscfact=" in elem or "facscfact" in elem:
                        sc, val = elem.split("=")
                        val = val.replace("d0","").replace("d",".")
                        try:
                            val = float(val)
                        except:
                            raise ValueError(f"Cannot convert {val} to float in line {l}")
                        if "rensc" in sc:
                            val *= float(opts.muR)
                        elif "facsc" in sc:
                            val *= float(opts.muF)

                        if val < 1.0:
                            val = f"{val}d0"
                        else:
                            val = str(val).replace(".", "d")
                        new_l.append(f"{sc}={val}")
                    else:
                        new_l.append(elem)
                new_l = " ".join(new_l)
                print(new_l.strip())

        if "name='scale_variation'" in l:
            # enter header
            print("\nModifying scale settings in pwg-rwl file...")
            in_head = True
        if "</weightgroup>" in l: 
            # leave header
            in_head = False
        new_file.append(new_l)

    with open(rwl_path, "w") as f:
        f.write("".join(new_file))
    print(f"\nWrote rwl input file to working directory:\n\t{rwl_path}\n")


    # generate a yml file with all settings
    settings = {
        "mass": float(opts.mass),
        "pdf": int(opts.pdf),
        "muR": float(opts.muR),
        "muF": float(opts.muF),
        "tag": opts.tag,
        "powheg.input": powheg_input_path,
        "pwg-rwl": rwl_path,
        "run_dir": run_dir,
        "name": dir_name,
        "stage1": False,
        "stage1_it": 0,
        "stage2": False,
        "stage3": False,
        "stage4": False,
        "stage5": False
        }
    yaml_file = os.path.join(dir_path, "settings.yml")
    with open(yaml_file, "w") as yf:
        yaml.dump(settings, yf, default_flow_style=False, indent=4)
    print(f"\nSaved settings in yaml file: {yaml_file}")
    print(settings)
    
    # adding the settings to the powheg input file
    cmd = f'echo "topmass {opts.mass}" >> {powheg_input_path}'
    os.system(cmd)
    cmd = f'echo "lhans1 {opts.pdf}" >> {powheg_input_path}'
    os.system(cmd)
    cmd = f'echo "lhans2 {opts.pdf}" >> {powheg_input_path}'
    os.system(cmd)
    cmd = f'echo "renscfact {opts.muR}" >> {powheg_input_path}'
    os.system(cmd)
    cmd = f'echo "facscfact {opts.muF}" >> {powheg_input_path}'
    os.system(cmd)
    print("\nAdded the pdf, topmass and scale settings to the powheg input file:")
    os.system(f"tail -n 5 {powheg_input_path}")

    print(f"\nIntialization is done, you can now start with the first processing stage. For this, run the submit command with the following arguments:")
    print(f"\n-w ./{dir_name} -S 1 -X 1 -n NBATCHES\n")
    print(f"This command submits NBATCHES condor jobs for parallelstage=1 and xgriditeration=1")
    
    exit()

# run the actual submit after successful initialization
# check that all necessary files and paths exist
if not os.path.exists(opts.workdir):
    raise ValueError(
        f"Working directory\n  {opts.workdir}\ndoes not exist")
settings_path = os.path.abspath(os.path.join(opts.workdir, "settings.yml"))
if not os.path.exists(settings_path):
    raise ValueError(
        f"Settings file in workdir\n  {settings_path}\ndoes not exist")
# read yaml file
with open(settings_path, "r") as yf:
    settings = yaml.full_load(yf)

powheg_input_path = settings["powheg.input"]
if not os.path.exists(powheg_input_path):
    raise ValueError(
        f"Powheg input file in workdir\n  {powheg_input_path}\ndoes not exist")

run_dir = settings["run_dir"]
if not os.path.exists(run_dir):
    raise ValueError(
        f"Run directory\n  {run_dir}\ndoes not exist")

# check if the requested stage has already been run
if opts.stage == "decay": 
    opts.stage = "5"
    print(f"You chose stage 'decay' which will be referred to as stage '5' internally.")
if int(opts.stage) in [1,2,3,4,5]:
    stage_status = settings[f"stage{opts.stage}"]
    if stage_status and not opts.force:
        print(f"\nParallelstage {opts.stage} has already been run for this setup. If you want to force a re-run, please re-execute this command and add the flag '--force'.")
        exit()
    if int(opts.stage) == 1:
        it_status = settings[f"stage1_it"]
        if it_status < int(opts.iteration)-1 and not opts.force:
            val = "NONE" if it_status == 0 else f"X={it_status}"
            print(f"\nThe last validated iteration is {val} and you requested X={opts.iteration}. Make sure this is what you want to do, or adjust the requested iteration. You can force the iteration you requested by re-executing this command and adding the flag '--force' or validate the previous iteration via '--validate'.")
            exit()
    else:
        last_stage_valid = settings[f"stage{int(opts.stage)-1}"]
        if (not last_stage_valid) and not (opts.force or opts.validate):
            print(f"\nYou requested to run stage S={opts.stage}, but the last stage has not yet been validated. You can validate the previous stage by appending '--validate' to the submit command of the previous stage to register its succesful completion. You can also force the execution of your current stage by re-executing the command and adding the flag '--force'.")
            exit()

from validate import check_stage_output
if opts.validate:
    print(f"Validating output of stage={opts.stage}, iteration={opts.iteration}...")
    # validate stage
    all_exist, missing_ids = check_stage_output(
        settings=settings,
        nbatches=int(opts.nbatches),
        stage=int(opts.stage),
        iteration=int(opts.iteration),
        workdir=opts.workdir,
        )
    if not all_exist:
        print(f"Not all files were found in output directory\n\t{settings['run_dir']}")
        print(f"List of jobids with missing files: {missing_ids}")
        if not opts.force:
            print(f"Validation unsuccessful, exiting.")
            exit()
    else:
        print(f"Validation successful, changing status in workdir...")
        if not opts.process_lhe:
            if int(opts.stage)==1:
                settings[f"stage1_it"] = int(opts.iteration)
                if int(opts.iteration) >= 3:
                    settings[f"stage{opts.stage}"] = True
                else:
                    print(f"Please proceed with the next xgriditeration before the next stage.")
            else:
                settings[f"stage{opts.stage}"] = True

            with open(settings_path, "w") as yf:
                yaml.dump(settings, yf, default_flow_style=False, indent=4)
            print(f"You can now proceed with the next stage.")
            exit()
    
else:
    # check if the output of the requested stage is already available
    any_exist, _ = check_stage_output(
        settings=settings,
        nbatches=int(opts.nbatches),
        stage=int(opts.stage),
        iteration=int(opts.iteration),
        workdir=opts.workdir,
        any_exist=True
        )
    if any_exist and not opts.force:
        print(f"\nFound output files of stage={opts.stage}, it={opts.iteration} in output directory\n\t{settings['run_dir']}")
        query = input(f"Stop execution (stop/quit/s/q/n) or delete old files (delete/del/d/y)? ")
        if query[0].lower() in ["d","y"]:
            print("Deleting old files...")
            # TODO
            print("not yet implemented ..")
            exit()
        else:
            print("Exiting.") 
        exit()

if opts.process_lhe:
    from lhe_postprocess import lhe_postprocess
    # make new lhe directory in working area
    lhe_dir = os.path.join(opts.workdir, "lhe")
    if not os.path.exists(lhe_dir):
        os.mkdir(lhe_dir)
    v = 1
    while os.path.exists(os.path.join(lhe_dir, f"v{v}")):
        v += 1
    out_dir = os.path.abspath(os.path.join(lhe_dir, f"v{v}"))
    os.mkdir(out_dir)
    lhe_postprocess(
        settings=settings,
        out_dir=out_dir
        )
    exit()

## TODO validation
## TODO validate that the number of batches matches the previous iteration
from submit_handler import submit_handler
submit_handler(
    settings=settings,
    nbatches=int(opts.nbatches),
    stage=int(opts.stage),
    iteration=int(opts.iteration),
    nevt=int(opts.nevents),
    ttbardecay=opts.ttbar_decay_channel,
    workdir=opts.workdir,
    finalization=False
    )

