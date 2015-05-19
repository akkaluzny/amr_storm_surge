import numpy as np
from batch import yeti
import clawpack.geoclaw.surge.data as surge

class SweepJob(yeti.YetiJob):

    def __init__(self, run_number=1, wave_tolerance=1.0, deep_depth=300.0, speed_tolerance=False):

        super(SweepJob, self).__init__(time=24*60, memory=15000)
        
        self.omp_num_threads = 16

        self.run_number = run_number
        self.type = 'sweep'
        if speed_tolerance:
            self.name = 'wave_deep_speed_l5'
        else:
            self.name = 'wave_deep_no_speed_l5'
        self.prefix = 'run_%s_wave_%s_deep_%s' % (self.run_number, wave_tolerance, deep_depth)
        self.executable = 'xgeoclaw'

        self.group = 'yetiapam'

        import setrun
        self.rundata = setrun.setrun()

        # incorporate storm parameters
        self.rundata.add_data(surge.SurgeData(), 'stormdata')
        setrun.set_storm(self.rundata)
        self.rundata.add_data(surge.FrictionData(), 'frictiondata')
        setrun.set_friction(self.rundata)
        
        ### modify setrun parameters here ###
        refine_data = self.rundata.refinement_data
        refine_data.wave_tolerance = wave_tolerance
        refine_data.deep_depth = deep_depth
        if not speed_tolerance:
            refine_data.speed_tolerance = [999999]  #big number so it never triggers

        amrdata = self.rundata.amrdata
        amrdata.amr_levels_max = 5


if __name__ == '__main__':

    jobs = []
    
    depth_values = np.arange(100., 800., 100.)
    wave_values = np.arange(0.25, 1.75, 0.25)

    ii = 1
    for depth in depth_values:
        for wave in wave_values:
            for speed in (True, False):
                jobs.append(SweepJob(ii, wave_tolerance=wave, deep_depth=depth, speed_tolerance=speed))
            ii += 1

    controller = yeti.YetiBatchController(jobs, email='akk2141@columbia.edu', output='~/tmp/output')
    controller.run()

