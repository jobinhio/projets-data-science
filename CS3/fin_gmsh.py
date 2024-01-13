import argparse
import gmsh
import sys


def parse_arguments():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--lc", help="mesh caracteristic length", type=float, default=0.05)
    parser.add_argument("--mesh", help="activate mesh mode", action="store_true")
    parser.add_argument("--meshAlgo", help="mesh algorithm", type=str, default="Frontal-Delaunay", choices=["MeshAdapt", "Automatic", "Initial", "Delaunay", "Frontal-Delaunay", "BAMG"])
    parser.add_argument("--refineExt", help="refine external boundary", action="store_true")
    parser.add_argument("--refineFactor", help="refine factor", type=float, default=0.1)
    parser.add_argument("--refineSampling", help="sampling for external boundary", type=int, default=100)
    parser.add_argument("--refineDistMin", help="minimum distance for external boundary", type=float, default=0.15)
    parser.add_argument("--refineDistMax", help="maximum distance for external boundary", type=float, default=0.25)
    parser.add_argument("--view", help="activate view mode", action="store_true")
    parser.add_argument("--L", help="length of fins", type=float, default=2.5)
    parser.add_argument("--N", help="number of fins", type=int, default=4)
    parser.add_argument("--t", help="thickness of fins", type=float, default=0.25)
    parser.add_argument("--d", help="distance between fins", type=float, default=0.75)
    parser.add_argument("--w", help="width of fins", type=float, default=1.0)

    return parser.parse_args()


def initialize_gmsh_model():
    """Initialize GMSH and add a model."""
    
    gmsh.initialize()
    gmsh.model.add("fin")


def create_geometry(lc,L,N,t,d,w):
    """Create the geometry of the thermal fin."""

    # get parameters


    # add a rectangle (the central post)
    x0, y0, z0 = 0, 0, 0
    dx = w
    dy = N * (d + t) + t
    _id = gmsh.model.occ.addRectangle(x0, y0, z0, dx, dy) # _id is the tag of the rectangle
    gmsh.model.occ.synchronize()

    # create branches
    _id_branches = []
    for r in range(1, N + 1):
        x = -L
        y = r * (d + t)
        z = 0
        dx = 2 * L + w
        dy = t
        _id_current_branch = gmsh.model.occ.addRectangle(x, y, z, dx, dy)
        _id_branches.append(_id_current_branch)
    gmsh.model.occ.synchronize()

    return _id, _id_branches


def apply_fragment(_id, _id_branches):
    """Apply fragmentation to the model if required."""

    ov, ovv = gmsh.model.occ.fragment([(2, _id)], [(2, i) for i in _id_branches])
    # ov contains all the generated entities of the same dimension as the input
    
    gmsh.model.occ.synchronize()

    # entities
    print("fragment produced volumes :")
    for e in ov:
        print(e)

    # ovv contains the parent-child relationships for all the input entities
    print("before/after fragment relations :")
    for e in zip([(2, _id)] + [(2, i) for i in _id_branches], ovv):
            print("parent " + str(e[0]) + " -> children " + str(e[1]))

    return ov, ovv


def create_physical_groups(_id, _id_branches, ovv,w):
    """Create physical groups for the model."""

    # select 0 for nodes, 1 for curves
    select = 1
    # use bounding box to get the root curve id
    x0, y0, z0 = 0, 0, 0
    eps = 1e-6
    xmin = x0 - eps
    ymin = y0 - eps
    zmin = z0 - eps
    xmax = x0 + w + eps
    ymax = y0 + eps
    zmax = z0 + eps
    _ov = gmsh.model.getEntitiesInBoundingBox(xmin, ymin, zmin, xmax, ymax, zmax, dim=select)
    print("entities in bounding box :")
    print(f'_ov={_ov}')
    Gamma_root_id = _ov[0][1]

    # create physical groups
    
    # for the central post
    ps = gmsh.model.addPhysicalGroup(2, [i for _, i in ovv[_id - 1]])
    gmsh.model.setPhysicalName(2, ps, name="Post")
    # for the branches or sub-fins
    for r, elt in enumerate(ovv[(_id_branches[0] - 1) : ]):
        ids_group = [elt[0][1], elt[-1][1]]
        ps = gmsh.model.addPhysicalGroup(2, ids_group)
        gmsh.model.setPhysicalName(2, ps, name=f"Fin_{r + 1}")
    
    # for the external boundary
    Gamma_ext = gmsh.model.getBoundary(gmsh.model.getEntities(2))
    for i in range(len(Gamma_ext)):
        Gamma_ext[i] = Gamma_ext[i][1]
    Gamma_ext_ids = [indice for indice in Gamma_ext if indice != Gamma_root_id]
    ps = gmsh.model.addPhysicalGroup(1, Gamma_ext_ids)
    gmsh.model.setPhysicalName(1, ps, name="Gamma_ext")
    # for the root boundary
    ps = gmsh.model.addPhysicalGroup(1, [Gamma_root_id])
    gmsh.model.setPhysicalName(1, ps, name="Gamma_root")

    return Gamma_ext_ids


def apply_refinement(Gamma_ext_ids, refineSampling,lc,refineFactor,refineDistMin,refineDistMax):
    """Apply refinement to the external boundary if required."""

    gmsh.model.mesh.field.add("Distance", 1)
    gmsh.model.mesh.field.setNumbers(1, "CurvesList", Gamma_ext_ids)
    gmsh.model.mesh.field.setNumber(1, "Sampling", refineSampling)

    gmsh.model.mesh.field.add("Threshold", 2)
    gmsh.model.mesh.field.setNumber(2, "InField", 1)
    gmsh.model.mesh.field.setNumber(2, "SizeMin", lc * refineFactor)
    gmsh.model.mesh.field.setNumber(2, "SizeMax", lc)
    gmsh.model.mesh.field.setNumber(2, "DistMin", refineDistMin)
    gmsh.model.mesh.field.setNumber(2, "DistMax", refineDistMax)

    gmsh.model.mesh.field.setAsBackgroundMesh(2)


def generate_mesh(Gamma_ext_ids ):
    """Generate mesh for the model."""

    MeshAlgo2D = {
                "MeshAdapt": 1,
                "Automatic": 2,
                "Initial": 3,
                "Delaunay": 5,
                "Frontal-Delaunay": 6,
                "BAMG": 7,
            }
    
    refineSampling,lc,refineFactor,refineDistMin,refineDistMax = 100,0.05,0.1,0.15,0.25
    apply_refinement(Gamma_ext_ids, refineSampling,lc,refineFactor,refineDistMin,refineDistMax)


    # set meshing options
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    # set meshing algorithm
    gmsh.option.setNumber("Mesh.Algorithm", MeshAlgo2D["MeshAdapt"])

    # generate 2D mesh
    gmsh.model.mesh.generate(2)

    # save mesh to disk
    gmsh.write("fin.msh")


def main():
    """Console script to generate gmsh geometry and mesh of a thermal fin."""


    initialize_gmsh_model()

    lc,L,N,t,d,w = 0.05,2.5,4,0.25,0.75,1.0
    _id, _id_branches = create_geometry(lc,L,N,t,d,w)

    _, ovv = apply_fragment(_id, _id_branches)

    Gamma_ext_ids = create_physical_groups(_id, _id_branches, ovv, w)

   
    generate_mesh(Gamma_ext_ids)
        
  
    gmsh.fltk.run()

    gmsh.finalize()

    return 0


if __name__ == "__main__":
    sys.exit(main())