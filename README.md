## How to use

Disclaimer: this script not guaranteed to work, and is far from being optimized.

- Open a new Blender project (recommended: use Blender from terminal to read printed out info)
- Go into Scripting tab and make a new file
- Paste the script (.py file in this repository)
- Modify the path to the lammps trajectory file at the bottom of the script
- Modify parameters if required (in SetPrimitive and SkipTimestep)
- Run the script by pressing the Start icon
- May take several minutes (takes about 10 minutes for 2000 atoms on a basic MacBook Pro 2020)

## Notes:

- Collections are created automatically. Primitive objects are created into "Atoms" collection, and are instanced in "Instances" collection.
- There are as many (primtitive) atoms as there are types in the lammpstrj file.
- Each (primitive) atom is assigned a new material called atom {i}.
- The atom types must be a number.
- The dump trajectory file must be of the following form:
```
ITEM: TIMESTEP
0
ITEM: NUMBER OF ATOMS
2016
ITEM: BOX BOUNDS ff ff ff
-6.0000000000000000e+01 6.0000000000000000e+01
-6.0000000000000000e+01 6.0000000000000000e+01
-6.0000000000000000e+01 6.0000000000000000e+01
ITEM: ATOMS id type xs ys zs
3 1 0.300446 0.0805083 0.5
1 1 0.290213 0.0864167 0.5
5 1 0.31068 0.0864167 0.5
7 1 0.320913 0.0805083 0.5
11 1 0.34138 0.0805083 0.5
9 1 0.331147 0.0864167 0.5
...
```
