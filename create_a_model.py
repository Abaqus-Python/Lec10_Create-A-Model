# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 12:13:23 2024

@author: Dell
"""

from abaqus import session, mdb
from abaqusConstants import STANDARD_EXPLICIT, STANDALONE, THREE_D, \
    DEFORMABLE_BODY, MIDDLE_SURFACE, FROM_SECTION, ON, UNIFORM, UNSET, \
    ANALYSIS, PERCENTAGE, SINGLE, OFF, ODB, DEFAULT

# get current viewport object
vp_name = session.currentViewportName
viewport = session.viewports[vp_name]
viewport.makeCurrent()
viewport.maximize()

model_name = 'Block'
part_name = 'BLOCK'
w, h = 20.0, 20.0
depth = 20.0
hole_center = (0.0, 0.0)
radius = 6

whole_model_set = 'block'

material_name = 'Steel'
youngs_modulus = 2.07e5
poissons_ratio = 0.3

section_name = '3d_section'

instance_name = part_name + '-1-1'

step_name = 'Pressure_150MPa'
load_surf_name = 'LOAD_TOP_SURF'
pressure_val = 250.0
bc_surf_name = 'BC_BOTTOM_SURF'

globalMeshSize = 1.0

job_name = 'block'

# Create the model object
myModel = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)

# Create sketch object
sketch = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)

sketch.setPrimaryObject(option=STANDALONE)
# Draw rectangle
sketch.rectangle(point1=(-w/2.0, -h/2.0), point2=(w/2.0, h/2.0))
# Draw a circle
sketch.CircleByCenterPerimeter(center=hole_center,
                               point1=(hole_center[0], hole_center[1]+radius))

# define a part object
myPart = myModel.Part(name=part_name, dimensionality=THREE_D,
                      type=DEFORMABLE_BODY)

myPart.BaseSolidExtrude(sketch=sketch, depth=depth)
sketch.unsetPrimaryObject()

# Set the part to the viewport
viewport.setValues(displayedObject=myPart)

# MATERIAL
steel_mat = myModel.Material(name=material_name)
steel_mat.Elastic(table=((youngs_modulus, poissons_ratio), ))

# SECTION
myModel.HomogeneousSolidSection(name=section_name,  material=material_name,
                                thickness=None)

region = myPart.Set(cells=myPart.cells, name=whole_model_set)
myPart.SectionAssignment(region=region, sectionName=section_name, offset=0.0,
                         offsetType=MIDDLE_SURFACE, offsetField='',
                         thicknessAssignment=FROM_SECTION)

# ASSEMBLY
asm_obj = myModel.rootAssembly
myInstance = asm_obj.Instance(name=instance_name, part=myPart, dependent=ON)
# Set assembly to the viewport
viewport.assemblyDisplay.setValues(adaptiveMeshConstraints=ON)

# ANALYSIS STEP
myModel.StaticStep(name=step_name, previous='Initial',
                   initialInc=0.1, maxInc=0.2, nlgeom=ON)

# LOADS and BC
# Apply pressure load
side1Faces = myInstance.faces.findAt(((0.1, h/2.0, 0.1), ))
region = asm_obj.Surface(side1Faces=side1Faces, name=load_surf_name)
myModel.Pressure(name='Load-1', createStepName=step_name,
                 region=region, distributionType=UNIFORM, field='',
                 magnitude=pressure_val, amplitude=UNSET)

# Apply boundary condition
faces1 = myInstance.faces.findAt(((0.1, -h/2.0, 0.1), ))
region = asm_obj.Set(faces=faces1, name=bc_surf_name)
myModel.EncastreBC(name='BC-1', createStepName=step_name,
                   region=region, localCsys=None)

# MESH
myPart.seedPart(size=globalMeshSize, deviationFactor=0.1, minSizeFactor=0.1)
myPart.generateMesh()
# Regenerate assembly to reflect mesh
asm_obj.regenerate()

# JOB
myJob = mdb.Job(
    name=job_name, model=model_name, description='', type=ANALYSIS,
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1,
    multiprocessingMode=DEFAULT, numCpus=1, numGPUs=0
    )
myJob.submit(consistencyChecking=OFF)
