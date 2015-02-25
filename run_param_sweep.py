# -*- coding: utf-8 -*-

import os
import re
import time

if __name__ == '__main__':
    homeDir = '/media/tfuser/E8/code/apma4301_2014_kaluzny_andrew/Project/myclaw'
    workingDir = 'advection_test'
    sourceDir = 'advection_base'
    newName = 'advection_test'
    
    nbuff = (0, 2, 4, 6, 8, 10)
    nlevels = 3
    ncells = 50
    amr_levels = 'amrdata.amr_levels_max'
    num_cells_x = 'clawdata.num_cells[0]'
    num_cells_y = 'clawdata.num_cells[1]'
    regrid_interval = 'amrdata.regrid_interval'
    buffer_width = 'amrdata.regrid_buffer_width'
    value_string = '\\s*=\\s*\\d+'
    
    setrun_base = open(homeDir+'/'+sourceDir+'/setrun.py').read()
    setrun_base = re.sub(re.escape(amr_levels) + value_string,
                         amr_levels + ' = ' + str(nlevels) + '\n',
                         setrun_base, flags=re.MULTILINE)
    for rep_str in (num_cells_x, num_cells_y):
        setrun_base = re.sub(re.escape(rep_str) + value_string,
                         rep_str + ' = ' + str(ncells) + '\n',
                         setrun_base, flags=re.MULTILINE)
                         
    for n in nbuff:
        newDir = workingDir+'/'+newName + str(n)
        os.system('cp -r ' + homeDir+'/'+sourceDir +\
                    ' ' + homeDir+'/'+newDir)
        print 'Made directory ' + newDir
        
        setrun_text = setrun_base
        for rep_str in (regrid_interval, buffer_width):
            setrun_text = re.sub(re.escape(rep_str) + value_string,
                                 rep_str + ' = ' + str(n) + '\n',
                                 setrun_text, flags=re.MULTILINE)
        setrun_file = open(homeDir+'/'+newDir + '/setrun.py', 'w')
        setrun_file.write(setrun_text)
        setrun_file.close()
        
        print 'Running code in ' + newDir + '...'
        os.chdir(homeDir+'/'+newDir)
        start = time.time()
        os.system('make .plots > output.log')
        print 'Done. ({} s)'.format(time.time() - start)