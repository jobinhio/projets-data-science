
import sys
import pytest
import feelpp as feelpp 
import feelpp.quality as q
import feelpp.toolboxes.core as tb
import feelpp.interpolation as I
from feelpp.toolboxes.fluid import *


@pytest.mark.order("first")
def test_fluid1():
    feelpp.Environment.setConfigFile('cfd1.cfg')
    # 2D fluid solver using P2P1G1 approximation
    f = fluid(dim=2, orderVelocity=2, orderPressure=1,worldComm=feelpp.Environment.worldCommPtr())
    simulate(f)

#@pytest.mark.order("second")
#def test_fluid2_remesh():
##    feelpp.Environment.setConfigFile('fluid/TurekHron/cfd3.cfg')
#    #feelpp.Environment.setConfigFile('fluid/swimmers/3-sphere/2d/three_sphere_2D.cfg')
#    #feelpp.Environment.setConfigFile('fluid/moving_body/gravity/cfd.cfg')
#    feelpp.Environment.setConfigFile(
#        'fluid/moving_body/gravity/cylinder_under_gravity/cylinder_under_gravity.cfg')
#    f = fluid(dim=2, orderVelocity=2, orderPressure=1)
#    f.init()
#
#    f.exportResults()
#    f.startTimeStep()
#    while not f.timeStepBase().isFinished():
#
#        if f.timeStepBase().iteration() % 4 == 0:
#            hfar=0.1
#            hclose=0.02
#            Xh = feelpp.functionSpace(mesh=f.mesh())
#            metric = feelpp.gradedls(Xh, feelpp.markedfaces(
#                Xh.mesh(), ["CylinderSurface"]), hclose, hfar)
#            R = feelpp.remesher(mesh=f.mesh(),required_elts="CylinderVolume",required_facets="CylinderSurface")
#            R.setMetric(metric)
#            new_mesh = R.execute()
#            f.applyRemesh(new_mesh)
#
#        if feelpp.Environment.isMasterRank():
#            print("============================================================\n")
#            print("time simulation: ", f.time(), "s \n")
#            print("============================================================\n")
#
#        f.solve()
#        f.exportResults()
#        f.updateTimeStep()
#

print('test')
