# -*- coding: utf-8 -*-

import re
import os
import pickle
import numpy as np
import pylab as pl
from clawpack.visclaw.data import ClawPlotData

def parse_runs(runsDir, nGauges, times):
    runDirs = os.listdir(runsDir)
    runs_data = dict()
    for runDir in runDirs:
        n = int(re.search('\\D*(\\d+)', runDir).group(1))
        runs_data[n] = parse_run(runsDir+'/'+runDir, nGauges, times)
        
    # switch the results so they are aggregated by value type first
    results = dict()
    if len(runs_data) > 0:
        n_values = runs_data.keys()
        value_names = runs_data[n_values[0]].keys()
        for name in value_names:
            results[name] = dict()
            for n in n_values:
                results[name][n] = runs_data[n][name]
    return results
    
    
def parse_run(runDir, nGauges, times):
    run_data = read_log(runDir)
    run_data['gauge_data'] = read_gauges(runDir, nGauges, times)
    return run_data

def read_gauges(runDir, nGauges, times):
    plotdata = ClawPlotData()
    plotdata.outdir = runDir+'/_output'   # set to the proper output directory
    
    gauge_data = []
    for ii in range(0,nGauges):
        g = plotdata.getgauge(ii)
        time_indices = np.array([any(np.isclose(t, times)) for t in g.t])
        gauge_data.append(g.q[0, time_indices])
    
    gauge_data = np.array(gauge_data)
    return gauge_data
    

def read_log(runDir, nlevels=3):
    log_file = open(runDir+'/output.log')
    log_text = log_file.read()
    log_file.close()
    
    result = dict()
    result['total_time'] = float(re.search(
                                'Total time to solution\\s*=\\s*(\\d*.\\d+) s',
                                 log_text).group(1))
    result['update_time'] = float(re.search(
                                'Total updating\\s+time\\s*(\\d*.\\d+) s',
                                 log_text).group(1))
    result['valout_time'] = float(re.search(
                                'Total valout\\s+time\\s*(\\d*.\\d+) s',
                                 log_text).group(1))
    result['regrid_time'] = float(re.search(
                                'Total regridding\\s+time\\s*(\\d*.\\d+) s',
                                 log_text).group(1))
    grid_time = 0
    levels_time = {}
    levels_cells = {}
    for ii in range(1, nlevels+1):
        lTime = re.search('Total advanc time on level'+\
                                 '\\s+'+str(ii)+'\\s*=\\s*(\\d*.\\d+) s',
                                 log_text)
        if lTime:
            levels_time[ii] = float(lTime.group(1))
            grid_time += levels_time[ii]
        cell_matches = re.finditer('\\d* grids with\\s+(\\d+) cells'+\
                                    ' at level\\s*'+str(ii), log_text)
        nCells = []
        for match in cell_matches:
            nCells.append(int(match.group(1)))
        if len(nCells) > 0:
            levels_cells[ii] = nCells
    result['grid_time'] = grid_time
    result['levels_time'] = levels_time
    result['levels_cells'] = levels_cells
    return result
  
def l1_norm(gauge_data):
    return np.sum(np.absolute(gauge_data))
    
def rel_err(ref_data, data):
    return l1_norm(ref_data - data) / l1_norm(ref_data)

def add_rel_err(runs_results, ref_run):
    ref_data = ref_run['gauge_data']
    runs_data = runs_results['gauge_data']
    err_data = {n:rel_err(ref_data, data) for (n, data) in runs_data.items()}
    runs_results['rel_err'] = err_data

def plot_rel_err(results):
    err_data = results['rel_err']
    x = sorted(err_data.keys())
    y = [err_data[n] for n in x]
    pl.figure()
    pl.plot(x,y, 'bo')
    pl.ylabel('L1 error')
    pl.xlabel('regridding interval')
    
def plot_times(results):
    grid_data = results['grid_time']
    regrid_data = results['regrid_time']
    update_data = results['update_time']
    x = sorted(grid_data.keys())
    grid_t   = np.array([grid_data[n] for n in x])
    regrid_t = np.array([regrid_data[n] for n in x])
    update_t = np.array([update_data[n] for n in x])
    pl.figure()
    pl.subplot(2,1,1)
    pl.plot(x,grid_t, 'bo', label='time on grids')
    pl.plot(x,regrid_t, 'rx', label='regrid time')
    pl.plot(x,update_t, 'g.', label='update time')
    pl.legend(loc='best', fontsize=10)
    pl.ylabel('time (s)')
    pl.subplot(2,1,2)
    pl.plot(x,regrid_t, 'rx', label='regrid time')
    pl.plot(x,update_t, 'g.', label='update time')
    pl.legend(loc='best', fontsize=10)
    pl.ylabel('time (s)')    
    pl.xlabel('regridding interval')

def plot_fraction_times(results, ref_data):
    grid_data   = results['grid_time']
    regrid_data = results['regrid_time']
    update_data = results['update_time']
    x = sorted(grid_data.keys())
    ref_time = ref_data['grid_time']
    comp_time   = np.array([grid_data[n]+regrid_data[n]+update_data[n] for n in x])
    pl.figure()
    pl.plot(x, comp_time / ref_time, 'bo')
    pl.ylabel('ratio of times')
    pl.xlabel('regridding interval')

def plot_avg_cells(results, ratios=[2, 2]):
    cell_data = results['levels_cells']
    x = sorted(cell_data.keys())
    ncells_1 = np.array([float(cell_data[n][1][0]) for n in x])  #float to avoid integer div later
    cells_2 = [cell_data[n][2] for n in x]
    ncells_2 = np.array([sum(cells) / len(cells) for cells in cells_2])
    cells_3 = [cell_data[n][3] for n in x]
    ncells_3 = np.array([sum(cells) / len(cells) for cells in cells_3])
    pl.figure()
    pl.plot(x, ncells_2 / (ncells_1 * ratios[0]**2), 'bo', label='level 2')
    pl.plot(x, ncells_3 / (ncells_1 * ratios[0]**2 * ratios[1]**2), 'k^', label='level 3')
    pl.legend(loc='best', fontsize=10)
    pl.ylabel('fraction of domain')
    pl.xlabel('regridding interval')
    pl.ylim(0,1.1)
    pl.grid()

def plot_cells(results, n=2, ratios=[2,2]):
    cell_data = results['levels_cells'][n]
    level_1 = float(cell_data[1][0])  #float to avoid integer division later
    level_2 = np.array(cell_data[2])
    x_2 = np.linspace(0, 1, len(level_2)+1)[0:(-1)]
    level_3 = np.array(cell_data[3])
    x_3 = np.linspace(0, 1, len(level_3)+1)[0:(-1)]
    pl.figure()
    pl.step(x_2, level_2 / (level_1 * ratios[0]**2), 'b-', label='level 2', where='post')
    pl.step(x_3, level_3 / (level_1 * ratios[0]**2 * ratios[1]**2), 'g-', label='level 3', where='post')
    pl.xlim(0,1)
    pl.ylim(0,1.1)
    pl.grid()
    pl.legend(loc='best', fontsize=10)
    pl.xlabel('time')
    pl.ylabel('fraction of domain')

if __name__ == '__main__':
    reread_data = False   # if true, read from data files again, otherwise
                        # import parsed data from saved pickle files
    euler_times = np.linspace(0.,0.8,17)
    advec_times = np.linspace(0.,2.,21)
    nGauges = 25
    if reread_data:
        euler_data = parse_runs('euler_basic_runs', nGauges, euler_times)
        bad_euler_data = parse_runs('euler_bad_runs', nGauges, euler_times)
        euler_ref = parse_run('euler_base', nGauges, euler_times)
        advec_data = parse_runs('advection_basic_runs', nGauges, advec_times)
        bad_advec_data = parse_runs('advection_bad_runs', nGauges, advec_times)
        advec_ref = parse_run('advection_base', nGauges, advec_times)
        with open('euler_data.pkl', 'wb') as f:
            pickle.dump(euler_data, f)
        with open('bad_euler_data.pkl', 'wb') as f:
            pickle.dump(bad_euler_data, f)
        with open('euler_ref.pkl', 'wb') as f:
            pickle.dump(euler_ref, f)
        with open('advec_data.pkl', 'wb') as f:
            pickle.dump(advec_data, f)
        with open('bad_advec_data.pkl', 'wb') as f:
            pickle.dump(bad_advec_data, f)
        with open('advec_ref.pkl', 'wb') as f:
            pickle.dump(advec_ref, f)
    else:
        with open('euler_data.pkl', 'rb') as f:
            euler_data = pickle.load(f)
        with open('bad_euler_data.pkl', 'rb') as f:
            bad_euler_data = pickle.load(f)
        with open('euler_ref.pkl', 'rb') as f:
            euler_ref = pickle.load(f)
        with open('advec_data.pkl', 'rb') as f:
            advec_data = pickle.load(f)
        with open('bad_advec_data.pkl', 'rb') as f:
            bad_advec_data = pickle.load(f)
        with open('advec_ref.pkl', 'rb') as f:
            advec_ref = pickle.load(f)

    add_rel_err(euler_data, euler_ref)
    add_rel_err(bad_euler_data, euler_ref)
    add_rel_err(advec_data, advec_ref)
    add_rel_err(bad_advec_data, advec_ref)
    

    plot_rel_err(advec_data)
    pl.savefig('l1_err_advec.pdf')
    plot_rel_err(euler_data)
    pl.savefig('l1_err_euler.pdf')
    plot_rel_err(bad_advec_data)
    pl.savefig('l1_err_advec_bad.pdf')
    plot_rel_err(bad_euler_data)
    pl.savefig('l1_err_euler_bad.pdf')
    pl.close('all')
    
    plot_times(advec_data)
    pl.savefig('time_advec.pdf')
    plot_times(euler_data)
    pl.savefig('time_euler.pdf')
    plot_times(bad_advec_data)
    pl.savefig('time_advec_bad.pdf')
    plot_times(bad_euler_data)
    pl.savefig('time_euler_bad.pdf')
    
    plot_fraction_times(advec_data, advec_ref)
    pl.savefig('rel_time_advec.pdf')
    plot_fraction_times(bad_advec_data, advec_ref)
    pl.savefig('rel_time_advec_bad.pdf')
    plot_fraction_times(euler_data, euler_ref)
    pl.savefig('rel_time_euler.pdf')
    plot_fraction_times(bad_euler_data, euler_ref)
    pl.savefig('rel_time_euler_bad.pdf')
    pl.close('all')

    plot_avg_cells(advec_data, [2, 2])
    pl.savefig('avg_cells_advec.pdf')
    plot_avg_cells(bad_advec_data, [2, 2])
    pl.savefig('avg_cells_advec_bad.pdf')
    plot_avg_cells(euler_data, [2, 4])
    pl.savefig('avg_cells_euler.pdf')
    pl.close('all')

    for ii in range(1,11,1):
        plot_cells(advec_data, ii, [2, 2])
        pl.savefig('cells_advec_'+str(ii)+'.pdf')
        plot_cells(bad_advec_data, ii, [2, 2])
        pl.savefig('cells_advec_bad_'+str(ii)+'.pdf')
    pl.close('all')

    for ii in range(4,10,2):  #something is wrong with parsing the data for 2
        plot_cells(bad_euler_data, ii, [2, 4])
        pl.savefig('cells_euler_bad_'+str(ii)+'.pdf')
    pl.close('all')

    for ii in range(2,12,2):
        plot_cells(euler_data, ii, [2, 4])
        pl.savefig('cells_euler_'+str(ii)+'.pdf')
    pl.close('all')
