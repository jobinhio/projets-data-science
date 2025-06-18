import matplotlib.pyplot as plt
import numpy as np

"""
Important parameters to create the guide curve:
    amplitude: The angle of the guide curve
    nb_blades: The number of blades of the guide curve
    h: The height of the guide curve
    L: The offset of the guide curve
"""



a = 10
b = 1
amplitude = -0.
nb_blades = 3
t = np.linspace(0,np.pi*2,100*nb_blades)
L = 0.
# x = 2*(np.cos(t)+1)*(a*np.cos(t)+b*np.sin(t))
# y = 2*(np.sin(t))*(a*np.cos(t)+b*np.sin(t))

# l = np.linspace(0,L,100)

x = np.cos((nb_blades-1)*t)-np.cos(t)
y = 2*np.sin((nb_blades-1)*t)+np.sin(t)
z = np.sin(nb_blades*t)*amplitude+np.modf(t/(np.pi*2)*nb_blades)[0]*L
# z = np.zeros(len(x))

# print(np.modf(2.3)[0])

diameter = max(np.linalg.norm([x,y],axis=0))

h = 2

x = x/diameter*h

y = y/diameter*h

# ax = plt.figure().add_subplot(projection='3d')
# ax.plot(x,y,z)

# separate the curves according to the number of blades
x = np.array_split(x,nb_blades)

y = np.array_split(y,nb_blades)

z = np.array_split(z,nb_blades)

t = np.linspace(0,2*np.pi,1000)
a = 1
b = 1
k = 1
l=1
epsilon = 1
c = 2
d_t = a-b*np.cos(t)
# print(d_t)

# The curve generated is the implementation of the following parametric equations:
# https://mathcurve.com/courbes2d/bielledeberard/bielledeberard.shtml
x_ = (b*np.cos(t) + k*d_t - l*epsilon*np.sqrt(c**2-d_t**2))/10
y_ = (b*np.sin(t) + epsilon*k*np.sqrt(c**2-d_t**2) - l*d_t)/10
z_ = np.zeros(x_.shape[0])
# rotate the curve along the z axis of an angle of 30°
theta = np.pi/6
x__ = x_*np.cos(theta)-y_*np.sin(theta)
y__ = x_*np.sin(theta)+y_*np.cos(theta)
x_ = x__
y_ = y__

mean_x = np.mean(x_)
mean_y = np.mean(y_)

x_ -= mean_x
y_ -= mean_y


P1 = []
P2 = []
P3 = []

P_curve1 = []
P_curve2 = []
P_curve3 = []

P_curve = []
for i in range(nb_blades):
    P_curve.append([])

import salome
salome.salome_init_without_session()
import GEOM
from salome.geom import geomBuilder
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")

for x_curve,y_curve,z_curve,i in zip(x,y,z,range(nb_blades)):
    for j in range(x_curve.shape[0]):
        P_curve[i].append(geompy.MakeVertex(x_curve[j],y_curve[j],z_curve[j]))

# print(x_)

P = []
for i in range(nb_blades):
    P.append([])
theta = np.pi*2/nb_blades
for i in range(nb_blades):
    for j in range(x_.shape[0]):
        # print(i)
        # print(j)
        # print(x_.shape[0])
        # print()
        P[i].append(geompy.MakeVertex(x_[j],y_[j],z_[j]))
    x__ = x_*np.cos(theta)-y_*np.sin(theta)
    y__ = x_*np.sin(theta)+y_*np.cos(theta)
    x_ = x__
    y_ = y__
    print(x_)
# print(P[i])



guide = []
P_interpol = []
for i in range(nb_blades):
    guide.append(geompy.MakeInterpol(P_curve[i]))
    geompy.addToStudy( guide[i], 'guide_'+str(i+1))
    P_interpol.append(geompy.MakeInterpol(P[i]))
    geompy.addToStudy( P_interpol[i], 'profile'+str(i+1))

Faces=[]
for P,i in zip(P_interpol,range(nb_blades)):
    Faces.append(geompy.MakeFaceWires([P],1))
    geompy.addToStudy( Faces[i], f'face_{i+1}')

import  SMESH, SALOMEDS
from salome.smesh import smeshBuilder

smesh = smeshBuilder.New()

Mesh_faces = []
for i in range(nb_blades):
    Mesh_faces.append(smesh.Mesh(Faces[i]))
    NETGEN_1D_2D = Mesh_faces[i].Triangle(algo=smeshBuilder.NETGEN_1D2D)
    NETGEN_2D_Simple_Parameters_1 = NETGEN_1D_2D.Parameters(smeshBuilder.SIMPLE)
    NETGEN_2D_Simple_Parameters_1.SetNumberOfSegments( 15 )
    NETGEN_2D_Simple_Parameters_1.LengthFromEdges()
    NETGEN_2D_Simple_Parameters_1.SetAllowQuadrangles( 1 )
    isDone = Mesh_faces[i].Compute()

Mesh_curves = []
Regular_1D = smesh.CreateHypothesis('Regular_1D')
Number_of_Segments_1 = smesh.CreateHypothesis('NumberOfSegments')
Number_of_Segments_1.SetNumberOfSegments( 15 )
for i in range(nb_blades):
    Mesh_4 = smesh.Mesh(guide[i],'Curve_Mesh_'+str(i+1))
    Mesh_curves.append(Mesh_4)
    status = Mesh_4.AddHypothesis(Number_of_Segments_1)
    status = Mesh_4.AddHypothesis(Regular_1D)
    isDone = Mesh_4.Compute()

for curves_mesh,faces_mesh in zip(Mesh_curves,Mesh_faces):
    (_noGroups, error) = faces_mesh.ExtrusionAlongPathObjects( [ faces_mesh ], [ faces_mesh ], [], curves_mesh, None, 1, 0, [  ], 0, 0, [ 0, 0, 0 ], 1, [  ], 0 )