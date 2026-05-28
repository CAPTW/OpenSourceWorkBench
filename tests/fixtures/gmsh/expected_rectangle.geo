// OpenSolver Workbench Gmsh primitive template
// geometry_id: rectangle
// kind: rectangle
// mesh_dimension: 2
// units: m

lc = 0.05;
Mesh.CharacteristicLengthMin = 0.05;
Mesh.CharacteristicLengthMax = 0.05;

SetFactory("Built-in");
Point(1) = {0, 0, 0, 0.05};
Point(2) = {1, 0, 0, 0.05};
Point(3) = {1, 0.5, 0, 0.05};
Point(4) = {0, 0.5, 0, 0.05};
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};
Physical Curve("inlet") = {4};
Physical Curve("outlet") = {2};
Physical Curve("wall") = {1, 3};
Physical Surface("domain") = {1};
