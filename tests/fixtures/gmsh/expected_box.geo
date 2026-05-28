// OpenSolver Workbench Gmsh primitive template
// geometry_id: box
// kind: box
// mesh_dimension: 3
// units: m

lc = 0.05;
Mesh.CharacteristicLengthMin = 0.05;
Mesh.CharacteristicLengthMax = 0.05;

SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 1, 0.2, 0.1};
Physical Surface("inlet") = {1};
Physical Surface("outlet") = {2};
Physical Surface("wall") = {3, 4, 5, 6};
Physical Volume("domain") = {1};
