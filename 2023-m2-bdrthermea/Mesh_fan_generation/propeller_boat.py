import matplotlib.pyplot as plt
import numpy as np

l           = np.array([0.0000,0.0624,0.1203,0.1773,0.2343,0.2937,0.3590,0.4377,0.4889,0.5250,0.5729,0.6000,0.6438,0.6842,0.7146,0.7574,0.8150,0.8582,0.8941,0.9249,0.9523,0.9771,1.0000])
r_l         = np.array([0.200,0.300,0.400,0.500,0.600,0.700,0.800,0.900,0.950,0.975,0.995,1.000,0.995,0.975,0.950,0.900,0.800,0.700,0.600,0.500,0.400,0.300,0.200])
b           = np.array([0.1210,0.1431,0.1600,0.1723,0.1797,0.1806,0.1683,0.1423,0.1228,0.1120,0.1027,0.1010,0.1065,0.1190,0.1311,0.1514,0.1763,0.1869,0.1862,0.1770,0.1626,0.1447,0.1240])
theta_s     = np.array([0.00,-0.89,-1.10,-0.90,-0.36,0.43,1.46,2.83,3.78,4.45,5.34,5.87,6.69,7.44,7.99,8.75,9.72,10.40,10.94,11.39,11.77,12.11,12.41])
x_l         = np.array([-0.0620,-0.0822,-0.0933,-0.0968,-0.0928,-0.0807,-0.0587,-0.0255,-0.0022,0.0140,0.0347,0.0458,0.0615,0.0732,0.0789,0.0819,0.0723,0.0537,0.0298,0.0024,-0.0272,-0.0584,-0.0910])
phi         = np.array([-27.56,-25.52,-23.44,-21.26,-18.93,-16.33,-13.26,-9.33,-6.55,-4.56,-1.86,-0.24,2.45,4.99,6.95,9.78,13.77,16.83,19.44,21.74,23.82,25.74,27.56])

# test data
# s = np.array([1.3120,1.3311,1.3365,1.3206,1.2807,1.1980,1.0784,0.9317,0.8631,0.8300,0.8065,0.8060,0.8528,0.9512,1.0400,1.1829,1.3959,1.5433,1.6367,1.6686,1.6636,1.6524,1.6310])
# yb = np.array([0.3007,0.2433,0.1967,0.1576,0.1253,0.0986,0.0774,0.0608,0.0548,0.0526,0.0524,0.0538,0.0583,0.0653,0.0727,0.0867,0.1138,0.1410,0.1686,0.1966,0.2246,0.2526,0.2807])
# yf = np.array([0.014,0.030,0.044,0.055,0.063,0.068,0.069,0.061,0.051,0.043,0.029,0.021,0.008,-0.003,-0.011,-0.020,-0.026,-0.027,-0.026,-0.023,-0.019,-0.014,-0.010])
# dist = np.abs(yb-yf)
s = 0.04
dist=0.02
# print(b/2)

beta = [np.pi/4]

# angles of rotation
gamma = [0,4*np.pi/3,2*np.pi/3]

# beta=[0,-np.pi/3]

def cosd(x):
    return np.cos(np.deg2rad(x))
def sind(x):
    return np.sin(np.deg2rad(x))

def rotation_matrix_X(gamma):
    return np.array([[1,0,0],[0,np.cos(gamma),-np.sin(gamma)],[0,np.sin(gamma),np.cos(gamma)]])
def rotation_matrix_Y(gamma):
    return np.array([[np.cos(gamma),0,np.sin(gamma)],[0,1,0],[-np.sin(gamma),0,np.cos(gamma)]])
def rotation_matrix_Z(gamma):
    return np.array([[np.cos(gamma),-np.sin(gamma),0],[np.sin(gamma),np.cos(gamma),0],[0,0,1]])

X = []
Y = []
Z = []
labels = []
i=0
for gamma_i in gamma:
    x_T = x_l+r_l*theta_s*np.tan(beta[0])
    x_T = np.zeros(len(x_T))
    x = l + x_T + (-b/2+s)*np.sin(beta[0])-dist*np.cos(beta[0])
    # x /= 6
    r=r_l
    theta = phi+theta_s + 1/r*((-b/2+s)*np.cos(beta[0])+dist*np.sin(beta[0]))
    y = r*cosd(theta)
    z = r*sind(theta)
    pt = np.array([x,y,z])
    # pt = np.dot(rotation_matrix_Y(np.pi/2),pt)
    pt = np.dot(rotation_matrix_X(gamma_i),pt)
    # pt = np.dot(rotation_matrix_Y(np.pi/2),pt)
    X.append(pt[0])
    Y.append(pt[1])
    Z.append(pt[2])
    labels.append(f"blade {i}")
    i+=1

print(X)
print(Y)
print(Z)

r = r_l
theta = np.zeros(len(r_l))
x_ = x_l + r*theta_s + np.tan(beta[0])
y_ = r*cosd(theta)
z_ = r*sind(theta)
x_ /= np.max(x_)
# y_ /= np.max(y_)

x_ /= 6
y_ /= 6

barycenter = np.array([np.mean(x_),np.mean(y_),np.mean(z_)])

vec_from_x_0_0 = np.array([X[0][0]-barycenter[0],Y[0][0] -barycenter[1],Z[0][0] -barycenter[2]])

x_ += vec_from_x_0_0[0]
y_ += vec_from_x_0_0[1]
z_ += vec_from_x_0_0[2]

x__ = np.dot(rotation_matrix_X(gamma[1]),np.array([x_,y_,z_]))[0]
y__ = np.dot(rotation_matrix_X(gamma[1]),np.array([x_,y_,z_]))[1]
z__ = np.dot(rotation_matrix_X(gamma[1]),np.array([x_,y_,z_]))[2]

x___ = np.dot(rotation_matrix_X(gamma[2]),np.array([x_,y_,z_]))[0]
y___ = np.dot(rotation_matrix_X(gamma[2]),np.array([x_,y_,z_]))[1]
z___ = np.dot(rotation_matrix_X(gamma[2]),np.array([x_,y_,z_]))[2]

P1 = []
P2 = []
P3 = []

P_curve1 = []
P_curve2 = []
P_curve3 = []

import salome
salome.salome_init_without_session()
import GEOM
from salome.geom import geomBuilder
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")

# O = geompy.MakeVertex(0, 0, 0)
# OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
# OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
# OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)

# Create a unique variable name for each point
for i in range(len(x_)):
    P1.append(geompy.MakeVertex(x_[i], y_[i], z_[i]))
    # geompy.addToStudy(P1[i], f'P1{i}')

P1.append(geompy.MakeVertex(x_[0], y_[0], z_[0]))

for i in range(len(x__)):
    P2.append(geompy.MakeVertex(x__[i], y__[i], z__[i]))
    # geompy.addToStudy(P2[i], f'P2{i}')

P2.append(geompy.MakeVertex(x__[0], y__[0], z__[0]))

for i in range(len(x___)):
    P3.append(geompy.MakeVertex(x___[i], y___[i], z___[i]))
    # geompy.addToStudy(P3[i], f'P3{i}')

P3.append(geompy.MakeVertex(x___[0], y___[0], z___[0]))

curve1 = geompy.MakeInterpol(P1)
curve2 = geompy.MakeInterpol(P2)
curve3 = geompy.MakeInterpol(P3)

# Add the guide curves to the study
for x,y,z,i in zip(X,Y,Z,range(3)):
    if i==0:
        for a,b,c in zip(x,y,z):
            P_curve1.append(geompy.MakeVertex(a,b,c))
    elif i==1:
        for a,b,c in zip(x,y,z):
            P_curve2.append(geompy.MakeVertex(a,b,c))
    else:
        for a,b,c in zip(x,y,z):
            P_curve3.append(geompy.MakeVertex(a,b,c))

guide_1 = geompy.MakeInterpol(P_curve1)
guide_2 = geompy.MakeInterpol(P_curve2)
guide_3 = geompy.MakeInterpol(P_curve3)

# geompy.addToStudy( O, 'O' )
# geompy.addToStudy( OX, 'OX' )
# geompy.addToStudy( OY, 'OY' )
# geompy.addToStudy( OZ, 'OZ' )
geompy.addToStudy( curve1, 'curve1')
geompy.addToStudy( curve2, 'curve2')
geompy.addToStudy( curve3, 'curve3')

geompy.addToStudy( guide_1, 'guide_1')
geompy.addToStudy( guide_2, 'guide_2')
geompy.addToStudy( guide_3, 'guide_3')

Face_1 = geompy.MakeFaceWires([curve1], 1)
Face_2 = geompy.MakeFaceWires([curve2], 1)
Face_3 = geompy.MakeFaceWires([curve3], 1)

geompy.addToStudy( Face_1, 'Face_1' )
geompy.addToStudy( Face_2, 'Face_2' )
geompy.addToStudy( Face_3, 'Face_3' )

import  SMESH, SALOMEDS
from salome.smesh import smeshBuilder

smesh = smeshBuilder.New()
#smesh.SetEnablePublish( False ) # Set to False to avoid publish in study if not needed or in some particular situations:
                                 # multiples meshes built in parallel, complex and numerous mesh edition (performance)

Mesh_1 = smesh.Mesh(Face_1,'Mesh_1')
NETGEN_1D_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_1D2D)
NETGEN_2D_Simple_Parameters_1 = NETGEN_1D_2D.Parameters(smeshBuilder.SIMPLE)
NETGEN_2D_Simple_Parameters_1.SetNumberOfSegments( 15 )
NETGEN_2D_Simple_Parameters_1.LengthFromEdges()
NETGEN_2D_Simple_Parameters_1.SetAllowQuadrangles( 1 )
isDone = Mesh_1.Compute()
Mesh_2 = smesh.Mesh(Face_2,'Mesh_2')
NETGEN_1D_2D_1 = Mesh_2.Triangle(algo=smeshBuilder.NETGEN_1D2D)
NETGEN_2D_Simple_Parameters_2 = NETGEN_1D_2D_1.Parameters(smeshBuilder.SIMPLE)
NETGEN_2D_Simple_Parameters_2.SetNumberOfSegments( 15 )
NETGEN_2D_Simple_Parameters_2.LengthFromEdges()
NETGEN_2D_Simple_Parameters_2.SetAllowQuadrangles( 1 )
isDone = Mesh_2.Compute()
Mesh_3 = smesh.Mesh(Face_3,'Mesh_3')
NETGEN_1D_2D_2 = Mesh_3.Triangle(algo=smeshBuilder.NETGEN_1D2D)
NETGEN_2D_Simple_Parameters_3 = NETGEN_1D_2D_2.Parameters(smeshBuilder.SIMPLE)
NETGEN_2D_Simple_Parameters_3.SetNumberOfSegments( 15 )
NETGEN_2D_Simple_Parameters_3.LengthFromEdges()
NETGEN_2D_Simple_Parameters_3.SetAllowQuadrangles( 1 )
isDone = Mesh_3.Compute()
Regular_1D = smesh.CreateHypothesis('Regular_1D')
Number_of_Segments_1 = smesh.CreateHypothesis('NumberOfSegments')
Number_of_Segments_1.SetNumberOfSegments( 15 )
Mesh_4 = smesh.Mesh(guide_1,'Mesh_4')
status = Mesh_4.AddHypothesis(Number_of_Segments_1)
status = Mesh_4.AddHypothesis(Regular_1D)
isDone = Mesh_4.Compute()
Mesh_5 = smesh.Mesh(guide_2,'Mesh_5')
status = Mesh_5.AddHypothesis(Number_of_Segments_1)
status = Mesh_5.AddHypothesis(Regular_1D)
isDone = Mesh_5.Compute()
Mesh_6 = smesh.Mesh(guide_3,'Mesh_6')
status = Mesh_6.AddHypothesis(Number_of_Segments_1)
status = Mesh_6.AddHypothesis(Regular_1D)
isDone = Mesh_6.Compute()
(_noGroups, error) = Mesh_1.ExtrusionAlongPathObjects( [ Mesh_1 ], [ Mesh_1 ], [], Mesh_4, None, 1, 0, [  ], 0, 0, [ 0, 0, 0 ], 1, [  ], 0 )
(_noGroups, error) = Mesh_2.ExtrusionAlongPathObjects( [ Mesh_2 ], [ Mesh_2 ], [], Mesh_5, None, 1, 0, [  ], 0, 0, [ 0, 0, 0 ], 1, [  ], 0 )
(_noGroups, error) = Mesh_3.ExtrusionAlongPathObjects( [ Mesh_3 ], [ Mesh_3 ], [], Mesh_6, None, 1, 0, [  ], 0, 0, [ 0, 0, 0 ], 1, [  ], 0 )
smesh.SetName(Mesh_4, 'Mesh_4')
# try:
#   Mesh_4.ExportMED( r'C:/Users/schal/M2_CSMI/Projet/BDR_Thermea/propeller/propeller_mesh.med', 0, 41, 1, Mesh_4, 1, [], '',-1, 1 )
#   pass
# except:
#   print('ExportPartToMED() failed. Invalid file name?')


## Set names of Mesh objects
smesh.SetName(NETGEN_1D_2D.GetAlgorithm(), 'NETGEN 1D-2D')
smesh.SetName(Regular_1D, 'Regular_1D')
smesh.SetName(NETGEN_2D_Simple_Parameters_2, 'NETGEN 2D Simple Parameters_2')
smesh.SetName(NETGEN_2D_Simple_Parameters_3, 'NETGEN 2D Simple Parameters_3')
smesh.SetName(NETGEN_2D_Simple_Parameters_1, 'NETGEN 2D Simple Parameters_1')
smesh.SetName(Number_of_Segments_1, 'Number of Segments_1')
smesh.SetName(Mesh_4.GetMesh(), 'Mesh_4')
smesh.SetName(Mesh_1.GetMesh(), 'Mesh_1')
smesh.SetName(Mesh_3.GetMesh(), 'Mesh_3')
smesh.SetName(Mesh_2.GetMesh(), 'Mesh_2')
smesh.SetName(Mesh_5.GetMesh(), 'Mesh_5')
smesh.SetName(Mesh_6.GetMesh(), 'Mesh_6')


if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()