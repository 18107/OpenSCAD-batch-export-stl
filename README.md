# OpenSCAD-batch-export-stl

Usage: `python export.py <filename.scad> [fileType]`

This script searches for `module export()` and individually renders and exports each item in it.
Each item is expected to be on its own line. The file name will be the comment on the same line, or the module call if no comment exists.
All files will be put in a folder with the same name as the scad file it's created from.

Example:

ExampleFile.scad
```
module export() {
  cube(10);
  sphere(5); //Ball
}
```

`python export.py ExampleFile.scad` will generate a folder named "ExampleFile exported", and will contain the files "cube.stl" and "Ball.stl"
