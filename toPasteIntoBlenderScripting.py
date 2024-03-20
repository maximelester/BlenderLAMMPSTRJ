# Import packages

import bpy
import numpy as np

# -----------------#
# Trajectory class #
# -----------------# 

'''

Imports a trajectory file (lammpstrj) and generates
a numpy array of the form:

    - self.atoms[i] = [[id, type, x, y, z], ...] (i is the frame id)

'''

class Trajectory:

    # ----------------------------------------------------- #
    # Related to extracting information from lammpstrj file #
    # ----------------------------------------------------- #

    def __init__(self, path):

        self.path = path
        self.GetRawFile() # reads the trajectory file
        self.GetInfo() # extracts information from the str object
        
    def __repr__(self):
        '''
        Basic print function (loops over attributes of self)
        '''
        s = '\n'
        d = self.__dict__
        for k, v in zip(d.keys(), d.values()):
            if ['RawFile'].count(k)==0: # list: attributes to hide
                u = '\t'*(3-(len(k))//8)
                if type(v) == np.ndarray:
                    if len(v.shape) > 1:
                        s+=f'{k}{u}np.array {v.shape}\n'
                    else: s+=f'{k}{u}{v}\n'
                else:
                    s+=f'{k}{u}{v}\n'

        return s

    def GetInfo(self):
        '''
        Gathers functions that get called sequentially during __init__
        '''
        self.GetAtoms()
        self.GetTypes()

    def GetAtoms(self):
        '''
        Stores all important information in self
        Using the string information in lammpstrj file
        '''

        # initializing the list of string lines from lammpstrj file
        lines = self.RawFile

        # initializing lists
        timesteps = []
        number_atoms = []
        extents = []
        indices_coord0 = []
        indices_coord1 = []
        atoms = []
        atoms_header = ''

        # looping over every single line
        for i in range(len(lines)):
            l = lines[i]
            if l.count('ITEM: TIMESTEP')>0:
                timesteps.append(int(lines[i+1]))
                if i != 0:
                    indices_coord1.append(i)
            if l.count('ITEM: NUMBER OF ATOMS')>0:
                number_atoms.append(int(lines[i+1]))
            if l.count(f'ITEM: BOX BOUNDS')>0:
                xb = BreakString(lines[i+1])
                yb = BreakString(lines[i+2])
                zb = BreakString(lines[i+3])
                extent = np.array([xb[0], xb[1], yb[0], yb[1], zb[0], zb[1]])
                extents.append(extent)
            if l.count(f'ITEM: ATOMS')>0:
                atoms_header = BreakString(l[l.index('ATOMS')+6:], sep=' ', func=str)
                indices_coord0.append(i+1)
        indices_coord1.append(-1) # adds the latest coord1 index (last line)

        # looping every coordinate index (makes the atoms array)
        for i0, i1 in zip(indices_coord0, indices_coord1):
            temp = []
            for i in range(i0, i1):
                v = BreakString(lines[i])
                temp.append(v)
            # turning temp into an array
            temp = np.array(temp)
            # rearranging temp by id (first column)
            if temp.size>0:
                sorted_temp = temp[np.argsort(temp[:, 0])]
                if len(sorted_temp)!=0:
                    atoms.append(sorted_temp)

        # stores info as self.<attribute>
        self.timesteps = np.array(timesteps)
        self.number_timesteps = len(timesteps)
        self.number_atoms = np.array(number_atoms)
        self.extents = np.array(extents)
        self.extent0 = self.extents[0]
        self.atoms_header = atoms_header
        if np.all(self.number_atoms-np.mean(self.number_atoms)==0):
            self.atoms = np.array(atoms)
            self.atom_varies = False
        else:
            self.atoms = atoms
            self.atom_varies = True
            print(f'Beware, some atoms get lost during the simulation')

    def GetRawFile(self):
        '''
        Stores self.RawFile which is the full string 
        '''
        with open(path) as f:
            self.RawFile = f.readlines()

    def GetTypes(self):
        '''
        Stores self.Ntypes the number of atom types
        - currently only looks at the first frame
        '''
        self.atom_types = np.unique(self.atoms[0,:,1])
    
    def GetXYZFromID(self, ID):
        '''
        Returns position array [[x0, y0, z0], [x1, y1, z1], ...]
        of a given id
        '''
        data = self.atoms
        pos = []
        for i in range(len(self.atoms)):
            for at in self.atoms[i]:
                # print(at)
                # input()
                if at[0] == ID:
                    pos.append(at[2:])
        return np.array(pos)
    
    def SkipTimestep(self, n):
        '''
        Reduces the size of the time-dependent arrays by a factor n
        '''	
        self.atoms = self.atoms[::n,:,:]
        self.extents = self.extents[::n]
        self.timesteps = self.timesteps[::n]
        self.number_timesteps = len(self.timesteps)
    
    # ---------------------------------- #
    # Related to making the Blender file #
    # ---------------------------------- #
    
    def Initialize(self):
        '''
        Initializes the Blender scene
        Future work:
            - name the new collection as per the folder name
        '''
        
        # makes a collection for the whole trajectory
        name = 'LAMMPSTRJ'
        collection = bpy.data.collections.new(name)
        
        # puts the collection in the Scene collection
        bpy.context.scene.collection.children.link(collection)
    
        # stores collection as a parameter	
        self.collection_main = name
        
        # sets correct frame number
        self.SetFrameNumber()
        
    def SetFrameNumber(self):
        '''
        Correctly sets the number of frames in the Blender timeline
        '''
        bpy.context.scene.frame_end = self.number_timesteps
    
    def SetPrimitive(self, n=1, smooth=True):
        '''
        Creates primitive objects which get instanced for every atom in the simulation
        '''
        
        # finds the main collection
        col = bpy.data.collections[self.collection_main]
        
        # make a new collection
        name = 'Atoms'	
        new_col = bpy.data.collections.new(name)
    
        # link the new collection to main collection	
        col.children.link(new_col)
        
        # stores collection as a parameter
        self.collection_atoms = name
        
        # find the collection in which primitives are stored
        col_atom = bpy.data.collections[self.collection_atoms]
        
        # creates primitives
        for t in self.atom_types:
            
            col = bpy.data.collections[self.collection_atoms]
            
            # object name
            name = f'Atom {int(t)}'
            
            # create icosphere
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=n, location=(0,0,0))
            
            # select object
            obj = bpy.context.active_object
            
            # rename object
            obj.name = name
            obj.data.name = name
            
            # shading smooth
            if smooth == True:
                bpy.ops.object.shade_smooth()
            
            # assign a new material named with object name
            mat = bpy.data.materials.new(name=name)
            obj.data.materials.append(mat)
            
            # move object into collection
            col0 = bpy.context.scene.collection
            col0.objects.unlink(obj)
            col_atom.objects.link(obj)
        
            # unselect object
            bpy.context.active_object.select_set(True)
            
        
    def SetInstances(self):
        '''
        Create the instances from primitive objects based on self.atoms
        '''
        
        # create a new collection in LAMMPSTRJ
        col = bpy.data.collections[self.collection_main]
        
        # make a new collection
        name = 'Instances'
        new_col = bpy.data.collections.new(name)
        col.children.link(new_col)
        self.collection_instances = name
        
        # choice of initializing frame number (typically i = 0; first frame)
        i = 0
        data = self.atoms[i]
        extent = self.extents[i]

        # FOR TESTING PURPOSES (caps the number of atoms)
        # set NUMBER = -1 to include all timesteps (which may
        # be downsized using 
        
        NUMBER = -1 
    
        # loop over the atoms
    
        for j,v in enumerate(data[:NUMBER]):
            
            print(f'{j}\t',v,'\n')

            # retreive information
            id, t, x, y, z = v
            
            # get the parent object that will get instanced
            name_atom = f'Atom {int(t)}'
            print(f'name_atom: {name_atom}')
            atom = bpy.context.scene.objects.get(name_atom)
            print(f'atom: {atom}')
            
            # set the object active
            bpy.context.view_layer.objects.active = atom
            
            # set the object the only selected one
            for obj in bpy.data.objects:
                name = obj.name
                bpy.data.objects[name].select_set(False)
            bpy.data.objects[name_atom].select_set(True)
            print(f'selected: {bpy.context.selected_objects}')

            # get instance name and object
            name_instance = f'Instance {int(t)} id {int(id)}'
                
            # duplicate the object at correct coordinate
            bpy.ops.object.duplicate(linked=True)
            inst = bpy.context.active_object

            # change name
            inst.name = name_instance
            
            # change position
            inst.location = FracToAbsolute(x, y, z, extent)
            
            # insert keyframes 
            inst.keyframe_insert("location", frame=i)
            pos = self.GetXYZFromID(ID=id)
            for frame in range(1,self.number_timesteps):
                x, y, z = pos[frame-1]
                inst.location = FracToAbsolute(x, y, z, extent)
                inst.keyframe_insert("location", frame=frame)
        
        # putting objects into proper collection
        col_atoms = bpy.data.collections[self.collection_atoms]
        col_instance = bpy.data.collections[self.collection_instances]
        for obj in col_atoms.objects:
            if obj.name[0] == 'I': # name: "Instance <type> id <id>"
                col_atoms.objects.unlink(obj)
                col_instance.objects.link(obj)
            
            

# --------------- #
# Other functions #
# --------------- #

def BreakString(s, sep=' ', func=float):
    '''
    Breaks the string into a numpy array with given separator
    '''
    l = []
    indices = [0]

    # find indices that bounds every value
    for i in range(len(s)):
        c = s[i]
        if c == sep:
            indices.append(i)
    indices.append(-1)

    # separate the string at indices
    for i in range(len(indices)-1):
        i0 = indices[i]
        i1 = indices[i+1]
        if func == float:
            l.append(func(s[i0:i1]))
        elif func == str:
            l = s.split()
    return l

def FracToAbsolute(xf, yf, zf, extent):
    '''
    Returns absolute coordinates given fractional coordinates
    and extent [x0, x1, y0, y1, z0, z1]
    '''
    x0, x1, y0, y1, z0, z1 = extent
    x = xf*(x1-x0)+x0
    y = yf*(y1-y0)+y0
    z = zf*(z1-z0)+z0
    
    return x, y, z

def DeleteAllObjects():
    '''
    Deletes all materials, objects, meshes, collections
    (useful for debugging, typically not used later)
    '''
    # delete materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    # delete objects
    for object in bpy.data.objects:
        bpy.data.objects.remove(object)
    # delete meshes
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    # delete collections
    for col in bpy.data.collections:
        bpy.data.collections.remove(col)

def IsSelected(name):
    return bpy.data.objects[name].select_get()

def DeselectAll():
    bpy.ops.objects.item_activate(deselect_all=True)
    
def Select(name):
    obj = bpy.context.scene.objects.get(name)
    bpy.context.view_layer.objects.active = obj
    bpy.data.objects[name].select_set(True)
        

# --------- #
# Execution #
# --------- #

# cleaning the bpy file

DeleteAllObjects()

# choosing the path (

path = './dump.lammpstrj' 

# execution

T = Trajectory(path=path)
T.Initialize()
T.SetPrimitive(n=1) # better set n = 1, and modify primitive object if finer object required
T.SkipTimestep(n=1) # handles 100s of timesteps fine, but in case of super large dump file this may be required
T.SetInstances()
