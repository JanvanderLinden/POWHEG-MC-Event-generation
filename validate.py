import os
import sys
import glob
    
def check_stage_output(settings, nbatches, stage, iteration, workdir, any_exist=False):
    unique_files = []
    if stage==1 and iteration==1:
        expected_files = [
            "pwg-{jobid:04d}-xg1-stat.dat",
            "pwgcounters-st1-{jobid:04d}.dat",
            "pwg-xg1-xgrid-btl-{jobid:04d}.dat",
            "pwg-xg1-xgrid-rm-{jobid:04d}.dat"
            ]
    elif stage==1 and iteration>1:
        expected_files = [
            f"pwg-{{jobid:04d}}-xg{iteration}-stat.dat",
            f"pwg-xg{iteration}-xgrid-btl-{{jobid:04d}}.dat",
            f"pwg-xg{iteration}-xgrid-rm-{{jobid:04d}}.dat",
            f"pwg-xg{iteration}-xgrid-btl-{{jobid:04d}}.top",
            f"pwg-xg{iteration}-xgrid-rm-{{jobid:04d}}.top"
            ]
    elif stage==2:
        expected_files=[
            "pwg-st2-xgrid-btl-{jobid:04d}.top",
            "pwggrid-btl-{jobid:04d}.dat",
            "pwgbtlupb-{jobid:04d}.dat",
            "pwg-st2-xgrid-rm-{jobid:04d}.top",
            "pwgrmupb-{jobid:04d}.dat",
            "pwggrid-rm-{jobid:04d}.dat",
            "pwg-{jobid:04d}-st2-stat.dat",
            "pwgcounters-st2-{jobid:04d}.dat"
            ]
    elif stage==3:
        expected_files=[
            "pwgubound-{jobid:04d}.dat",
            "pwg-{jobid:04d}-st3-stat.dat",
            "pwgcounters-st3-{jobid:04d}.dat"
            ]
        unique_files = [
            "pwgfullgrid-btl-{jobid:04d}.dat",
            "pwgfullgrid-rm-{jobid:04d}.dat",
            "mint_upb_btlupb_rat.top",
            "mint_upb_btlupb.top",
            "mint_upb_rmupb.top",
            "pwghistnorms.top",
            "pwgborngrid-stat.dat"
            ]
    elif stage==4:
        expected_files = [
            "pwgevents-{jobid:04d}.lhe",
            "pwg-{jobid:04d}-st4-stat.dat",
            "pwgcounters-st4-{jobid:04d}.dat",
            #"pwgboundviolations-{jobid:04d}.dat"
            ]
    else:
        expected_files=[]
    
    missing_ids = []
    for n in range(nbatches):
        for f in expected_files:
            f_formatted = f.format(jobid=n)
            f_dir = os.path.join(settings['run_dir'], f_formatted)
            if os.path.exists(f_dir) and any_exist:
                # any_exist --> return true as soon as one file exists
                return True, []
            if not os.path.exists(f_dir) and not any_exist:
                #print(f_formatted)
                # all_exist --> return list of missing files
                missing_ids.append(n)

    if any_exist:
        # any_exist --> return false if none exist here
        return False, []    
    elif len(missing_ids) > 0:
        # all_exist --> return true if all exist
        return False, list(sorted(set(missing_ids)))
    
    # check for unique files (only relevant for all_exist checks
    missing_unique = []
    for f in unique_files:
        found = False
        for n in range(nbatches):
            f_formatted = f.format(jobid=n)
            f_dir = os.path.join(settings['run_dir'], f_formatted)
            if os.path.exists(f_dir):
                found = True
                break
        if not found:
            missing_unique.append(f)
    if len(missing_unique) > 0:
        print(f"Missing the following unique output files:\n\t{missing_unique}")
        return False, []
    else:
        return True, []
