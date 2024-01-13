import argparse
import gmsh
import sys


def MakeBranchs(L,N,t,d):
        # create a branch
    _id_branches = []
    # branche du  grand rectangle
    x0 = 0
    y0 = 0
    z0 = 0
    dx = 1
    dy = N * (d + t) + t
    _id = gmsh.model.occ.addRectangle(x0, y0, z0, dx, dy) # les id commencent a 1
    # _id_branches.append(_id)
    gmsh.model.occ.synchronize()
    
    # branches des long rectangles
    for r in range(1, N + 1):
        # creation des long rectangles
        _id_branches.append(gmsh.model.occ.addRectangle(-L,r*(d+t),0,2*L+1,t))
    gmsh.model.occ.synchronize()
    return _id , _id_branches

    
def MakeFragment(_id , _id_branches):
    # fragmentations de la géométrie
    ov, ovv = gmsh.model.occ.fragment(
        [(2, _id)], [(2, i) for i in _id_branches]
    )
    # ov contains all the generated entities of the same dimension as the input
    # entities:
    print("fragment produced volumes:")
    for e in ov:
        print(e)

    # ovv contains the parent-child relationships for all the input entities:
    print("before/after fragment relations:")
    for e in zip([(2, _id)] + [(2, i) for i in _id_branches], ovv):
        print("parent " + str(e[0]) + " -> child " + str(e[1]))

    gmsh.model.occ.synchronize()

    return  ov, ovv 

def MakePhysicalGroup(_id , _id_branches,_id_root, ov, ovv ):
    # for the central Omega0
    # ps = gmsh.model.addPhysicalGroup(2, [_id])
    # gmsh.model.setPhysicalName(2, ps, name="Gamma_root")
    ps = gmsh.model.addPhysicalGroup(2, [i for _, i in ovv[_id - 1]])
    gmsh.model.setPhysicalName(2, ps, name="Gamma_root")

    # for the branches or sub-fins
    # _id_branches contient des tuples (tag = _id, numero de l'elment)

    for i, elt in enumerate(ovv[(_id_branches[0] - 1) : ]):
        _ids_Fin_i = [elt[0][1], elt[-1][1]] # on récupére l'id de Fin_i
        ps = gmsh.model.addPhysicalGroup(2, _ids_Fin_i)
        gmsh.model.setPhysicalName(2, ps, name=f"Fin_{i + 1}")
    
    # for the external boundary
    Gamma_ext = gmsh.model.getBoundary(gmsh.model.getEntities(2))
    for i in range(len(Gamma_ext)):
        Gamma_ext[i] = Gamma_ext[i][1]
    _ids_Gamma_ext = [indice for indice in Gamma_ext if indice != _id_root]
    ps = gmsh.model.addPhysicalGroup(1, _ids_Gamma_ext)
    gmsh.model.setPhysicalName(1, ps, name="Gamma_ext")

    # for the root boundary
    ps = gmsh.model.addPhysicalGroup(1, [_id_root])
    gmsh.model.setPhysicalName(1, ps, name="Gamma_root")


    return _ids_Gamma_ext


def MakeMesh(parser,_id,_ids_Gamma_ext,lc,hExt):
    ## pour raffiner le maillage au bord
    # if parser.raffiner:

    # gmsh.model.mesh.field.add("Distance", 1)
    # gmsh.model.mesh.field.setNumbers(1, "CurvesList", _ids_Gamma_ext)
    # gmsh.model.mesh.field.setNumber(1, "Sampling", 100)

    # gmsh.model.mesh.field.add("Threshold", 2)
    # gmsh.model.mesh.field.setNumber(2, "InField", 1)
    # gmsh.model.mesh.field.setNumber(2, "SizeMin",hExt ) # hExt
    # gmsh.model.mesh.field.setNumber(2, "SizeMax", lc)
    # gmsh.model.mesh.field.setNumber(2, "DistMin", 0.15)
    # gmsh.model.mesh.field.setNumber(2, "DistMax", 0.17)

    # gmsh.model.mesh.field.setAsBackgroundMesh(2)

    MeshAlgo2D = {
        "MeshAdapt": 1,
        "Automatic": 2,
        "Initial": 3,
        "Delaunay": 5,
        "Frontal-Delaunay": 6,
        "BAMG": 7,
    }
    
   
       # set meshing options
    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    # Meshing algorithms can changed globally using options:
    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D["Frontal-Delaunay"])  # Frontal-Delaunay for 2D meshes

    # They can also be set for individual surfaces, e.g. for using `MeshAdapt' on
    # surface 1:
    gmsh.model.mesh.setAlgorithm(2, _id, MeshAlgo2D["MeshAdapt"])

    # set mesh characteristic size
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lc)


    # We can then generate a 2D mesh...
    gmsh.model.mesh.generate(2)

    # ... and save it to disk
    gmsh.write("fin.msh")

    return 0


def main():
    """Console script for python_magnetgeo."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--lc", help="load mesh size from file", type=float, default=0.05)
    parser.add_argument("--mesh", help="activate mesh mode", action="store_true")
    parser.add_argument("--fragment", help="activate fragment", action="store_true")
    parser.add_argument("--view", help="activate view mode", action="store_true")
    parser.add_argument("--debug", help="activate debug mode", action="store_true")

    # arguments en plus
    parser.add_argument("--Lfins", help="longueur d'un fin", type=float, default=2.5)
    parser.add_argument("--Nfins", help="nombre de fins", type=int, default=4)
    parser.add_argument("--t", help="largeur de f_i", type=float, default=0.25)
    parser.add_argument("--d", help="distance entre les f_i", type=float, default=0.75)

    parser.add_argument("--hExt", help="load mesh size from Ext", type=float, default=0.01)
    parser.add_argument("--raffiner", help="activer le mode raffiner", action="store_true")



    # parameters global

    # lc = parser.lc
    # L = parser.Lfins
    # N = parser.Nfins
    # t = parser.t
    # d = parser.d
    # hExt = parser.hExt

    lc = 0.05
    L = 2.5
    N = 4
    t = 0.25
    d = 0.75

    hExt = 0.01

    x0 = 0
    y0 = 0
    z0 = 0
    dx = 1
    dy = N * (d + t) + t


    # init gmsh 
    gmsh.initialize()
    # add a model
    gmsh.model.add("fin")


    _id,_id_branches = MakeBranchs(L,N,t,d) 
    ov, ovv = MakeFragment(_id , _id_branches)

    ## physical group
    # select 0 for nodes, 1 for lines
    select = 1
    eps = 1.e-3 #1.e-3
    xmin = x0 - eps
    ymin = y0 -eps
    zmin = z0 -eps
    xmax = x0 + eps +1
    ymax = y0 + eps
    zmax = z0 + eps
    # On recupere Gamma_root
    _ov = gmsh.model.getEntitiesInBoundingBox(xmin, ymin, zmin, xmax, ymax, zmax, select)
    print(f'_ov={_ov}')
    _id_root = _ov[0][1] 

    _ids_Gamma_ext = MakePhysicalGroup(_id , _id_branches,_id_root, ov, ovv )


    # if parser.mesh:
    MakeMesh(parser,_id,_ids_Gamma_ext,lc,hExt)

    # to view the model
    # if parser.view:
    gmsh.fltk.run()

    # need to end gmsh
    gmsh.finalize()

    return 0


if __name__ == "__main__":
    sys.exit(main())