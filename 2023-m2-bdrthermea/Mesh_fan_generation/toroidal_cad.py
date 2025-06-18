import sys
import salome

salome.salome_init()
import salome_notebook
notebook = salome_notebook.NoteBook()
sys.path.insert(0, r'C:/Users/schal/M2_CSMI/Projet/BDR_Thermea')

###
### GEOM component
###

import GEOM
from salome.geom import geomBuilder
import math
import SALOMEDS


geompy = geomBuilder.New()

O = geompy.MakeVertex(0, 0, 0)
OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)
Hub_circle_contour = geompy.MakeCircle(None, None, 12)
Hub_circle_hole = geompy.MakeCircle(None, None, 5.2)
Hub_full_12 = geompy.MakeFaceWires([Hub_circle_contour], 1)
Hub_hole_5_2 = geompy.MakeFaceWires([Hub_circle_hole], 1)
Hub_face = geompy.MakeCutList(Hub_full_12, [Hub_hole_5_2], True)
Hub = geompy.MakePrismVecH(Hub_face, OZ, 6)
Plane_1 = geompy.MakePlane2Vec(OY, OX, 2000)
geompy.TranslateDXDYDZ(Plane_1, 3, 0, 0)
Start_profile_point_1 = geompy.MakeVertex(3, -2, 1)
Start_profile_point_2 = geompy.MakeVertex(3, 2, 7)
Start_profile_control_1 = geompy.MakeVertex(3, -1.8, 2)
Start_profile_point_3 = geompy.MakeVertex(3, -1.2, 1)
Start_profile_control_3 = geompy.MakeVertex(3, -1.6, 0)
Start_profile_vector_start = geompy.MakeVector(Start_profile_point_1, Start_profile_control_1)
geompy.TranslateDXDYDZ(Start_profile_control_3, 0, -0.7, 0)
Start_profile_vector_end = geompy.MakeVector(Start_profile_point_3, Start_profile_control_3)
# Start_profile_contour = geompy.MakeInterpolWithTangents([Start_profile_point_1, Start_profile_point_2, Start_profile_point_3], Start_profile_vector_start, Start_profile_vector_end)
Start_profile_contour = geompy.MakeInterpol([Start_profile_point_1,Start_profile_control_1, Start_profile_point_2, Start_profile_point_3,Start_profile_control_3], True, False)
Start_profile_base = geompy.MakeLineTwoPnt(Start_profile_point_3, Start_profile_point_1)
Start_profile = geompy.MakeFaceWires(Start_profile_contour, 1)
End_profile = geompy.MakeTranslation(Start_profile, -6, 0, 0)
Mirror_Y = geompy.MakePlane2Vec(OX, OY, 2000)
geompy.MirrorByPlane(End_profile, Mirror_Y)
geompy.TranslateDXDYDZ(Start_profile, 2, 0, 0)
geompy.TranslateDXDYDZ(End_profile, -2, 0, 0)
Edge_profile_point_1 = geompy.MakeVertex(0, 0, 0.5)
Edge_profile_point_2 = geompy.MakeVertex(0, 0, 1.5)
Edge_profile_point_3 = geompy.MakeVertex(0, 0.5, 5)
Edge_profile_point_4 = geompy.MakeVertex(0, 1., 0.5)
Edge_profile_point_5 = geompy.MakeVertex(0, 0.5, 0)
Edge_profile_control_3 = geompy.MakeVertex(0, 0.8, 1)
Edge_profile_control_1 = geompy.MakeVertex(0, 0, 1)
Edge_profile_vector_1 = geompy.MakeVector(Edge_profile_point_1, Edge_profile_control_1)
geompy.TranslateDXDYDZ(Edge_profile_control_3, 0, 0, -2)
Edge_profile_vector_2 = geompy.MakeVector(Edge_profile_point_3, Edge_profile_control_3)
Edge_profile_contour = geompy.MakeInterpol([Edge_profile_point_1, Edge_profile_point_2, Edge_profile_point_3,Edge_profile_point_4,Edge_profile_point_5],True,False)
# Edge_profile_contour = geompy.MakeInterpolWithTangents([Edge_profile_point_1, Edge_profile_point_2, Edge_profile_point_3,Edge_profile_point_4,Edge_profile_point_5], Edge_profile_vector_1, Edge_profile_vector_2)
# Edge_profile_base = geompy.MakeLineTwoPnt(Edge_profile_point_3, Edge_profile_point_1)
Edge_profile = geompy.MakeFaceWires(Edge_profile_contour, 1)

shift_edge_profile = 108.1

geompy.TranslateDXDYDZ(Edge_profile, 0, shift_edge_profile, 0)
Plane_2 = geompy.MakePlane2Vec(OX, OY, 2000)
geompy.TranslateDXDYDZ(Plane_2, 0, 19.05, 0)
Mid_profile_2 = geompy.MakeVertex(20, 19.05, 5)

L_mid_profile = 20

Mid_profile_1 = geompy.MakeVertex(20+L_mid_profile, 19.05, 0)
Mid_profile_3 = geompy.MakeVertex(20+L_mid_profile-0.8, 19.05, 0)
Mid_profile_control_1 = geompy.MakeVertex(20+L_mid_profile-1, 19.05, 1)
Mid_profile_control_3 = geompy.MakeVertex(20+L_mid_profile+0.2, 19.05, -1)

# Mid_profile_1 = geompy.MakeVertex(40, 19.05, 0)
# Mid_profile_3 = geompy.MakeVertex(39.2, 19.05, 0)
# Mid_profile_control_1 = geompy.MakeVertex(39, 19.05, 1)
# Mid_profile_control_3 = geompy.MakeVertex(40.2, 19.05, -1)
geompy.TranslateDXDYDZ(Mid_profile_control_1, -1.5, 0, 0)
Mid_profile_vector_1 = geompy.MakeVector(Mid_profile_1, Mid_profile_control_1)
geomObj_1 = geompy.MakeMarker(0, 0, 0, 1, 0, 0, 0, 1, 0)
geompy.TranslateDXDYDZ(Mid_profile_control_3, 1.5, 0, 0)
Mid_profile_vector_2 = geompy.MakeVector(Mid_profile_3, Mid_profile_control_3)
Mid_profile_contour = geompy.MakeInterpolWithTangents([Mid_profile_1, Mid_profile_2, Mid_profile_3], Mid_profile_vector_1, Mid_profile_vector_2)
Mid_profile_base = geompy.MakeLineTwoPnt(Mid_profile_3, Mid_profile_1)

x = [0.0000000,0.0122600,0.0246300,0.0494000,0.0742600,0.0991500,0.1489800,0.1988800,0.2987800,0.3988000,0.4989000,0.5990500,0.6992199,0.7994200,0.8996900,0.9498200,1.0000000]
x_= [0.0000000,0.0126400,0.0251800,0.0502100,0.0751900,0.1001700,0.1500700,0.1999700,0.2998200,0.3997800,0.4997800,0.5998000,0.6998200,0.7998800,0.8999400,0.9499700,1.0000000]
y = [0.0000000,0.0157800,0.0249700,0.0397400,0.0491100,0.0564900,0.0680300,0.0748800,0.0813800,0.0799800,0.0732800,0.0635900,0.0519900,0.0387900,0.0208000,0.0117500,0.0000000]
y_= [0.0000000,-0.0092100,-0.0118200,-0.0142500,-0.0128700,-0.0113000,-0.0043500,0.0019000,0.0118000,0.0144000,0.0148000,0.0139500,0.0122000,0.0080000,0.0041000,0.0020500,0.0000000]

scale_factor_1 = 30
scale_factor_2 = 50

last_point = [x[-1]*scale_factor_1, y[-1]*scale_factor_2]

x_ = x_[::-1]
y_ = y_[::-1]

x += x_
y += y_

x = [i*scale_factor_1 for i in x]
y = [i*scale_factor_2 for i in y]

x = x[::2]
y = y[::2]

Mid_profile_points = []

for xs,ys in zip(x,y):
  Mid_profile_points.append(geompy.MakeVertex(xs, 0, ys))
  # geompy.addToStudy(Mid_profile_points[-1], 'Mid_profile_point_'+str(len(Mid_profile_points)))

Mid_profile_contour = geompy.MakeInterpol(Mid_profile_points, True, False)
# Rotate by 25 degrees
angle = 25*math.pi/180.0
geompy.Rotate(Mid_profile_contour, OY, angle)
rotated_last_point = [last_point[0]*math.cos(angle)-last_point[1]*math.sin(angle), last_point[0]*math.sin(angle)+last_point[1]*math.cos(angle)]
geompy.TranslateDXDYDZ(Mid_profile_contour, 0, 0, rotated_last_point[1])
print(shift_edge_profile-18.1+L_mid_profile)
geompy.TranslateDXDYDZ(Mid_profile_contour, 20+L_mid_profile, shift_edge_profile/2, 0)
Bezier_path_2 = geompy.MakeVertex(20+L_mid_profile+rotated_last_point[0], shift_edge_profile/2,0)

Mid_profile_1_1 = geompy.MakeFaceWires(Mid_profile_contour, 1)
Mirror_X = geompy.MakePlane2Vec(OY, OX, 2000)
# Mid_profile_2_1 = geompy.MakeMirrorByPlane(Mid_profile_1_1, Mirror_X)
Mid_profile_2_1 = geompy.MakeTranslation(Mid_profile_1_1, -3*(20+L_mid_profile), 0, 0)
Bezier_path_1 = geompy.MakeCDG(Start_profile)
Bezier_path_2 = geompy.MakeCDG(Mid_profile_1_1)
Bezier_path_3 = geompy.MakeCDG(Edge_profile)
Bezier_path_4 = geompy.MakeCDG(Mid_profile_2_1)
Bezier_path_5 = geompy.MakeCDG(End_profile)
# Bezier_path_4 = geompy.MakeMirrorByPlane(Bezier_path_2, Mirror_X)
# Bezier_path_3 = geompy.MakeTranslation(Edge_profile_point_5, 0, shift_edge_profile, 0)
# Bezier_path_1 = geompy.MakeTranslation(Start_profile_control_3, 2, 0, 0)
# Bezier_path_5 = geompy.MakeTranslation(Start_profile_control_3, -8, 0, 0)
geompy.MirrorByPlane(Bezier_path_5, Mirror_Y)
Bezier_curve_control_1 = geompy.MakeTranslation(Bezier_path_1, 1, 0, 0)
Bezier_curve_control_5 = geompy.MakeTranslation(Bezier_path_5, 1, 0, 0)
Vector_1 = geompy.MakeVector(Bezier_path_1, Bezier_curve_control_1)
Vector_2 = geompy.MakeVector(Bezier_path_5, Bezier_curve_control_5)
Bezier_curve_path_pipe = geompy.MakeInterpol([Bezier_path_1, Bezier_path_2, Bezier_path_3, Bezier_path_4, Bezier_path_5], False, False)
Pipe_1 = geompy.MakePipeWithDifferentSectionsBySteps([Start_profile, Mid_profile_1_1, Edge_profile, Mid_profile_2_1, End_profile], [Bezier_path_1, Bezier_path_2, Bezier_path_3, Bezier_path_4, Bezier_path_5], Bezier_curve_path_pipe)
# Pipe_1 = geompy.MakePipeWithDifferentSections([Start_profile, Mid_profile_1_1, Edge_profile, Mid_profile_2_1, End_profile], [Bezier_path_1, Mid_profile_1, Bezier_path_3, Bezier_path_4, Bezier_path_5], Bezier_curve_path_pipe,False,False)
# Pipe_2 = geompy.MakeRotation(Pipe_1, OZ, 120*math.pi/180.0)
# Pipe_3 = geompy.MakeRotation(Pipe_2, OZ, 120*math.pi/180.0)

Bezier_curve_test = geompy.MakeInterpol([Bezier_path_1, Bezier_path_2, Bezier_path_3], False, False)
Pipe_2 = geompy.MakePipeWithDifferentSections([Start_profile, Mid_profile_1_1, Edge_profile], [Bezier_path_1, Bezier_path_2, Bezier_path_3], Bezier_curve_test,False,False)
Pipe_test = geompy.MakeMirrorByPlane(Pipe_2, Mirror_X)
Bezier_test_2 = geompy.MakeInterpol([Bezier_path_3, Bezier_path_4, Bezier_path_5], False, False)
Pipe_3 = geompy.MakePipeWithDifferentSections([Edge_profile, Mid_profile_2_1, End_profile], [Bezier_path_3, Bezier_path_4, Bezier_path_5], Bezier_test_2,False,False)
Blade_1 = geompy.MakeFuseList([Pipe_2, Pipe_3], False, True)
Blade_2 = geompy.MakeRotation(Blade_1, OZ, 120*math.pi/180.0)
Blade_3 = geompy.MakeRotation(Blade_2, OZ, 120*math.pi/180.0)
Blade_1_minus_Blade_2_and_Blade_3 = geompy.MakeCutList(Blade_1, [Blade_2, Blade_3])
Blade_2_minus_Blade_1_and_Blade_3 = geompy.MakeCutList(Blade_2, [Blade_1, Blade_3])
Blade_3_minus_Blade_1_and_Blade_2 = geompy.MakeCutList(Blade_3, [Blade_1, Blade_2])

Blade_1_minus_Blade_2 = geompy.MakeCutList(Blade_1, [Blade_2])
SuppressFaces_1 = geompy.SuppressFaces(Blade_1_minus_Blade_2, [68, 82, 96, 102])
Final_Blade_1 = geompy.SuppressFaces(SuppressFaces_1, [68, 74, 80])
Final_Blade_2 = geompy.MakeRotation(Final_Blade_1, OZ, 120*math.pi/180.0)
Final_blade_3 = geompy.MakeRotation(Final_Blade_2, OZ, 120*math.pi/180.0)

geompy.addToStudy( O, 'O' )
geompy.addToStudy( OX, 'OX' )
geompy.addToStudy( OY, 'OY' )
geompy.addToStudy( OZ, 'OZ' )
geompy.addToStudy( Hub_circle_contour, 'Hub_circle_contour' )
geompy.addToStudy( Hub_circle_hole, 'Hub_circle_hole' )
geompy.addToStudy( Hub_full_12, 'Hub_full_12' )
geompy.addToStudy( Hub_hole_5_2, 'Hub_hole_5.2' )
geompy.addToStudy( Hub_face, 'Hub_face' )
geompy.addToStudy( Hub, 'Hub' )
geompy.addToStudy( Plane_1, 'Plane_1' )
geompy.addToStudy( Start_profile_point_1, 'Start_profile_point_1' )
geompy.addToStudy( Start_profile_point_2, 'Start_profile_point_2' )
geompy.addToStudy( Start_profile_control_1, 'Start_profile_control_1' )
geompy.addToStudy( Start_profile_point_3, 'Start_profile_point_3' )
geompy.addToStudy( Start_profile_control_3, 'Start_profile_control_3' )
geompy.addToStudy( Start_profile_vector_start, 'Start_profile_vector_start' )
geompy.addToStudy( Start_profile_vector_end, 'Start_profile_vector_end' )
geompy.addToStudy( Start_profile_contour, 'Start_profile_contour' )
geompy.addToStudy( Start_profile_base, 'Start_profile_base' )
geompy.addToStudy( Start_profile, 'Start_profile' )
geompy.addToStudy( Mirror_Y, 'Mirror_Y' )
geompy.addToStudy( End_profile, 'End_profile' )
geompy.addToStudy( Edge_profile_point_1, 'Edge_profile_point_1' )
geompy.addToStudy( Edge_profile_point_2, 'Edge_profile_point_2' )
geompy.addToStudy( Edge_profile_point_3, 'Edge_profile_point_3' )
geompy.addToStudy( Edge_profile_control_3, 'Edge_profile_control_3' )
geompy.addToStudy( Edge_profile_control_1, 'Edge_profile_control_1' )
geompy.addToStudy( Edge_profile_vector_1, 'Edge_profile_vector_1' )
geompy.addToStudy( Edge_profile_vector_2, 'Edge_profile_vector_2' )
geompy.addToStudy( Edge_profile_contour, 'Edge_profile_contour' )
# geompy.addToStudy( Edge_profile_base, 'Edge_profile_base' )
geompy.addToStudy( Edge_profile, 'Edge_profile' )
geompy.addToStudy( Plane_2, 'Plane_2' )
geompy.addToStudy( Mid_profile_2, 'Mid_profile_2' )
geompy.addToStudy( Mid_profile_1, 'Mid_profile_1' )
geompy.addToStudy( Mid_profile_3, 'Mid_profile_3' )
geompy.addToStudy( Mid_profile_control_1, 'Mid_profile_control_1' )
geompy.addToStudy( Mid_profile_control_3, 'Mid_profile_control_3' )
geompy.addToStudy( Mid_profile_vector_1, 'Mid_profile_vector_1' )
geompy.addToStudy( Mid_profile_vector_2, 'Mid_profile_vector_2' )
geompy.addToStudy( Mid_profile_contour, 'Mid_profile_contour' )
geompy.addToStudy( Mid_profile_base, 'Mid_profile_base' )
geompy.addToStudy( Mid_profile_1_1, 'Mid_profile_1' )
geompy.addToStudy( Mirror_X, 'Mirror_X' )
geompy.addToStudy( Mid_profile_2_1, 'Mid_profile_2' )
geompy.addToStudy( Bezier_path_1, 'Bezier_path_1' )
geompy.addToStudy( Bezier_path_2, 'Bezier_path_2' )
geompy.addToStudy( Bezier_path_3, 'Bezier_path_3' )
geompy.addToStudy( Bezier_path_4, 'Bezier_path_4' )
geompy.addToStudy( Bezier_path_5, 'Bezier_path_5' )
geompy.addToStudy( Bezier_curve_control_5, 'Bezier_curve_control_5' )
geompy.addToStudy( Bezier_curve_control_1, 'Bezier_curve_control_1' )
geompy.addToStudy( Vector_1, 'Vector_1' )
geompy.addToStudy( Vector_2, 'Vector_2' )
geompy.addToStudy( Bezier_curve_path_pipe, 'Bezier_curve_path_pipe' )
geompy.addToStudy( Pipe_1, 'Pipe_1' )
# geompy.addToStudy( Pipe_2, 'Pipe_2' )
# geompy.addToStudy( Pipe_3, 'Pipe_3' )
geompy.addToStudy( Bezier_curve_test, 'Bezier_curve_test' )
geompy.addToStudy( Pipe_2, 'Pipe_2' )
geompy.addToStudy( Pipe_test, 'Pipe_test' )
geompy.addToStudy( Bezier_test_2, 'Bezier_test_2' )
geompy.addToStudy( Pipe_3, 'Pipe_3' )
geompy.addToStudy( Blade_1, 'Blade_1' )
geompy.addToStudy( Blade_2, 'Blade_2' )
geompy.addToStudy( Blade_3, 'Blade_3' )
geompy.addToStudy( Blade_1_minus_Blade_2_and_Blade_3, 'Blade_1_minus_Blade_2_and_Blade_3' )
geompy.addToStudy( Blade_2_minus_Blade_1_and_Blade_3, 'Blade_2_minus_Blade_1_and_Blade_3' )
geompy.addToStudy( Blade_3_minus_Blade_1_and_Blade_2, 'Blade_3_minus_Blade_1_and_Blade_2' )

geompy.addToStudy( Final_Blade_1, 'Final_Blade_1' )
geompy.addToStudy( Final_Blade_2, 'Final_Blade_2' )
geompy.addToStudy( Final_blade_3, 'Final_blade_3' )


if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
