import sys
import salome

salome.salome_init()
import salome_notebook
notebook = salome_notebook.NoteBook()

###
### GEOM component
###

import GEOM
from salome.geom import geomBuilder
import math
import SALOMEDS


geompy = geomBuilder.New()

gg = salome.ImportComponentGUI("GEOM")

O = geompy.MakeVertex(0, 0, 0)
OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)

# We create an annulus with r=90 and R=100
# To do that we create two circles of radius 100 and 90
Circle_1 = geompy.MakeCircle(O, OZ, 100)
Circle_2 = geompy.MakeCircle(O, OZ, 90)

# We create two faces from the two circles, we get two disks Face_1 (radius = 100) and Face_2 (radius = 90)
Face_1 = geompy.MakeFaceWires([Circle_1], 1)
Face_2 = geompy.MakeFaceWires([Circle_2], 1)

# We make the boolean operation to get the annulus (Face_1 - Face_2)
Cut_1 = geompy.MakeCutList(Face_1, [Face_2], True)

# Now we can create one blade of the fan, to do that we extrude the annulus along a line
# We create a vertex at the end of the line, the coordinates of the vertex are (0, -50, 30)
Vertex_1 = geompy.MakeVertex(0, -50, 30)

# We create the line
Line_1 = geompy.MakeLineTwoPnt(O, Vertex_1)

# We extrude the annulus along the line
Pipe_1 = geompy.MakePipe(Cut_1, Line_1)

# We can now create the fan by rotating the blade 3 times
# First, we need to translate the blade to the center of the rotation
geompy.TranslateDXDYDZ(Pipe_1, 50, 0, 0)

# We create the 3 blades by rotating the blade 120° around the Z axis
Pipe_2 = geompy.MakeRotation(Pipe_1, OZ, -120*math.pi/180.0)
Pipe_3 = geompy.MakeRotation(Pipe_1, OZ, 120*math.pi/180.0)

# The result gives us 3 blades intersecting each other, we need to cut them and remove what's inside the fan
# We create the 3 blades intersections
Pipe_1_and_Pipe_2 = geompy.MakeCommonList([Pipe_1, Pipe_2], True)
Pipe_1_and_Pipe_3 = geompy.MakeCommonList([Pipe_1, Pipe_3], True)
Pipe_2_and_Pipe_3 = geompy.MakeCommonList([Pipe_2, Pipe_3], True)

# We remove the intersection from the blades
Pipe_1_less_Pipe_2_and_Pipe_3 = geompy.MakeCutList(Pipe_1, [Pipe_1_and_Pipe_2, Pipe_1_and_Pipe_3], True)

# We explode the 3 blades to get 3 solids (+1 which corresponds to the outside of the fan)
[Solid_7, Solid_8, Solid_9] = geompy.MakeBlockExplode(Pipe_1_less_Pipe_2_and_Pipe_3, 6, 6)

# We do the same for the 2 other blades
Pipe_2_less_Pipe_1_and_Pipe_3 = geompy.MakeCutList(Pipe_2, [Pipe_1_and_Pipe_2, Pipe_2_and_Pipe_3], True)
[Solid_4, Solid_5, Solid_6] = geompy.MakeBlockExplode(Pipe_2_less_Pipe_1_and_Pipe_3, 6, 6)
Pipe_3_less_Pipe_1_and_Pipe_2 = geompy.MakeCutList(Pipe_3, [Pipe_1_and_Pipe_3, Pipe_2_and_Pipe_3], True)
[Solid_1, Solid_2, Solid_3] = geompy.MakeBlockExplode(Pipe_3_less_Pipe_1_and_Pipe_2, 6, 6)

# We remove the solids inside the fan
Cut_2 = geompy.MakeCutList(Pipe_3_less_Pipe_1_and_Pipe_2, [Solid_1, Solid_2, Solid_3], True)
Cut_3 = geompy.MakeCutList(Pipe_2_less_Pipe_1_and_Pipe_3, [Solid_4, Solid_5, Solid_6], True)
Cut_4 = geompy.MakeCutList(Pipe_1_less_Pipe_2_and_Pipe_3, [Solid_7, Solid_8, Solid_9], True)

# We fuse the 3 blades to get the fan
Fuse_1 = geompy.MakeFuseList([Pipe_1_and_Pipe_2, Pipe_1_and_Pipe_3, Pipe_2_and_Pipe_3, Cut_2, Cut_3, Cut_4, Solid_7, Solid_8, Solid_4, Solid_5, Solid_1, Solid_3], True, True)

# We create the axle of the fan
Cylinder_1 = geompy.MakeCylinderRH(60, 30)
Cylinder_2 = geompy.MakeCylinderRH(40, 30)
Cut_5 = geompy.MakeCutList(Cylinder_1, [Cylinder_2], True)
Cut_6 = geompy.MakeCutList(Fuse_1, [Cylinder_1], True)

# We fuse the axle and the fan to create the final geometry
Fuse_2 = geompy.MakeFuseList([Cut_5, Cut_6], True, True)

# We make our creations visible in the GUI
geompy.addToStudy( O, 'O' )
geompy.addToStudy( OX, 'OX' )
geompy.addToStudy( OY, 'OY' )
geompy.addToStudy( OZ, 'OZ' )
fan = geompy.addToStudy( Fuse_2, 'Fuse_2' )

# Add geometry view
gg.createAndDisplayGO(fan)

if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
