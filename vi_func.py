import bpy, os, sys, multiprocessing, mathutils, bmesh, datetime, colorsys, bgl, blf, numpy
from math import sin, cos, asin, acos, pi, isnan, tan
from mathutils import Vector, Matrix
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty
try:
    import matplotlib
    matplotlib.use('Qt4Agg', force = True)
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    from .windrose import WindroseAxes
    mp = 1
except:
    mp = 0

dtdf = datetime.date.fromordinal

def cmap(cm):
    cmdict = {'hot': 'livi', 'grey': 'shad'}
    for i in range(20):       
        if not bpy.data.materials.get('{}#{}'.format(cmdict[cm], i)):
            bpy.data.materials.new('{}#{}'.format(cmdict[cm], i))
        bpy.data.materials['{}#{}'.format(cmdict[cm], i)].diffuse_color = colorsys.hsv_to_rgb(0.75 - 0.75*(i/19), 1, 1) if cm == 'hot' else colorsys.hsv_to_rgb(1, 0, (i/19))

def radmat(self, scene):
    radname = self.name.replace(" ", "_")    
    radentry = '# ' + ('plastic', 'glass', 'dielectric', 'translucent', 'mirror', 'light', 'metal', 'antimatter')[int(self.radmatmenu)] + ' material\n' + \
            'void {} {}\n'.format(('plastic', 'glass', 'dielectric', 'trans', 'mirror', 'light', 'metal', 'antimatter')[int(self.radmatmenu)], radname) + \
           {'0': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f}\n'.format(self.radcolour, self.radspec, self.radrough), 
            '1': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format(self.radcolour), 
            '2': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} 0\n'.format(self.radcolour, self.radior),
            '3': '0\n0\n7 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f} {3:.3f} {4:.3f}\n'.format(self.radcolour, self.radspec, self.radrough, self.radtrans, self.radtranspec), 
            '4': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format(self.radcolour),
            '5': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format([c * self.radintensity for c in self.radcolour]), 
            '6': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f}\n'.format(self.radcolour, self.radspec, self.radrough), 
            '7': '1 void\n0\n0\n'}[self.radmatmenu] + '\n'

    self['radentry'] = radentry
    return(radentry)
    
def fvmat(self, mn, bound):
#    fvname = on.replace(" ", "_") + self.name.replace(" ", "_") 
    begin = '\n  {}\n  {{\n    type    '.format(mn)  
    end = ';\n  }\n'
    
    if bound == 'p':
        val = 'uniform {}'.format(self.flovi_b_sval) if not self.flovi_p_field else '$internalField'
        pdict = {'0': self.flovi_bmwp_type, '1': self.flovi_bmip_type, '2': self.flovi_bmop_type, '3': 'symmetryPlane', '4': 'empty'}
        ptdict = {'zeroGradient': 'zeroGradient', 'fixedValue': 'fixedValue;\n    value    {}'.format(val), 'calculated': 'calculated;\n    value    $internalField', 
        'freestreamPressure': 'freestreamPressure', 'symmetryPlane': 'symmetryPlane', 'empty': 'empty'}
#        if pdict[self.flovi_bmb_type] == 'zeroGradient':
        entry = ptdict[pdict[self.flovi_bmb_type]]            
#        return begin + entry + end 
    
    elif bound == 'U':
        val = 'uniform ({} {} {})'.format(*self.flovi_b_vval) if not self.flovi_u_field else '$internalField'
        Udict = {'0': self.flovi_bmwu_type, '1': self.flovi_bmiu_type, '2': self.flovi_bmou_type, '3': 'symmetryPlane', '4': 'empty'}
        Utdict = {'fixedValue': 'fixedValue;\n    value    {}'.format(val), 'slip': 'slip', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField',
                  'pressureInletOutletVelocity': 'pressureInletOutletVelocity;\n    value    $internalField', 'zeroGradient': 'zeroGradient', 'symmetryPlane': 'symmetryPlane', 
                  'freestream': 'freestream;\n    freestreamValue    $internalField','calculated': 'calculated;\n    value    $internalField', 'empty': 'empty'}
        entry = Utdict[Udict[self.flovi_bmb_type]]            
#        return begin + entry + end
        
    elif bound == 'nut':
        ndict = {'0': self.flovi_bmwnut_type, '1': self.flovi_bminut_type, '2': self.flovi_bmonut_type, '3': 'symmetryPlane', '4': 'empty'}
        ntdict = {'nutkWallFunction': 'nutkWallFunction;\n    value    $internalField', 'nutUSpaldingWallFunction': 'nutUSpaldingWallFunction;\n    value    $internalField', 
        'calculated': 'calculated;\n    value    $internalField', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField',  'symmetryPlane': 'symmetryPlane','empty': 'empty'}
        entry = ntdict[ndict[self.flovi_bmb_type]]            
#        return begin + entry + end

    elif bound == 'k':
        kdict = {'0': self.flovi_bmwk_type, '1': self.flovi_bmik_type, '2': self.flovi_bmok_type, '3': 'symmetryPlane', '4': 'empty'}
        ktdict = {'fixedValue': 'fixedValue;\n    value    $internalField', 'kqRWallFunction': 'kqRWallFunction;\n    value    $internalField', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField',
        'calculated': 'calculated;\n    value    $internalField', 'symmetryPlane': 'symmetryPlane', 'empty': 'empty'}
        entry = ktdict[kdict[self.flovi_bmb_type]]            
#        return begin + entry + end
        
    elif bound == 'e':
        edict = {'0': self.flovi_bmwe_type, '1': self.flovi_bmie_type, '2': self.flovi_bmoe_type, '3': 'symmetryPlane', '4': 'empty'}
        etdict = {'symmetryPlane': 'symmetryPlane', 'empty': 'empty', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField', 'fixedValue': 'fixedValue;\n    value    $internalField', 
                  'epsilonWallFunction': 'epsilonWallFunction;\n    value    $internalField', 'calculated': 'calculated;\n    value    $internalField', 'symmetryPlane': 'symmetryPlane', 'empty': 'empty'}
        entry = etdict[edict[self.flovi_bmb_type]]            
#        return begin + entry + end
        
    elif bound == 'o':
        odict = {'0': self.flovi_bmwo_type, '1': self.flovi_bmio_type, '2': self.flovi_bmoo_type, '3': 'symmetryPlane', '4': 'empty'}
        otdict = {'symmetryPlane': 'symmetryPlane', 'empty': 'empty', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField', 'zeroGradient': 'zeroGradient', 
                  'omegaWallFunction': 'omegaWallFunction;\n    value    $internalField', 'fixedValue': 'fixedValue;\n    value    $internalField'}
        entry = otdict[odict[self.flovi_bmb_type]]            
#        return begin + entry + end
        
    elif bound == 'nutilda':
        ntdict = {'0': self.flovi_bmwnutilda_type, '1': self.flovi_bminutilda_type, '2': self.flovi_bmonutilda_type, '3': 'symmetryPlane', '4': 'empty'}
        nttdict = {'fixedValue': 'fixedValue;\n    value    $internalField', 'inletOutlet': 'inletOutlet;\n    inletValue    $internalField\n    value    $internalField', 'empty': 'empty', 
                   'zeroGradient': 'zeroGradient', 'freestream': 'freestream\n    freeStreamValue  $internalField\n', 'symmetryPlane': 'symmetryPlane'} 
        entry = nttdict[ntdict[self.flovi_bmb_type]]            
    return begin + entry + end
        
        
def radpoints(o, faces, sks):
    fentries = ['']*len(faces)   
    if sks:
        (skv0, skv1, skl0, skl1) = sks
    for f, face in enumerate(faces):
        fentry = "# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.name.replace(" ", "_"), face.index, 3*len(face.verts))
        if sks:
            ventries = ''.join([" {0[0]} {0[1]} {0[2]}\n".format((o.matrix_world*mathutils.Vector((v[skl0][0]+(v[skl1][0]-v[skl0][0])*skv1, v[skl0][1]+(v[skl1][1]-v[skl0][1])*skv1, v[skl0][2]+(v[skl1][2]-v[skl0][2])*skv1)))) for v in face.verts])
        else:
            ventries = ''.join([" {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n".format(v.co) for v in face.verts])
        fentries[f] = ''.join((fentry, ventries+'\n'))        
    return ''.join(fentries)
                       
def viparams(op, scene):
    if not bpy.data.filepath:
        op.report({'ERROR'},"The Blender file has not been saved. Save the Blender file before exporting")
        return 'Save file'
    if " "  in bpy.data.filepath:
        op.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces in the file name or the directory path")
        return 'Rename file'
    fd, fn = os.path.dirname(bpy.data.filepath), os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if not os.path.isdir(os.path.join(fd, fn)):
        os.makedirs(os.path.join(fd, fn))
    if not os.path.isdir(os.path.join(fd, fn, 'obj')):
        os.makedirs(os.path.join(fd, fn, 'obj'))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam'))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam', 'system')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam', "system"))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam', 'constant')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam', "constant"))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam', 'constant', 'polyMesh')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam', "constant", "polyMesh"))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam', 'constant', 'triSurface')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam', "constant", "triSurface"))
    if not os.path.isdir(os.path.join(fd, fn, 'Openfoam', '0')):
        os.makedirs(os.path.join(fd, fn, 'Openfoam', "0"))
        
    nd = os.path.join(fd, fn)
    fb, ofb, offb, idf  = os.path.join(nd, fn), os.path.join(nd, 'obj'), os.path.join(nd, 'Openfoam'), os.path.join(nd, 'in.idf')
    offzero, offs, offc, offcp, offcts = os.path.join(offb, '0'), os.path.join(offb, 'system'), os.path.join(offb, 'constant'), os.path.join(offb, 'constant', "polyMesh"), os.path.join(offb, 'constant', "triSurface")
    scene['viparams'] = {'rm': ('rm ', 'del ')[str(sys.platform) == 'win32'], 'cat': ('cat ', 'type ')[str(sys.platform) == 'win32'], 'cp': ('cp ', 'copy ')[str(sys.platform) == 'win32'], 
    'nproc': str(multiprocessing.cpu_count()), 'filepath': bpy.data.filepath, 'filename': fn, 'filedir': fd, 'newdir': nd, 'filebase': fb}
    
    scene['liparams'] = {'objfilebase': ofb}
    scene['enparams'] = {'idf_file': idf, 'epversion': '8-2-0'}
    scene['flparams'] = {'offilebase': offb, 'ofsfilebase': offs, 'ofcfilebase': offc, 'ofcpfilebase': offcp, 'of0filebase': offzero, 'ofctsfilebase': offcts}

def resnameunits():
    rnu = {'0': ("Temperature", "Ambient Temperature (C)"),'1': ("Wind Speed", "Ambient Wind Speed (m/s)"), '2': ("Wind Direction", "Ambient Wind Direction (degrees from North)"),
                '3': ("Humidity", "Ambient Humidity"),'4': ("Direct Solar", u'Direct Solar Radiation (W/m\u00b2K)'), '5': ("Diffuse Solar", u'Diffuse Solar Radiation (W/m\u00b2K)'),
                '6': ("Temperature", "Zone Temperatures"), '7': ("Heating Watts", "Zone Heating Requirement (Watts)"), '8': ("Cooling Watts", "Zone Cooling Requirement (Watts)"),
                '9': ("Solar Gain", "Window Solar Gain (Watts)"), '10': ("PPD", "Percentage Proportion Dissatisfied"), '11': ("PMV", "Predicted Mean Vote"),
                '12': ("Ventilation (l/s)", "Zone Ventilation rate (l/s)"), '13': (u'Ventilation (m\u00b3/h)', u'Zone Ventilation rate (m\u00b3/h)'),
                '14': (u'Infiltration (m\u00b3)',  u'Zone Infiltration (m\u00b3)'), '15': ('Infiltration (ACH)', 'Zone Infiltration rate (ACH)'), '16': (u'CO\u2082 (ppm)', u'Zone CO\u2082 concentration (ppm)'),
                '17': ("Heat loss (W)", "Ventilation Heat Loss (W)"), '18': (u'Flow (m\u00b3/s)', u'Linkage flow (m\u00b3/s)'), '19': ('Opening factor', 'Linkage Opening Factor'),
                '20': ("MRT (K)", "Mean Radiant Temperature (K)"), '21': ('Occupancy', 'Occupancy count'), '22': ("Humidity", "Zone Humidity"),
                '23': ("Fabric HB (W)", "Fabric convective heat balance"), '24': ("Air Heating", "Zone air heating"), '25': ("Air Cooling", "Zone air cooling")}
    return [bpy.props.BoolProperty(name = rnu[str(rnum)][0], description = rnu[str(rnum)][1], default = False) for rnum in range(len(rnu))]

def enresprops(disp):
    return {'0': (0, "resat{}".format(disp), "resaws{}".format(disp), 0, "resawd{}".format(disp), "resah{}".format(disp), 0, "resasb{}".format(disp), "resasd{}".format(disp)), 
           '1': (0, "restt{}".format(disp), "resh{}".format(disp), 0, "restwh{}".format(disp), "restwc{}".format(disp), 0, "ressah{}".format(disp), "ressac{}".format(disp), 0,"reswsg{}".format(disp), "resfhb{}".format(disp)),
            '2': (0, "rescpp{}".format(disp), "rescpm{}".format(disp), 0, 'resmrt{}'.format(disp), 'resocc{}'.format(disp)), 
            '3': (0, "resim{}".format(disp), "resiach{}".format(disp), 0, "resco2{}".format(disp), "resihl{}".format(disp)), 
            '4': (0, "resl12ms{}".format(disp), "reslof{}".format(disp))}
        
def nodestate(self, opstate):
    if self['exportstate'] !=  opstate:
        self.exported = False
        if self.bl_label[0] != '*':
            self.bl_label = '*'+self.bl_label
    else:
        self.exported = True
        if self.bl_label[0] == '*':
            self.bl_label = self.bl_label[1:-1]

def face_centre(ob, obresnum, f):
    if obresnum:
        vsum = mathutils.Vector((0, 0, 0))
        for v in f.vertices:
            vsum = ob.active_shape_key.data[v].co + vsum
        return(vsum/len(f.vertices))
    else:
        return(f.center)

def v_pos(ob, v):
    return(ob.active_shape_key.data[v].co if ob.lires else ob.data.vertices[v].co)
    
def newrow(layout, s1, root, s2):
    row = layout.row()
    row.label(s1)
    row.prop(root, s2)

def retobj(name, fr, node, scene):
    if node.animmenu == "Geometry":
        return(scene['viparams']['objfilebase']+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
    else:
        return(scene['viparams']['objfilebase']+"-{}-{}.obj".format(name.replace(" ", "_"), bpy.context.scene.frame_start))

def retelaarea(node):
    inlinks = [sock.links[0] for sock in node.inputs if sock.bl_idname in ('EnViSSFlowSocket', 'EnViSFlowSocket') and sock.links]
    outlinks = [sock.links[:] for sock in node.outputs if sock.bl_idname in ('EnViSSFlowSocket', 'EnViSFlowSocket') and sock.links]
    inosocks = [link.from_socket for link in inlinks if inlinks and link.from_socket.node.get('zone')]
    outosocks = [link.to_socket for x in outlinks for link in x if link.to_socket.node.get('zone')]
    if outosocks or inosocks:
        elaarea = max([facearea(bpy.data.objects[sock.node.zone], bpy.data.objects[sock.node.zone].data.polygons[int(sock.sn)]) for sock in outosocks + inosocks])
        node["_RNA_UI"] = {"ela": {"max":elaarea}}
        
def objmode():
    if bpy.context.active_object and bpy.context.active_object.type == 'MESH' and not bpy.context.active_object.hide:
        bpy.ops.object.mode_set(mode = 'OBJECT')

def objoin(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select = True
    bpy.context.scene.objects.active = obs[-1]
    bpy.ops.object.join()
    return bpy.context.active_object
    
def retmesh(name, fr, node, scene):
    if node.animmenu in ("Geometry", "Material"):
        return(scene['viparams']['objfilebase']+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
    else:
        return(scene['viparams']['objfilebase']+"-{}-{}.mesh".format(name.replace(" ", "_"), bpy.context.scene.frame_start))

def nodeinputs(node):
    try:
        ins = [i for i in node.inputs if not i.hide]
        if ins and not all([i.links for i in ins]):
            return 0
        elif ins and any([i.links[0].from_node.use_custom_color for i in ins if i.links]):
            return 0
        else:
            inodes = [i.links[0].from_node for i in ins if i.links[0].from_node.inputs]
            for inode in inodes:
                iins = [i for i in inode.inputs if not i.hide]
                if iins and not all([i.is_linked for i in iins]):
                    return 0
                elif iins and not all([i.links[0].from_node.use_custom_color for i in iins if i.is_linked]):
                    return 0
        return 1
    except:
        pass

def retmat(fr, node, scene):
    if node.animmenu == "Material":
        return("{}-{}.rad".format(scene['viparams']['filebase'], fr))
    else:
        return("{}-{}.rad".format(scene['viparams']['filebase'], scene.frame_start))

def retsky(fr, node, scene):
    if node.animmenu == "Time":
        return("{}-{}.sky".format(scene['viparams']['filebase'], fr))
    else:
        return("{}-{}.sky".format(scene['viparams']['filebase'], scene.frame_start))

def nodeexported(self):
    self.exported = 0

def negneg(x):
    x = 0 if float(x) < 0 else x        
    return float(x)

def clearanim(scene, obs):
    for o in obs:
        selobj(scene, o)
        o.animation_data_clear()
        o.data.animation_data_clear()        
        while o.data.shape_keys:
            bpy.context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=True)
            
def clearscene(scene, op):
    for ob in [ob for ob in scene.objects if ob.type == 'MESH' and ob.layers[scene.active_layer]]:
        if ob.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
        if ob.get('lires'):
            scene.objects.unlink(ob)       
        if scene.get('livig') and ob.name in scene['livig']:
            v, f, svv, svf = [0] * 4             
            if 'export' in op.name or 'simulation' in op.name:
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                if "export" in op.name:
                    if bm.faces.layers.int.get('rtindex'):
                        bm.faces.layers.int.remove(bm.faces.layers.int['rtindex'])
                    if bm.verts.layers.int.get('rtindex'):
                        bm.verts.layers.int.remove(bm.verts.layers.int['rtindex'])
                if "simulation" in op.name:
                    while bm.verts.layers.float.get('res{}'.format(v)):
                        livires = bm.verts.layers.float['res{}'.format(v)]
                        bm.verts.layers.float.remove(livires)
                        v += 1
                    while bm.faces.layers.float.get('res{}'.format(f)):
                        livires = bm.faces.layers.float['res{}'.format(f)]
                        bm.faces.layers.float.remove(livires)
                        f += 1
                bm.to_mesh(ob.data)
                bm.free()

    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for lamp in bpy.data.lamps:
        if lamp.users == 0:
            bpy.data.lamps.remove(lamp)

    for oldgeo in bpy.data.objects:
        if oldgeo.users == 0:
            bpy.data.objects.remove(oldgeo)

    for sk in bpy.data.shape_keys:
        if sk.users == 0:
            for keys in sk.keys():
                keys.animation_data_clear()

def retmenu(dnode, axis, mtype):
    if mtype == 'Climate':
        return [dnode.inputs[axis].climmenu, dnode.inputs[axis].climmenu]
    if mtype == 'Zone':
        return [dnode.inputs[axis].zonemenu, dnode.inputs[axis].zonermenu]
    elif mtype == 'Linkage':
        return [dnode.inputs[axis].linkmenu, dnode.inputs[axis].linkrmenu]
    elif mtype == 'External node':
        return [dnode.inputs[axis].enmenu, dnode.inputs[axis].enrmenu]

def retrmenus(innode): 
    rtype = [(restype, restype, "Plot "+restype) for restype in innode['rtypes']]
    ctype = [(clim, clim, "Plot "+clim) for clim in innode['ctypes']]
    ztype = [(zone, zone, "Plot "+zone) for zone in innode['ztypes']]
    zrtype = [(zoner, zoner, "Plot "+zoner) for zoner in innode['zrtypes']]
    ltype = [(link, link, "Plot "+link) for link in innode['ltypes']]
    lrtype = [(linkr, linkr, "Plot "+linkr) for linkr in innode['lrtypes']]
    entype = [(en, en, "Plot "+en) for en in innode['entypes']]
    enrtype = [(enr, enr, "Plot "+enr) for enr in innode['enrtypes']]
    rtypemenu = bpy.props.EnumProperty(items=rtype, name="", description="Result types", default = rtype[0][0])
    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')
    valid = ['EnVi Results']    
    climmenu = bpy.props.EnumProperty(items=ctype, name="", description="Climate type", default = ctype[0][0]) if 'Climate' in innode['rtypes'] else ''     
    zonemenu = bpy.props.EnumProperty(items=ztype, name="", description="Zone", default = ztype[0][0]) if 'Zone' in innode['rtypes'] else ''
    zonermenu = bpy.props.EnumProperty(items=zrtype, name="", description="Zone result", default = zrtype[0][0])  if 'Zone' in innode['rtypes'] else ''
    linkmenu = bpy.props.EnumProperty(items=ltype, name="", description="Flow linkage result", default = ltype[0][0]) if 'Linkage' in innode['rtypes'] else ''
    linkrmenu = bpy.props.EnumProperty(items=lrtype, name="", description="Flow linkage result", default = lrtype[0][0]) if 'Linkage' in innode['rtypes'] else ''
    enmenu = bpy.props.EnumProperty(items=entype, name="", description="External node result", default = entype[0][0]) if 'External node' in innode['rtypes'] else ''
    enrmenu = bpy.props.EnumProperty(items=enrtype, name="", description="External node result", default = enrtype[0][0]) if 'External node' in innode['rtypes'] else ''
    return (valid, statmenu, rtypemenu, climmenu, zonemenu, zonermenu, linkmenu, linkrmenu, enmenu, enrmenu)
        
def processf(pro_op, node):
    ctypes, ztypes, zrtypes, ltypes, lrtypes, entypes, enrtypes = [], [], [], [], [], [], []

    envdict = {'Site Outdoor Air Drybulb Temperature [C] !Hourly': "Temperature (degC)",
               'Site Outdoor Air Relative Humidity [%] !Hourly': 'Humidity (%)',
                'Site Wind Direction [deg] !Hourly': 'Wind Direction (deg)',
                'Site Wind Speed [m/s] !Hourly': 'Wind Speed (m/s)',
                'Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly': "Diffuse Solar (W/m^2)",
                'Site Direct Solar Radiation Rate per Area [W/m2] !Hourly': "Direct Solar (W/m^2)"}
    zresdict = {'Zone Air Temperature [C] !Hourly': "Temperature (degC)",
                'Zone Air Relative Humidity [%] !Hourly': 'Humidity (%)',
                'Zone Air System Sensible Heating Rate [W] !Hourly': 'Heating (W)',
                'Zone Air System Sensible Cooling Rate [W] !Hourly': 'Cooling (W)',
                'Zone Ideal Loads Supply Air Sensible Heating Rate [W] !Hourly': 'Zone air heating (W)',
                'Zone Ideal Loads Supply Air Sensible Cooling Rate [W] !Hourly': 'Zone air cooling (W)',
                'Zone Windows Total Transmitted Solar Radiation Rate [W] !Hourly': 'Solar gain (W)',
                'Zone Infiltration Current Density Volume Flow Rate [m3/s] !Hourly': 'Infiltration (m'+u'\u00b3'+')',
                'Zone Infiltration Air Change Rate [ach] !Hourly': 'Infiltration (ACH)',
                'Zone Mean Air Temperature [C] ! Hourly': 'Mean Temperature ({})'.format(u'\u00b0'),
                'Zone Mean Radiant Temperature [C] !Hourly' :'Mean Radiant ({})'.format(u'\u00b0'), 
                'Zone Thermal Comfort Fanger Model PPD [%] !Hourly' :'PPD',
                'Zone Thermal Comfort Fanger Model PMV [] !Hourly' :'PMV',               
                'AFN Node CO2 Concentration [ppm] !Hourly': 'CO2',
                'Zone Air CO2 Concentration [ppm] !Hourly': 'CO2',
                'Zone Mean Radiant Temperature [C] !Hourly': 'MRT', 'Zone People Occupant Count [] !Hourly': 'Occupancy', 
                'Zone Air Heat Balance Surface Convection Rate [W] !Hourly': 'Heat balance (W)'}
    enresdict = {'AFN Node CO2 Concentration [ppm] !Hourly': 'CO2'}
    lresdict = {'AFN Linkage Node 1 to Node 2 Volume Flow Rate [m3/s] !Hourly': 'Linkage Flow out',
                'AFN Linkage Node 2 to Node 1 Volume Flow Rate [m3/s] !Hourly': 'Linkage Flow in',
                'AFN Surface Venting Window or Door Opening Factor [] !Hourly': 'Opening Factor'}
    resdict = {}
    allresdict = {}
    objlist = []
    
    with open(node.resfilename, 'r') as resfile:
        intro = 1    
        for line in resfile.readlines():
            linesplit = line.strip('\n').split(',')
            if intro:
                if len(linesplit) == 1:
                    intro = 0
                elif linesplit[1] == '1' and '!Hourly' in linesplit[-1]:
                    if linesplit[3] in zresdict and linesplit[2][-10:] == '_OCCUPANCY' and linesplit[2].strip('_OCCUPANCY') not in objlist and 'ExtNode' not in linesplit[2]:
                        objlist.append(linesplit[2].strip('_OCCUPANCY'))
                    elif linesplit[3] in zresdict and linesplit[2][-4:] == '_AIR' and linesplit[2].strip('_AIR') not in objlist and 'ExtNode' not in linesplit[2]:
                        objlist.append(linesplit[2].strip('_AIR'))
                    elif linesplit[3] in zresdict and linesplit[2] not in objlist and 'ExtNode' not in linesplit[2]:
                        objlist.append(linesplit[2])
                    allresdict[linesplit[0]] = []
            elif not intro and len(linesplit) == 2:
                allresdict[linesplit[0]].append(float(linesplit[1]))
            if linesplit[0] in resdict:
                if linesplit[0] == dos:
                    allresdict['Month'].append(int(linesplit[2]))
                    allresdict['Day'].append(int(linesplit[3]))
                    allresdict['Hour'].append(int(linesplit[5]))
                    allresdict['dos'].append(int(linesplit[1]))
                        
            elif len(linesplit) > 3 and linesplit[2] == 'Day of Simulation[]':
                resdict[linesplit[0]], allresdict['Month'],  allresdict['Day'], allresdict['Hour'], allresdict['dos'], dos, node['rtypes'] = ['Day of Simulation'], [], [], [], [], linesplit[0], ['Time']
    
            elif len(linesplit) > 3 and linesplit[2] == 'Environment':
                if 'Climate' not in node['rtypes']:
                    node['rtypes']+= ['Climate']
                try:
                    resdict[linesplit[0]] = ['Climate', envdict[linesplit[3]]]
                    ctypes.append(envdict[linesplit[3]])
                except:
                    pass
    
            elif len(linesplit) > 3 and linesplit[2][-10:] == '_OCCUPANCY' and linesplit[2][:-10] in objlist:
                if 'Zone' not in node['rtypes']:
                   node['rtypes'] += ['Zone']
                try:
                    resdict[linesplit[0]] = [linesplit[2][:-10], zresdict[linesplit[3]]]
                    if linesplit[2][:-10] not in ztypes:
                        ztypes.append(linesplit[2][:-10])
                    if zresdict[linesplit[3]] not in zrtypes:
                        zrtypes.append(zresdict[linesplit[3]])
                except:
                    pass
            
            elif len(linesplit) > 3 and linesplit[2][-4:] == '_AIR' and linesplit[2][:-4] in objlist:
                if 'Zone' not in node['rtypes']:
                   node['rtypes'] += ['Zone']
                try:
                    resdict[linesplit[0]] = [linesplit[2][:-4], zresdict[linesplit[3]]]
                    if linesplit[2][:-4] not in ztypes:
                        ztypes.append(linesplit[2][:-4])
                    if zresdict[linesplit[3]] not in zrtypes:
                        zrtypes.append(zresdict[linesplit[3]])
                except:
                    pass
            
            elif len(linesplit) > 3 and linesplit[2] in objlist:
                if 'Zone' not in node['rtypes']:
                   node['rtypes'] += ['Zone']
                try:
                    resdict[linesplit[0]] = [linesplit[2], zresdict[linesplit[3]]]
                    if linesplit[2] not in ztypes:
                        ztypes.append(linesplit[2])
                    if zresdict[linesplit[3]] not in zrtypes:
                        zrtypes.append(zresdict[linesplit[3]])
                except:
                    pass
            
            elif len(linesplit) > 3 and linesplit[3] in lresdict:
                if 'Linkage' not in node['rtypes']:
                   node['rtypes'] += ['Linkage']
                try:
                    resdict[linesplit[0]] = [linesplit[2], lresdict[linesplit[3]]]
                    if linesplit[2] not in ltypes:
                        ltypes.append(linesplit[2])
                    if lresdict[linesplit[3]] not in lrtypes:
                        lrtypes.append(lresdict[linesplit[3]])
                except:
                    pass
            
            elif len(linesplit) > 3 and linesplit[3] in enresdict:
                if 'External node' not in node['rtypes']:
                   node['rtypes'] += ['External node']
                try:
                    resdict[linesplit[0]] = [linesplit[2], enresdict[linesplit[3]]]
                    if linesplit[2] not in entypes:
                        entypes.append(linesplit[2])
                    if enresdict[linesplit[3]] not in enrtypes:
                        enrtypes.append(enresdict[linesplit[3]])
                except Exception as e:
                    print('ext', e)
            
    node.dsdoy = datetime.datetime(datetime.datetime.now().year, allresdict['Month'][0], allresdict['Day'][0]).timetuple().tm_yday
    node.dedoy = datetime.datetime(datetime.datetime.now().year, allresdict['Month'][-1], allresdict['Day'][-1]).timetuple().tm_yday
    node['dos'], node['resdict'], node['ctypes'], node['ztypes'], node['zrtypes'], node['ltypes'], node['lrtypes'], node['entypes'], node['enrtypes'] = dos, resdict, ctypes, ztypes, zrtypes, ltypes, lrtypes, entypes, enrtypes
    node['allresdict'] = allresdict
    if node.outputs['Results out'].links:
       node.outputs['Results out'].links[0].to_node.update() 

    for o in bpy.data.objects:
        if 'EN_'+o.name.upper() in objlist:
            o['enviresults'] = {}
    for zres in resdict.items():
        for o in bpy.data.objects:
            if ['EN_'+o.name.upper(), 'Zone air heating (W)'] == zres[1]:            
                o['enviresults']['Zone air heating (kWh)'] = sum(allresdict[zres[0]])*0.001
            elif ['EN_'+o.name.upper(), 'Zone air cooling (W)'] == zres[1]:            
                o['enviresults']['Zone air cooling (kWh)'] = sum(allresdict[zres[0]])*0.001
                
#    node['envdict'], node['zresdict'], node['enresdict'], node['lresdict'] = envdict, zresdict, enresdict, lresdict

def iprop(iname, idesc, imin, imax, idef):
    return(IntProperty(name = iname, description = idesc, min = imin, max = imax, default = idef))
def eprop(eitems, ename, edesc, edef):
    return(EnumProperty(items=eitems, name = ename, description = edesc, default = edef))
def bprop(bname, bdesc, bdef):
    return(BoolProperty(name = bname, description = bdesc, default = bdef))
def sprop(sname, sdesc, smaxlen, sdef):
    return(StringProperty(name = sname, description = sdesc, maxlen = smaxlen, default = sdef))
def fprop(fname, fdesc, fmin, fmax, fdef):
    return(FloatProperty(name = fname, description = fdesc, min = fmin, max = fmax, default = fdef))
def fvprop(fvsize, fvname, fvattr, fvdef, fvsub, fvmin, fvmax):
    return(FloatVectorProperty(size = fvsize, name = fvname, attr = fvattr, default = fvdef, subtype =fvsub, min = fvmin, max = fvmax))
def niprop(iname, idesc, imin, imax, idef):
        return(IntProperty(name = iname, description = idesc, min = imin, max = imax, default = idef, update = nodeexported))
def neprop(eitems, ename, edesc, edef):
    return(EnumProperty(items=eitems, name = ename, description = edesc, default = edef, update = nodeexported))
def nbprop(bname, bdesc, bdef):
    return(BoolProperty(name = bname, description = bdesc, default = bdef, update = nodeexported))
def nsprop(sname, sdesc, smaxlen, sdef):
    return(StringProperty(name = sname, description = sdesc, maxlen = smaxlen, default = sdef, update = nodeexported))
def nfprop(fname, fdesc, fmin, fmax, fdef):
    return(FloatProperty(name = fname, description = fdesc, min = fmin, max = fmax, default = fdef, update = nodeexported))
def nfvprop(fvname, fvattr, fvdef, fvsub):
    return(FloatVectorProperty(name=fvname, attr = fvattr, default = fvdef, subtype = fvsub, update = nodeexported))

def boundpoly(obj, mat, poly, enng):
    if mat.envi_boundary:
        nodes = [node for node in enng.nodes if hasattr(node, 'zone') and node.zone == obj.name]
        for node in nodes:
            insock = node.inputs['{}_{}_b'.format(mat.name, poly.index)]
            outsock = node.outputs['{}_{}_b'.format(mat.name, poly.index)]              
            if insock.links:
                bobj = bpy.data.objects[insock.links[0].from_node.zone]
                bpoly = bobj.data.polygons[int(insock.links[0].from_socket.name.split('_')[-2])]
                if bobj.data.materials[bpoly.material_index] == mat:# and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                    return(("Surface", node.inputs['{}_{}_b'.format(mat.name, poly.index)].links[0].from_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))
        
            elif outsock.links:
                bobj = bpy.data.objects[outsock.links[0].to_node.zone]
                bpoly = bobj.data.polygons[int(outsock.links[0].to_socket.name.split('_')[-2])]
                if bobj.data.materials[bpoly.material_index] == mat:# and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                    return(("Surface", node.outputs['{}_{}_b'.format(mat.name, poly.index)].links[0].to_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))
            return(("Outdoors", "", "SunExposed", "WindExposed"))

    elif mat.envi_thermalmass:
        return(("Adiabatic", "", "NoSun", "NoWind"))
    else:
        return(("Outdoors", "", "SunExposed", "WindExposed"))

def objvol(op, obj):
    bm , floor, roof, mesh = bmesh.new(), [], [], obj.data
    bm.from_object(obj, bpy.context.scene)
    for f in mesh.polygons:
        if obj.data.materials[f.material_index].envi_con_type == 'Floor':
            floor.append((facearea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
        elif obj.data.materials[f.material_index].envi_con_type == 'Roof':
            roof.append((facearea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
    zfloor = list(zip(*floor))
    if not zfloor and op:
        op.report({'INFO'},"Zone has no floor area")

    return(bm.calc_volume()*obj.scale[0]*obj.scale[1]*obj.scale[2])

def ceilheight(obj, vertz):
    mesh = obj.data
    for vert in mesh.vertices:
        vertz.append((obj.matrix_world * vert.co)[2])
    zmax, zmin = max(vertz), min(vertz)
    ceiling = [max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) > 0.9 * zmax]
    floor = [min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) < zmin + 0.1 * (zmax - zmin)]
    return(sum(ceiling)/len(ceiling)-sum(floor)/len(floor))

def vertarea(mesh, vert):
    area = 0
    faces = [face for face in vert.link_faces] 
    if len(faces) > 1:
        for f, face in enumerate(faces):
            ovs = []
            fvs = [le.verts[(0, 1)[le.verts[0] == vert]] for le in vert.link_edges]
            ofaces = [oface for oface in faces if len([v for v in oface.verts if v in face.verts]) == 2]    
            for oface in ofaces:
                ovs.append([i for i in face.verts if i in oface.verts])
            if len(ovs) == 1:
                if hasattr(mesh.verts, "ensure_lookup_table"):
                    mesh.verts.ensure_lookup_table()
                sedgevs = (vert.index, [v.index for v in fvs if v not in ovs][0])
                sedgemp = mathutils.Vector([((mesh.verts[sedgevs[0]].co)[i] + (mesh.verts[sedgevs[1]].co)[i])/2 for i in range(3)])
                eps = [mathutils.geometry.intersect_line_line(face.calc_center_median(), ofaces[0].calc_center_median(), ovs[0][0].co, ovs[0][1].co)[1]] + [sedgemp]
            elif len(ovs) == 2:
                eps = [mathutils.geometry.intersect_line_line(face.calc_center_median(), ofaces[i].calc_center_median(), ovs[i][0].co, ovs[i][1].co)[1] for i in range(2)]
            area += mathutils.geometry.area_tri(vert.co, *eps) + mathutils.geometry.area_tri(face.calc_center_median(), *eps)
    elif len(faces) == 1:
        eps = [(ev.verts[0].co +ev.verts[1].co)/2 for ev in vert.link_edges]
        eangle = (vert.link_edges[0].verts[0].co - vert.link_edges[0].verts[1].co).angle(vert.link_edges[1].verts[0].co - vert.link_edges[1].verts[1].co)
        area = mathutils.geometry.area_tri(vert.co, *eps) + mathutils.geometry.area_tri(faces[0].calc_center_median(), *eps) * 2*pi/eangle
    return area       

def facearea(obj, face):
    omw = obj.matrix_world
    vs = [omw*mathutils.Vector(face.center)] + [omw*obj.data.vertices[v].co for v in face.vertices] + [omw*obj.data.vertices[face.vertices[0]].co]
    return(vsarea(obj, vs))

def vsarea(obj, vs):
    if len(vs) == 5:
        cross = mathutils.Vector.cross(vs[3]-vs[1], vs[3]-vs[2])
        return(0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5)
    else:
        i, area = 0, 0
        while i < len(vs) - 2:
            cross = mathutils.Vector.cross(vs[0]-vs[1+i], vs[0]-vs[2+i])
            area += 0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5
            i += 1
        return(area)

def wind_rose(maxws, wrsvg, wrtype):
    pa, zp, lpos, scene, vs = 0, 0, [], bpy.context.scene, []    
    bm = bmesh.new()
    wrme = bpy.data.meshes.new("Wind_rose")   
    wro = bpy.data.objects.new('Wind_rose', wrme)     
    scene.objects.link(wro)
    scene.objects.active = wro
    wro.select, wro.location = True, (0, 0 ,0)
    
    with open(wrsvg, 'r') as svgfile:  
        svglines = svgfile.readlines()     
        for line in svglines:
            if "<svg height=" in line:
                dimen = int(line.split('"')[1].strip('pt'))
                scale = 0.04 * dimen
            if '/>' in line:
                lcolsplit = line.split(';')
                for lcol in lcolsplit: 
                    if 'style="fill:#' in lcol and lcol[-6:] != 'ffffff':
                        fillrgb = colors.hex2color(lcol[-7:])
                        if 'wr-{}'.format(lcol[-6:]) not in [mat.name for mat in bpy.data.materials]:
                            bpy.data.materials.new('wr-{}'.format(lcol[-6:]))
                        bpy.data.materials['wr-{}'.format(lcol[-6:])].diffuse_color = fillrgb
                        if 'wr-{}'.format(lcol[-6:]) not in [mat.name for mat in wro.data.materials]:
                            bpy.ops.object.material_slot_add()
                            wro.material_slots[-1].material = bpy.data.materials['wr-{}'.format(lcol[-6:])]  
                
        for line in svglines:
            linesplit = line.split(' ')
            if '<path' in line:
                pa = 1
            if pa and line[0] == 'M':
                spos = [((float(linesplit[0][1:])- dimen/2) * 0.1, (float(linesplit[1]) - dimen/2) * -0.1, 0.05)]
            if pa and line[0] == 'L':
                lpos.append(((float(linesplit[0][1:]) - dimen/2) * 0.1, (float(linesplit[1].strip('"')) - dimen/2) *-0.1, 0.05))
            if pa and '/>' in line:
                lcolsplit = line.split(';')
                for lcol in lcolsplit:                
                    if 'style="fill:#' in lcol and lcol[-6:] != 'ffffff':
                        for pos in spos + lpos:
                            vs.append(bm.verts.new(pos))                        
                        if len(vs) > 2:
                            nf = bm.faces.new(vs)
                            nf.material_index = wro.data.materials[:].index(wro.data.materials['wr-{}'.format(lcol[-6:])])                            
                            if wrtype in ('2', '3', '4'):
                                zp += 0.0005 * scale 
                                for vert in nf.verts:
                                    vert.co[2] = zp
                bmesh.ops.remove_doubles(bm, verts=vs, dist = scale * 0.01)
                pa, lpos, vs = 0, [], []  

            if 'wr-000000' not in [mat.name for mat in bpy.data.materials]:
                bpy.data.materials.new('wr-000000')
            bpy.data.materials['wr-000000'].diffuse_color = (0, 0, 0)
            if 'wr-000000' not in [mat.name for mat in wro.data.materials]:
                bpy.ops.object.material_slot_add()
                wro.material_slots[-1].material = bpy.data.materials['wr-000000']
            

    if wrtype in ('0', '1', '3', '4'):            
        thick = scale * 0.005 if wrtype == '4' else scale * 0.0025
        faces = bmesh.ops.inset_individual(bm, faces=bm.faces, thickness = thick, use_even_offset = True)['faces']
        if wrtype == '4':
            [bm.faces.remove(f) for f in bm.faces if f not in faces]
        else:
            for face in faces:
                face.material_index = wro.data.materials[:].index(wro.data.materials['wr-000000'])

    bm.to_mesh(wro.data)
    bm.free()
    
    bpy.ops.mesh.primitive_circle_add(vertices = 132, fill_type='NGON', radius=scale*1.2, view_align=False, enter_editmode=False, location=(0, 0, 0))
    wrbo = bpy.context.active_object
    if 'wr-base'not in [mat.name for mat in bpy.data.materials]:
        bpy.data.materials.new('wr-base')
        bpy.data.materials['wr-base'].diffuse_color = (1,1,1)
    bpy.ops.object.material_slot_add()
    wrbo.material_slots[-1].material = bpy.data.materials['wr-base']
    return (objoin((wrbo, wro)), scale)
    

def compass(loc, scale, wro, mat):
    txts = []
    come = bpy.data.meshes.new("Compass")   
    coo = bpy.data.objects.new('Compass', come)
    coo.location = loc
    bpy.context.scene.objects.link(coo)
    bpy.context.scene.objects.active = coo
    bpy.ops.object.material_slot_add()
    coo.material_slots[-1].material = mat
    bm = bmesh.new()
    matrot = Matrix.Rotation(pi*0.25, 4, 'Z')
    
    for i in range(1, 11):
        bmesh.ops.create_circle(bm, cap_ends=False, diameter=scale*i*0.1, segments=132,  matrix=Matrix.Rotation(pi/64, 4, 'Z')*Matrix.Translation((0, 0, scale*0.005)))
    
    for edge in bm.edges:
        edge.select_set(False) if edge.index % 3 or edge.index > 1187 else edge.select_set(True)
    
    bmesh.ops.delete(bm, geom = [edge for edge in bm.edges if edge.select], context = 2)
    newgeo = bmesh.ops.extrude_edge_only(bm, edges = bm.edges, use_select_history=False)
    
    for v, vert in enumerate(newgeo['geom'][:1320]):
        vert.co = vert.co + (vert.co - coo.location).normalized() * scale * (0.0025, 0.005)[v > 1187]
        vert.co[2] = scale*0.005
           
    bmesh.ops.create_circle(bm, cap_ends=True, diameter=scale *0.005, segments=8, matrix=Matrix.Rotation(-pi/8, 4, 'Z')*Matrix.Translation((0, 0, scale*0.005)))
    matrot = Matrix.Rotation(pi*0.25, 4, 'Z')
    tmatrot = Matrix.Rotation(0, 4, 'Z')
    direc = Vector((0, 1, 0))
    for i, edge in enumerate(bm.edges[-8:]):
        verts = bmesh.ops.extrude_edge_only(bm, edges = [edge], use_select_history=False)['geom'][:2]
        for vert in verts:
            vert.co = 1.5*vert.co + 1.025*scale*(tmatrot*direc)
            vert.co[2] = scale*0.005
        bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=Vector(loc) + scale*1.05*(tmatrot*direc), rotation=tmatrot.to_euler())
        txt = bpy.context.active_object
        txt.scale, txt.data.body, txt.data.align, txt.location[2]  = (scale*0.1, scale*0.1, scale*0.1), ('N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE')[i], 'CENTER', txt.location[2] + scale*0.005
        
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.material_slot_add()
        txt.material_slots[-1].material = mat
        txts.append(txt)
        tmatrot = tmatrot * matrot
    bm.to_mesh(come)
    bm.free()

    return objoin(txts + [coo] + [wro])

def windnum(maxws, loc, scale, wr):
    txts = []
    matrot = Matrix.Rotation(-pi*0.125, 4, 'Z')
    direc = Vector((0, 1, 0))
    for i in range(5):
        bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((i+1)/5)*scale*(matrot*direc))
        txt = bpy.context.active_object
        txt.data.body, txt.scale, txt.location[2] = '{:.1f}'.format((i+1)*maxws/5), (scale*0.05, scale*0.05, scale*0.05), scale*0.01
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.material_slot_add()
        txt.material_slots[-1].material = bpy.data.materials['wr-000000']
        txts.append(txt)
    objoin(txts + [wr]).name = 'Wind Rose'
    bpy.context.active_object['VIType']  = 'Wind_Plane'
    
def windcompass():
    rad1 = 1.4
    dep = 2.8
    lettwidth = 0.3
    lettheight = 0.15
    bpy.ops.mesh.primitive_torus_add(location=(0.0, 0.0, 0.0), view_align=False, rotation=(0.0, 0.0, 0.0), major_segments=48, minor_segments=12, major_radius=2.5, minor_radius=0.01)
    bpy.ops.mesh.primitive_cone_add(location=(0.0, rad1, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, 0.0), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=((rad1**2/2)**0.5, (rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.25), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(rad1, 0.0, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.5), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=((rad1**2/2)**0.5, -(rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.75), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(0.0, -rad1, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-(rad1**2/2)**0.5, -(rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.25), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-rad1, 0.0, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.5), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-(rad1**2/2)**0.5, (rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.75), radius1 = 0.01, depth = dep)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettheight*1.3, dep, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'N'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((dep**2/2)**0.5-lettheight, (1+dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*-0.25))
    txt = bpy.context.active_object
    txt.data.body = 'NE'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(dep, -lettheight, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'W'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((dep**2/2)**0.5, -lettwidth-lettheight-(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*0.25))
    txt = bpy.context.active_object
    txt.data.body = 'SW'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettwidth/3, -dep-lettwidth*1.3, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'S'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-(dep**2/2)**0.5-lettwidth-0.1, -lettwidth/2-(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*-0.25))
    txt = bpy.context.active_object
    txt.data.body = 'SE'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettwidth-dep, -lettheight, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'E'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-(dep**2/2)**0.5-lettwidth, -(lettheight+lettwidth)*0.5+(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*0.25))
    txt = bpy.context.active_object
    txt.data.body = 'NW'
    txt.scale = (0.4, 0.4, 0.4)
    arrverts = ((0.05, -0.25, 0.0), (-0.05, -0.25, 0.0), (0.05, 0.25, 0.0), (-0.05, 0.25, 0.0), (0.15, 0.1875, 0.0), (-0.15, 0.1875, 0.0), (0.0, 0.5, 0.0))
    arrfaces = ((1, 0, 2, 3), (2, 4, 6, 5, 3))
    arrme = bpy.data.meshes.new('windarrow')
    arrob = bpy.data.objects.new('windarrow', arrme)
    arrme.from_pydata(arrverts, [], arrfaces)
    arrme.update()
    bpy.context.scene.objects.link(arrob)

def rgb2h(rgb):
    return colorsys.rgb_to_hsv(rgb[0]/255.0,rgb[1]/255.0,rgb[2]/255.0)[0]

def livisimacc(simnode, connode):
    return(simnode.csimacc if connode.bl_label in ('LiVi Compliance', 'LiVi CBDM') else simnode.simacc)

def drawpoly(x1, y1, x2, y2, a, r, g, b):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(r, g, b, a)
    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glVertex2i(x1, y2)
    bgl.glVertex2i(x2, y2)
    bgl.glVertex2i(x2, y1)
    bgl.glVertex2i(x1, y1)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)
    
def drawtri(posx, posy, l, d, hscale, radius):
    r, g, b = colorsys.hsv_to_rgb(0.75 - l * 0.75, 1.0, 1.0)
    a = 0.9
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glColor4f(r, g, b, a)
    bgl.glVertex2f(posx - l * 0.5  * hscale *(radius - 20)*sin(d*pi/180), posy - l * 0.5 * hscale * (radius - 20)*cos(d*pi/180)) 
    bgl.glVertex2f(posx + hscale * (l**0.5) *(radius/4 - 5)*cos(d*pi/180), posy - hscale * (l**0.5) *(radius/4 - 5)*sin(d*pi/180))    
    bgl.glVertex2f(posx + l**0.5 * hscale *(radius - 20)*sin(d*pi/180), posy + l**0.5 * hscale * (radius - 20)*cos(d*pi/180)) 
    bgl.glVertex2f(posx - hscale * (l**0.5) *(radius/4 - 5)*cos(d*pi/180), posy + hscale * (l**0.5) *(radius/4 - 5)*sin(d*pi/180))
    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)
    
def drawcircle(center, radius, resolution, fill, a, r, g, b):
    bgl.glColor4f(r, g, b, a)
    if fill:
        bgl.glBegin(bgl.GL_POLYGON)
    else:
        bgl.glBegin(bgl.GL_LINE_STRIP)

    for i in range(resolution+1):
        vec = Vector((cos(i/resolution*2*pi), sin(i/resolution*2*pi)))
        v = vec * radius + center
        bgl.glVertex2f(v.x, v.y)
    bgl.glEnd()

def drawloop(x1, y1, x2, y2):
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(x1, y2)
    bgl.glVertex2i(x2, y2)
    bgl.glVertex2i(x2, y1)
    bgl.glVertex2i(x1, y1)
    bgl.glEnd()

def drawfont(text, fi, lencrit, height, x1, y1):
    blf.position(fi, x1, height - y1 - lencrit*26, 0)
    blf.draw(fi, text)

def mtx2vals(mtxlines, fwd, node):
    for m, mtxline in enumerate(mtxlines):
        if 'NROWS' in mtxline:
            patches = int(mtxline.split('=')[1])
        elif 'NCOLS' in mtxline:
            hours = int(mtxline.split('=')[1])
        elif mtxline == '\n':
            startline = m + 1
            break

    vecvals, vals, hour, patch = numpy.array([[x%24, (fwd+int(x/24))%7] + [0 for p in range(patches)] for x in range(hours)]), numpy.zeros((patches)), 0, 2
    
    for fvals in mtxlines[startline:]:
        if fvals == '\n':
            patch += 1
            hour = 0
        else:
            sumvals = sum([float(lv) for lv in fvals.split(" ") if not isnan(eval(lv))])/3
            if sumvals > 0:
                vals[patch - 2] += sumvals
                vecvals[hour][patch] = sumvals
            hour += 1
    return(vecvals.tolist(), vals)

def bres(scene, o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    if scene['liparams']['cp'] == '1':
        rtlayer = bm.verts.layers.int['cindex']
        reslayer = bm.verts.layers.float['res{}'.format(scene.frame_current)]
        res = [v[reslayer] for v in bm.verts if v[rtlayer] > 0]
    elif scene['liparams']['cp'] == '0':
        rtlayer = bm.faces.layers.int['cindex']
        reslayer = bm.faces.layers.float['res{}'.format(scene.frame_current)]
        res = [f[reslayer] for f in bm.faces if f[rtlayer] > 0]
    bm.free()
    return res
    
def framerange(scene, anim):
    if anim == 'Static':
        return(range(scene.frame_current, scene.frame_current +1))
    else:
        return(range(scene.frame_start, scene.fe + 1))

def frameindex(scene, anim):
    if anim == 'Static':
        return(range(0, 1))
    else:
        return(range(0, scene.frame_end - scene.frame_start +1))

def retobjs(otypes):
    scene = bpy.context.scene
    if otypes == 'livig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and len(geo.data.materials) and not (geo.parent and os.path.isfile(geo.iesname)) and not geo.lila \
        and geo.hide == False and geo.layers[scene.active_layer] == True and geo.lires == 0 and geo.get('VIType') not in ('SPathMesh', 'SunMesh', 'Wind_Plane', 'SkyMesh')])
    elif otypes == 'livigengeo':
        return([geo for geo in scene.objects if geo.type == 'MESH' and not any([m.livi_sense for m in geo.data.materials])])
    elif otypes == 'livigengeosel':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.select == True and not any([m.livi_sense for m in geo.data.materials])])
    elif otypes == 'livil':
        return([geo for geo in scene.objects if (geo.type == 'LAMP' or geo.lila) and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livic':
        return([geo for geo in scene.objects if geo.type == 'MESH' and li_calcob(geo, 'livi') and geo.lires == 0 and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livir':
        return([geo for geo in bpy.data.objects if geo.type == 'MESH' and True in [m.livi_sense for m in geo.data.materials] and geo.licalc and geo.layers[scene.active_layer] == True])
    elif otypes == 'envig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.hide == False and geo.layers[0] == True])
    elif otypes == 'ssc':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.licalc and geo.lires == 0 and geo.hide == False and geo.layers[scene.active_layer] == True])

def viewdesc(context):
    region = context.region
    width, height = region.width, region.height
    mid_x, mid_y = width/2, height/2
    return(mid_x, mid_y, width, height)
    
def skfpos(o, frame, vis):
    vcos = [o.matrix_world*o.data.shape_keys.key_blocks[str(frame)].data[v].co for v in vis]
    maxx = max([vco[0] for vco in vcos])
    minx = min([vco[0] for vco in vcos])
    maxy = max([vco[1] for vco in vcos])
    miny = min([vco[1] for vco in vcos])
    maxz = max([vco[2] for vco in vcos])
    minz = min([vco[2] for vco in vcos])
    return mathutils.Vector(((maxx + minx) * 0.5, (maxy + miny) * 0.5, (maxz + minz) * 0.5))

def selmesh(sel):
    bpy.ops.object.mode_set(mode = 'EDIT')
    if sel == 'selenm':
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
    elif sel == 'desel':
        bpy.ops.mesh.select_all(action='DESELECT')
    elif sel in ('delf', 'rd'):
        if sel == 'delf':
            bpy.ops.mesh.delete(type = 'FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='DESELECT')
    elif sel in ('SELECT', 'INVERT', 'PASS'):
        if sel in ('SELECT', 'INVERT'):
            bpy.ops.mesh.select_all(action=sel)    
        bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode = 'OBJECT')

def draw_index(context, leg, mid_x, mid_y, width, height, posis, res):
    vecs = [mathutils.Vector((vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3])) for vec in posis]
    xs = [int(mid_x + vec[0] * mid_x) for vec in vecs]
    ys = [int(mid_y + vec[1] * mid_y) for vec in vecs]
    [(blf.position(0, xs[ri], ys[ri], 0), blf.draw(0, ('{:.1f}', '{:.0f}')[r > 100 or context.scene.resnode == 'VI Sun Path'].format(r))) for ri, r in enumerate(res) if (leg == 1 and (xs[ri] > 120 or ys[ri] < height - 530)) or leg == 0]
        
def edgelen(ob, edge):
    omw = ob.matrix_world
    vdiff = omw * (ob.data.vertices[edge.vertices[0]].co - ob.data.vertices[edge.vertices[1]].co)
    mathutils.Vector(vdiff).length

def sunpath1(self, context):
    sunpath()

def sunpath2(scene):
    sunpath()

def sunpath():
    # For future reference I can also project an emmisve sky texture on a sphere using the normal texture coordinate.
    scene = bpy.context.scene
    sun = [ob for ob in scene.objects if ob.get('VIType') == 'Sun'][0]
    skysphere = [ob for ob in scene.objects if ob.get('VIType') == 'SkyMesh'][0]

    if 0 in (sun['solhour'] == scene.solhour, sun['solday'] == scene.solday, sun['soldistance'] == scene.soldistance):
        sunob = [ob for ob in scene.objects if ob.get('VIType') == 'SunMesh'][0]
        spathob = [ob for ob in scene.objects if ob.get('VIType') == 'SPathMesh'][0]
        beta, phi = solarPosition(scene.solday, scene.solhour, scene['latitude'], scene['longitude'])[2:]
        sunob.location.z = sun.location.z = spathob.location.z + scene.soldistance * sin(beta)
        sunob.location.x = sun.location.x = spathob.location.x -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5  * sin(phi)
        sunob.location.y = sun.location.y = spathob.location.y -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5 * cos(phi)
        sun.rotation_euler = pi * 0.5 - beta, 0, -phi
        spathob.scale = 3 * [scene.soldistance/100]
        skysphere.scale = 3 * [1.05 * scene.soldistance/100]
        sunob.scale = 3*[scene.soldistance/100]

        if scene.render.engine == 'CYCLES':
            if bpy.data.worlds['World'].node_tree:
                if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                    bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)
            if sun.data.node_tree:
                for blnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Blackbody']:
                    blnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5 if beta > 0 else 2000
                for emnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Emission']:
                    emnode.inputs[1].default_value = 10 * sin(beta) if beta > 0 else 0
            if sunob.data.materials[0].node_tree:
                for smblnode in [node for node in sunob.data.materials[0].node_tree.nodes if sunob.data.materials and node.bl_label == 'Blackbody']:
                    smblnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5 if beta > 0 else 2000
            if skysphere and not skysphere.hide and skysphere.data.materials[0].node_tree:
                if 'Sky Texture' in [no.bl_label for no in skysphere.data.materials[0].node_tree.nodes]:
                    skysphere.data.materials[0].node_tree.nodes['Sky Texture'].sun_direction = sin(phi), -cos(phi), sin(beta)

        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance
    else:
        return

def epwlatilongi(scene, node):
    with open(node.weather, "r") as epwfile:
        fl = epwfile.readline()
        latitude, longitude = float(fl.split(",")[6]), float(fl.split(",")[7])
#    else:
#        latitude, longitude = node.latitude, node.longitude
    return latitude, longitude

#Compute solar position (altitude and azimuth in degrees) based on day of year (doy; integer), local solar time (lst; decimal hours), latitude (lat; decimal degrees), and longitude (lon; decimal degrees).
def solarPosition(doy, lst, lat, lon):
    #Set the local standard time meridian (lsm) (integer degrees of arc)
    lsm = round(lon/15, 0)*15
    #Approximation for equation of time (et) (minutes) comes from the Wikipedia article on Equation of Time
    b = 2*pi*(doy-81)/364
    et = 9.87 * sin(2*b) - 7.53 * cos(b) - 1.5 * sin(b)
    #The following formulas adapted from the 2005 ASHRAE Fundamentals, pp. 31.13-31.16
    #Conversion multipliers
    degToRad = 2*pi/360
    radToDeg = 1/degToRad
    #Apparent solar time (ast)
    ast = lst + et/60 + (lsm-lon)/15
    #Solar declination (delta) (radians)
    delta = degToRad*23.45 * sin(2*pi*(284+doy)/365)
    #Hour angle (h) (radians)
    h = degToRad*15 * (ast-12)
     #Local latitude (l) (radians)
    l = degToRad*lat
    #Solar altitude (beta) (radians)
    beta = asin(cos(l) * cos(delta) * cos(h) + sin(l) * sin(delta))
    #Solar azimuth phi (radians)
    phi = acos((sin(beta) * sin(l) - sin(delta))/(cos(beta) * cos(l)))
    #Convert altitude and azimuth from radians to degrees, since the Spatial Analyst's Hillshade function inputs solar angles in degrees
    altitude = radToDeg*beta
    phi = 2*pi - phi if ast<=12 or ast >= 24 else phi
    azimuth = radToDeg*phi
    return([altitude, azimuth, beta, phi])

def set_legend(ax):
    l = ax.legend(borderaxespad = -4)
    plt.setp(l.get_texts(), fontsize=8)

def wr_axes():
    fig = plt.figure(figsize=(8, 8), dpi=150, facecolor='w', edgecolor='w')
    rect = [0.1, 0.1, 0.8, 0.8]
    ax = WindroseAxes(fig, rect, axisbg='w')
    fig.add_axes(ax)
    return(fig, ax)

def skframe(pp, scene, oblist, anim):
    for frame in range(scene.fs, scene.fe + 1):
        scene.frame_set(frame)
        for o in [o for o in oblist if o.data.shape_keys]:
            for shape in o.data.shape_keys.key_blocks:
                if shape.name.isdigit():
                    shape.value = shape.name == str(frame)
                    shape.keyframe_insert("value")

def gentarget(tarnode, result):
    if tarnode.stat == '0':
        res = sum(result)/len(result)
    elif tarnode.stat == '1':
        res = max(result)
    elif tarnode.stat == '2':
        res = min(result)
    elif tarnode.stat == '3':
        res = sum(result)

    if tarnode.value > res and tarnode.ab == '0':
        return(1)
    elif tarnode.value < res and tarnode.ab == '1':
        return(1)
    else:
        return(0)

def selobj(scene, geo):
    for ob in scene.objects:
        ob.select = True if ob == geo else False
    scene.objects.active = geo

def nodeid(node):
    for ng in bpy.data.node_groups:
        if node in ng.nodes[:]:
            return node.name+'@'+ng.name

def nodecolour(node, prob):
    (node.use_custom_color, node.color) = (1, (1.0, 0.3, 0.3)) if prob else (0, (1.0, 0.3, 0.3))
    return not prob

def remlink(node, links):
    for link in links:
        bpy.data.node_groups[node['nodeid'].split('@')[1]].links.remove(link)

def epentry(header, params, paramvs):
    return '{}\n'.format(header+(',', '')[header == ''])+'\n'.join([('    ', '')[header == '']+'{:{width}}! - {}'.format(str(pv[0])+(',', ';')[pv[1] == params[-1]], pv[1], width = 80 + (0, 4)[header == '']) for pv in zip(paramvs, params)]) + ('\n\n', '')[header == '']

def sockhide(node, lsocknames):
    try:
        for ins in [insock for insock in node.inputs if insock.name in lsocknames]:
            node.outputs[ins.name].hide = True if ins.links else False
        for outs in [outsock for outsock in node.outputs if outsock.name in lsocknames]:
            node.inputs[outs.name].hide = True if outs.links else False
    except Exception as e:
        print('sockhide', e)

def socklink(sock, ng):
    try:
        valid1 = sock.valid if not sock.get('valid') else sock['valid']
        for link in sock.links:
            valid2 = link.to_socket.valid if not link.to_socket.get('valid') else link.to_socket['valid'] 
            if not set(valid1)&set(valid2):
                bpy.data.node_groups[ng].links.remove(link)
    except Exception as e:
        print(e)
    
def rettimes(ts, fs, us):
    tot = range(min(len(ts), len(fs), len(us)))
    fstrings, ustrings, tstrings = [[] for t in tot],  [[] for t in tot], ['Through: {}/{}'.format(dtdf(ts[t]).month, dtdf(ts[t]).day) for t in tot]
    for t in tot:
        fstrings[t]= ['For: '+''.join(f.strip()) for f in fs[t].split(' ') if f.strip(' ') != '']
        for uf, ufor in enumerate(us[t].split(';')):
            ustrings[t].append([])
            for ut, utime in enumerate(ufor.split(',')):
                ustrings[t][uf].append(['Until: '+','.join([u.strip() for u in utime.split(' ') if u.strip(' ')])])
    return(tstrings, fstrings, ustrings)
    
def epschedwrite(name, stype, ts, fs, us):
    params = ['Name', 'Schedule Type Limits Name']
    paramvs = [name, stype]
    for t in range(len(ts)):
        params.append('Field {}'.format(len(params)-2))
        paramvs .append(ts[t])
        for f in range(len(fs[t])):
            params.append('Field {}'.format(len(params)-2))
            paramvs.append(fs[t][f])
            for u in range(len(us[t][f])):
                params.append('Field {}'.format(len(params)-2))
                paramvs.append(us[t][f][u][0])
    return epentry('Schedule:Compact', params, paramvs)
    
def li_calcob(ob, li):
    if not ob.data.materials:
        return False
    else:
        ob.licalc = 1 if [face.index for face in ob.data.polygons if (ob.data.materials[face.material_index].mattype == '2', ob.data.materials[face.material_index].mattype == '1')[li == 'livi']] else 0
        return ob.licalc

# FloVi functions
def fvboundwrite(o):
    boundary = ''
    for mat in o.data.materials:        
        boundary += "  {}\n  {{\n    type {};\n    faces\n    (\n".format(mat.name, ("wall", "patch", "patch", "symmetryPlane", "empty")[int(mat.flovi_bmb_type)])#;\n\n"
        faces = [face for face in o.data.polygons if o.data.materials[face.material_index] == mat]
        for face in faces:
            boundary += "      ("+" ".join([str(v) for v in face.vertices])+")\n"
        boundary += "    );\n  }\n"
#        fvvarwrite(mat, solver)
    boundary += ");\n\nmergePatchPairs\n(\n);"
    return boundary
#    self.p += "}"   
#    self.U += "}" 
    
def fvbmwrite(o, expnode):
    omw, bmovs = o.matrix_world, [vert for vert in o.data.vertices]
    xvec, yvec, zvec = (omw*bmovs[3].co - omw*bmovs[0].co).normalized(), (omw*bmovs[2].co - omw*bmovs[3].co).normalized(), (omw*bmovs[4].co - omw*bmovs[0].co).normalized() 
    ofvpos = [[(omw*bmov.co - omw*bmovs[0].co)*vec for vec in (xvec, yvec, zvec)] for bmov in bmovs]
    bmdict = "FoamFile\n  {\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  object      blockMeshDict;\n  }\n\nconvertToMeters 1.0;\n\n" 
    bmdict += "vertices\n(\n" + "\n".join(["  ({0:.3f} {1:.3f} {2:.3f})" .format(*ofvpo) for ofvpo in ofvpos]) +"\n);\n\n"
    bmdict += "blocks\n(\n  hex (0 3 2 1 4 7 6 5) ({} {} {}) simpleGrading ({} {} {})\n);\n\n".format(expnode.bm_xres, expnode.bm_yres, expnode.bm_zres, expnode.bm_xgrad, expnode.bm_ygrad, expnode.bm_zgrad) 
    bmdict += "edges\n(\n);\n\n"  
    bmdict += "boundary\n(\n" 
    bmdict += fvboundwrite(o)
    return bmdict
    
def fvblbmgen(mats, ffile, vfile, bfile, meshtype):
    scene = bpy.context.scene
    matfacedict = {mat.name:[0, 0] for mat in mats}
    
    for line in bfile.readlines():
        if line.strip() in matfacedict:
            mat = line.strip()
        elif '_' in line and line.strip().split('_')[1] in matfacedict:
            mat = line.strip().split('_')[1]
        if 'nFaces' in line:
            matfacedict[mat][1] = int(line.split()[1].strip(';'))
        if 'startFace' in line:
            matfacedict[mat][0] = int(line.split()[1].strip(';'))
    bobs = [ob for ob in scene.objects if ob.get('VIType') and ob['VIType'] == 'FloViMesh']
    
    if bobs:
        o = bobs[0]
        selobj(scene, o)
        while o.data.materials:
            bpy.ops.object.material_slot_remove()
    else:
        bpy.ops.object.add(type='MESH', layers=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True))
        o = bpy.context.object
        o['VIType'] = 'FloViMesh'
    
    o.name = meshtype
    for mat in mats:
        if mat.name not in o.data.materials:
            bpy.ops.object.material_slot_add()
            o.material_slots[-1].material = mat 
    matnamedict = {mat.name: m for  m, mat in enumerate(o.data.materials)}
    
    bm = bmesh.new()
    for line in [line for line in vfile.readlines() if line[0] == '(' and len(line.split(' ')) == 3]:
        bm.verts.new().co = [float(vpos) for vpos in line[1:-2].split(' ')]
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for l, line in enumerate([line for line in ffile.readlines() if '(' in line and line[0].isdigit() and len(line.split(' ')) == int(line[0])]):
        newf = bm.faces.new([bm.verts[int(fv)] for fv in line[2:-2].split(' ')])
        for facerange in matfacedict.items():
            if l in range(facerange[1][0], facerange[1][0] + facerange[1][1]):
                newf.material_index = matnamedict[facerange[0]]
    bm.to_mesh(o.data)
    bm.free()

def fvbmr(scene, o):
    points = '{\n    version     2.0;\n    format      ascii;\n    class       vectorField;\n    location    "constant/polyMesh";\n    object      points;\n}\n\n{}\n(\n'.format(len(o.data.verts))
    points += ''.join(['({} {} {})\n'.format(o.matrix_world * v.co) for v in o.data.verts]) + ')'
    with open(os.path.join(scene['viparams']['ofcpfilebase'], 'points'), 'r') as pfile:
        pfile.write(points)
    faces = '{\n    version     2.0;\n    format      ascii;\n    class       faceList;\n    location    "constant/polyMesh";\n    object      faces;\n}\n\n{}\n(\n'.format(len(o.data.faces))
    faces += ''.join(['({} {} {} {})\n'.format(f.vertices) for f in o.data.faces]) + ')'
    with open(os.path.join(scene['viparams']['ofcpfilebase'], 'faces'), 'r') as ffile:
        ffile.write(faces)
    
def fvvarwrite(scene, obs, node):
    '''Turbulence modelling: k and epsilon required for kEpsilon, k and omega required for kOmega, nutilda required for SpalartAllmaras, nut required for all
        Bouyancy modelling: T''' 
    (pentry, Uentry, nutildaentry, nutentry, kentry, eentry, oentry) = ["FoamFile\n{{\n  version     2.0;\n  format      ascii;\n  class       vol{}Field;\n  object      {};\n}}\n\ndimensions [0 {} {} 0 0 0 0];\ninternalField   uniform {};\n\nboundaryField\n{{\n".format(*var) for var in (('Scalar', 'p', '2', '-2', '{}'.format(node.pval)), ('Vector', 'U', '1', '-1' , '({} {} {})'.format(*node.uval)), ('Scalar', 'nuTilda', '2', '-1' , '{}'.format(node.nutildaval)), ('Scalar', 'nut', '2', '-1' , '{}'.format(node.nutval)), 
    ('Scalar', 'k', '2', '-2' , '{}'.format(node.kval)), ('Scalar', 'epsilon', '2', '-3' , '{}'.format(node.epval)), ('Scalar', 'omega', '0', '-1' , '{}'.format(node.oval)))]
    
    for o in obs:
        for mat in o.data.materials: 
            matname = '{}_{}'.format(o.name, mat.name) if o.vi_type == '3' else mat.name 
            if mat.mattype == '3':
                pentry += mat.fvmat(matname, 'p')
                Uentry += mat.fvmat(matname, 'U')
                if node.solver != 'icoFoam':
                    nutentry += mat.fvmat(matname, 'nut')
#                    matbnuttype = mat.flovi_bmwnut_type
                    if node.turbulence ==  'SpalartAllmaras':
                        nutildaentry += mat.fvmat(matname, 'nutilda')
#                        matbnutildatype = mat.flovi_bmwnutilda_type
                    elif node.turbulence ==  'kEpsilon':
                        kentry += mat.fvmat(matname, 'k')
                        eentry += mat.fvmat(matname, 'e')
#                        matbktype = mat.flovi_bmwk_type
#                        matbetype = mat.flovi_bmwe_type
                    elif node.turbulence ==  'kOmega':
                        kentry += mat.fvmat(matname, 'k')
                        oentry += mat.fvmat(matname, 'o')
#                        matbktype = mat.flovi_bmwk_type
#                        matbotype = mat.flovi_bmwe_type
#                if mat.flovi_bmb_type == '0':
#                    matbptype = mat.flovi_bmwp_type
#                    matbUtype = mat.flovi_bmwu_type
#                    Uentry += "  {}\n  {{\n    type    {};\n    value  uniform ({} {} {});\n  }}\n".format(matname, mat.flovi_bmwu_type, mat.flovi_bmu_x, mat.flovi_bmu_y, mat.flovi_bmu_z) 
#                    pentry += "  {}\n  {{\n    type    {};\n  }}\n".format(matname, matbptype)
#                    if node.solver != 'icoFoam':
#                        matbnuttype = mat.flovi_bmwnut_type
#                        if node.turbulence ==  'SpalartAllmaras':
#                            matbnutildatype = mat.flovi_bmwnutilda_type
#                        elif node.turbulence ==  'kEpsilon':
#                            matbktype = mat.flovi_bmwk_type
#                            matbetype = mat.flovi_bmwe_type
#                        elif node.turbulence ==  'kOmega':
#                            matbktype = mat.flovi_bmwk_type
#                            matbotype = mat.flovi_bmwe_type
#                elif mat.flovi_bmb_type == '1':
#                    matbptype = mat.flovi_bmip_type
#                    matbUtype = mat.flovi_bmiu_type
#                    Uentry += "  {}\n  {{\n    type    {};\n    value  uniform ({} {} {});\n  }}\n".format(matname, mat.flovi_bmiu_type, mat.flovi_bmu_x, mat.flovi_bmu_y, mat.flovi_bmu_z) 
#                    if node.solver != 'icoFoam':
#                        matbnuttype = mat.flovi_bminut_type
#                        if node.turbulence ==  'SpalartAllmaras':
#                            matbnutildatype = mat.flovi_bminutilda_type
#                        elif node.turbulence ==  'kEpsilon':
#                            matbktype = mat.flovi_bmik_type
#                            matbetype = mat.flovi_bmie_type
#                        elif node.turbulence ==  'kOmega':
#                            matbktype = mat.flovi_bmik_type
#                            matbotype = mat.flovi_bmio_type
#                elif mat.flovi_bmb_type == '2':
#                    matbptype = mat.flovi_bmop_type
#                    matbUtype = mat.flovi_bmou_type
#                    Uentry += "  {}\n  {{\n    type    {};\n".format(matname, mat.flovi_bmou_type)
#                    if node.solver != 'icoFoam':
#                        matbnuttype = mat.flovi_bmonut_type
#                        if node.turbulence ==  'SpalartAllmaras':
#                            matbnutildatype = mat.flovi_bmonutilda_type
#                        elif node.turbulence ==  'kEpsilon':
#                            matbktype = mat.flovi_bmok_type
#                            matbetype = mat.flovi_bmoe_type
#                        elif node.turbulence ==  'kOmega':
#                            matbktype = mat.flovi_bmok_type
#                            matbotype = mat.flovi_bmoo_type
#                
#                elif mat.flovi_bmb_type == '4':
#                    matbptype = 'empty'
#                    matbUtype = 'empty'
#                    if node.solver != 'icoFoam':
#                        matbnuttype = 'empty'
#                        matbnutildatype = 'empty'
#                        matbktype = 'empty'
#                        matbotype = 'empty'
#                        matbetype = 'empty'
#                    Uentry += "  {}\n  {{\n    type    {};\n  }}\n".format(matname, 'empty') 
#                
#                pentry += "  {}\n  {{\n    type    {};\n  }}\n".format(matname, matbptype) 
##                if matbUtype == 'empty':
##                    Uentry += "  {}\n  {{\n    type    {};\n  }}\n".format(matname, matbUtype) 
##                else:
##                    Uentry += "  {}\n  {{\n    type    {};\n    value  uniform ({} {} {});\n  }}\n".format(matname, matbUtype, mat.flovi_bmwu_x, mat.flovi_bmwu_y, mat.flovi_bmwu_z) 
#                if node.solver != 'icoFoam':
#                    if mat.flovi_bmb_type == '0':
#                        nutentry += "  {0}\n  {{\n    type    {1};\n    value  $internalField;\n  }}\n".format(matname, matbnuttype) 
#                        if node.turbulence ==  'SpalartAllmaras':                    
#                            nutildaentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbnutildatype, 'value', node.nutildaval) 
#                        elif node.turbulence ==  'kEpsilon':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbktype, 'value', node.kval) 
#                            eentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbetype, 'value', node.epval)
#                        elif node.turbulence ==  'kOmega':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbktype, 'value', node.kval) 
#                            oentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbotype, 'value', node.oval)
#                    if mat.flovi_bmb_type == '1':
#                        nutentry += "  {0}\n  {{\n    type    {1};\n    value $internalField;\n  }}\n".format(matname, matbnuttype) 
#                        if node.turbulence ==  'SpalartAllmaras':
#                            nutildaentry += "  {0}\n  {{\n    type    {1};\n    uniform {3};\n  }}\n".format(matname, matbnutildatype, 'freestreamValue', mat.flovi_bmnut) 
#                        elif node.turbulence ==  'kEpsilon':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbktype, 'value', node.kval) 
#                            eentry += "  {0}\n  {{\n    type    {1};\n    {2}  $internalField;\n  }}\n".format(matname, matbetype, 'value')
#                        elif node.turbulence ==  'kOmega':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbktype, 'value', node.kval) 
#                            oentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbotype, 'value', node.oval)
#                    if mat.flovi_bmb_type == '2':
#                        nutentry += "  {0}\n  {{\n    type    {1};\n    value  $internalField;\n  }}\n".format(matname, matbnuttype)
#                        if node.turbulence ==  'SpalartAllmaras':
#                            nutildaentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbnutildatype, 'freestreamValue', mat.flovi_bmnut) 
#                        elif node.turbulence ==  'kEpsilon':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    inletValue    $internalField;\n    value    $internalField;\n  }}\n".format(matname, matbktype) 
#                            eentry += "  {0}\n  {{\n    type    {1};\n    inletValue    $internalField;\n    value    $internalField;\n  }}\n".format(matname, matbetype)
#                        elif node.turbulence ==  'kOmega':
#                            kentry += "  {0}\n  {{\n    type    {1};\n  }}\n".format(matname, matbktype) 
#                            oentry += "  {0}\n  {{\n    type    {1};\n  }}\n".format(matname, matbotype)
#                    if mat.flovi_bmb_type == '3':
#                        nutentry += "  {0}\n  {{\n    type    {1};\n    value  $internalField;\n  }}\n".format(matname, matbnuttype)
#                        if node.turbulence ==  'SpalartAllmaras':
#                            nutildaentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(matname, matbnutildatype, 'freestreamValue', mat.flovi_bmnut) 
#                        elif node.turbulence ==  'kEpsilon':
#                            kentry += "  {0}\n  {{\n    type    {1};\n    inletValue    $internalField;\n    value    $internalField;\n  }}\n".format(matname, matbktype) 
#                            eentry += "  {0}\n  {{\n    type    {1};\n    inletValue    $internalField;\n    value    $internalField;\n  }}\n".format(matname, matbetype)
#                        elif node.turbulence ==  'kOmega':
#                            kentry += "  {0}\n  {{\n    type    {1};\n  }}\n".format(matname, matbktype) 
#                            oentry += "  {0}\n  {{\n    type    {1};\n  }}\n".format(matname, matbotype)
#                    if mat.flovi_bmb_type == '4':
#                        nutentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#                        if node.turbulence ==  'SpalartAllmaras':
#                            nutildaentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#                        elif node.turbulence ==  'kEpsilon':
#                            kentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#                            eentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#                        elif node.turbulence ==  'kOmega':
#                            kentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#                            oentry += "  {}\n  {{\n    type    empty;\n  }}\n".format(matname)
#            else:
#                if node.turbulence ==  'SpalartAllmaras':
#                    nutentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnuttype, ('value', 'freestreamValue')[matbnuttype == 'freestream'], mat.flovi_bmnut) 
#                    nutildaentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnutildatype, ('value', 'freestreamValue')[matbnutildatype == 'freestream'], mat.flovi_bmnut) 
#                elif node.turbulence ==  'kEpsilon':
#                    
#                    kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnuttype, ('value', 'freestreamValue')[matbktype == 'freestream'], mat.flovi_bmnut)
#                    eentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnuttype, ('value', 'freestreamValue')[matbnuttype == 'freestream'], mat.flovi_bmnut)
#                elif node.turbulence ==  'kOmega':
#                    kentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnuttype, ('value', 'freestreamValue')[matbnuttype == 'freestream'], mat.flovi_bmnut)
#                    oentry += "  {0}\n  {{\n    type    {1};\n    {2}  uniform {3};\n  }}\n".format(mat.name, matbnuttype, ('value', 'freestreamValue')[matbnuttype == 'freestream'], mat.flovi_bmnut)

    pentry += '}'
    Uentry += '}'
    nutentry += '}'
    kentry += '}'
    eentry += '}'
    oentry += '}'
    
    with open(os.path.join(scene['viparams']['of0filebase'], 'p'), 'w') as pfile:
        pfile.write(pentry)
    with open(os.path.join(scene['viparams']['of0filebase'], 'U'), 'w') as Ufile:
        Ufile.write(Uentry)
    if node.solver != 'icoFoam':
        with open(os.path.join(scene['viparams']['of0filebase'], 'nut'), 'w') as nutfile:
            nutfile.write(nutentry)
        if node.turbulence == 'SpalartAllmaras':
            with open(os.path.join(scene['viparams']['of0filebase'], 'nuTilda'), 'w') as nutildafile:
                nutildafile.write(nutildaentry)
        if node.turbulence == 'kEpsilon':
            with open(os.path.join(scene['viparams']['of0filebase'], 'k'), 'w') as kfile:
                kfile.write(kentry)
            with open(os.path.join(scene['viparams']['of0filebase'], 'epsilon'), 'w') as efile:
                efile.write(eentry)
        if node.turbulence == 'kOmega':
            with open(os.path.join(scene['viparams']['of0filebase'], 'k'), 'w') as kfile:
                kfile.write(kentry)
            with open(os.path.join(scene['viparams']['of0filebase'], 'omega'), 'w') as ofile:
                ofile.write(oentry)
                
def fvmattype(mat, var):
    if mat.flovi_bmb_type == '0':
        matbptype = ['zeroGradient'][int(mat.flovi_bmwp_type)]
        matbUtype = ['fixedValue'][int(mat.flovi_bmwu_type)]
    elif mat.flovi_bmb_type in ('1', '2'):
        matbptype = ['freestreamPressure'][int(mat.flovi_bmiop_type)]
        matbUtype = ['fixedValue'][int(mat.flovi_bmiou_type)]
    elif mat.flovi_bmb_type == '3':
        matbptype = 'empty'
        matbUtype = 'empty'
    
def fvcdwrite(solver, dt, et):
    pw = 0 if solver == 'icoFoam' else 1
    return 'FoamFile\n{\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  location    "system";\n  object      controlDict;\n}\n\n' + \
            'application     {};\nstartFrom       startTime;\nstartTime       0;\nstopAt          endTime;\nendTime         {};\n'.format(solver, et)+\
            'deltaT          {};\nwriteControl    timeStep;\nwriteInterval   {};\npurgeWrite      {};\nwriteFormat     ascii;\nwritePrecision  6;\n'.format(dt, 1, pw)+\
            'writeCompression off;\ntimeFormat      general;\ntimePrecision   6;\nrunTimeModifiable true;\n\n'

def fvsolwrite(node):
    ofheader = 'FoamFile\n{\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  location    "system";\n  object    fvSolution;\n}\n\n' + \
        'solvers\n{\n  p\n  {\n    solver          PCG;\n    preconditioner  DIC;\n    tolerance       1e-06;\n    relTol          0;\n  }\n\n' + \
        '  "(U|k|epsilon|omega|R|nuTilda)"\n  {\n    solver          smoothSolver;\n    smoother        symGaussSeidel;\n    tolerance       1e-05;\n    relTol          0;  \n  }\n}\n\n'
    if node.solver == 'icoFoam':
        ofheader += 'PISO\n{\n  nCorrectors     2;\n  nNonOrthogonalCorrectors 0;\n  pRefCell        0;\n  pRefValue       0;\n}\n\n' + \
        'solvers\n{\n    p\n    {\n        solver          GAMG;\n        tolerance       1e-06;\n        relTol          0.1;\n        smoother        GaussSeidel;\n' + \
        '        nPreSweeps      0;\n        nPostSweeps     2;\n        cacheAgglomeration true;\n        nCellsInCoarsestLevel 10;\n        agglomerator    faceAreaPair;\n'+ \
        '        mergeLevels     1;\n    }\n\n    U\n    {\n        solver          smoothSolver;\n        smoother        GaussSeidel;\n        nSweeps         2;\n' + \
        '        tolerance       1e-08;\n        relTol          0.1;\n    }\n\n    nuTilda\n    {\n        solver          smoothSolver;\n        smoother        GaussSeidel;\n' + \
        '        nSweeps         2;\n        tolerance       1e-08;\n        relTol          0.1;\n    }\n}\n\n'
    elif node.solver == 'simpleFoam':   
        ofheader += 'SIMPLE\n{{\n  nNonOrthogonalCorrectors 0;\n  pRefCell        0;\n  pRefValue       0;\n\n    residualControl\n  {{\n    "(p|U|k|epsilon|omega|nut|nuTilda)" {};\n  }}\n}}\n'.format(node.convergence)
        ofheader += 'relaxationFactors\n{\n    fields\n    {\n        p               0.3;\n    }\n    equations\n    {\n' + \
            '        U               0.7;\n        k               0.7;\n        epsilon           0.7;\n      omega           0.7;\n        nuTilda           0.7;\n    }\n}\n\n'
#        if node.turbulence == 'kEpsilon':
#            ofheader += 'relaxationFactors\n{\n    fields\n    {\n        p               0.3;\n    }\n    equations\n    {\n' + \
#            '        U               0.7;\n        k               0.7;\n        epsilon           0.7;\n    }\n}\n\n'
#        elif node.turbulence == 'kOmega':
#            ofheader += 'relaxationFactors\n{\n    fields\n    {\n        p               0.3;\n    }\n    equations\n    {\n' + \
#            '        U               0.7;\n        k               0.7;\n        omega           0.7;\n    }\n}\n\n'
#        elif node.turbulence == 'SpalartAllmaras':
#            ofheader += 'relaxationFactors\n{\n    fields\n    {\n        p               0.3;\n    }\n    equations\n    {\n' + \
#            '        U               0.7;\n        k               0.7;\n        nuTilda           0.7;\n    }\n}\n\n'
    return ofheader

def fvschwrite(node):
    ofheader = 'FoamFile\n{\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  location    "system";\n  object    fvSchemes;\n}\n\n'
    if node.solver == 'icoFoam':
        return ofheader + 'ddtSchemes\n{\n  default         Euler;\n}\n\ngradSchemes\n{\n  default         Gauss linear;\n  grad(p)         Gauss linear;\n}\n\n' + \
            'divSchemes\n{\n  default         none;\n  div(phi,U)      Gauss linear;\n}\n\nlaplacianSchemes\n{\n  default         Gauss linear orthogonal;\n}\n\n' + \
            'interpolationSchemes\n{\n  default         linear;\n}\n\n' + \
            'snGradSchemes{  default         orthogonal;}\n\nfluxRequired{  default         no;  p;\n}'
    else:
        ofheader += 'ddtSchemes\n{\n    default         steadyState;\n}\n\ngradSchemes\n{\n    default         Gauss linear;\n}\n\ndivSchemes\n{\n    '
        if node.turbulence == 'kEpsilon':
            ofheader += 'default         none;\n    div(phi,U)   bounded Gauss upwind;\n    div(phi,k)      bounded Gauss upwind;\n    div(phi,epsilon)  bounded Gauss upwind;\n    div((nuEff*dev(T(grad(U))))) Gauss linear;\n}\n\n'
        elif node.turbulence == 'kOmega':
            ofheader += 'default         none;\n    div(phi,U)   bounded Gauss upwind;\n    div(phi,k)      bounded Gauss upwind;\n    div(phi,omega)  bounded Gauss upwind;\n    div((nuEff*dev(T(grad(U))))) Gauss linear;\n}\n\n'
        elif node.turbulence == 'SpalartAllmaras':
            ofheader += 'default         none;\n    div(phi,U)   bounded Gauss linearUpwind grad(U);\n    div(phi,nuTilda)      bounded Gauss linearUpwind grad(nuTilda);\n    div((nuEff*dev(T(grad(U))))) Gauss linear;\n}\n\n'
        ofheader += 'laplacianSchemes\n{\n    default         Gauss linear corrected;\n}\n\n' + \
        'interpolationSchemes\n{\n    default         linear;\n}\n\nsnGradSchemes\n{\n    default         corrected;\n}\n\n' + \
        'fluxRequired\n{\n    default         no;\n    p               ;\n}\n'
    return ofheader

def fvtppwrite(solver):
    ofheader = 'FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       dictionary;\n    location    "constant";\n    object      transportProperties;\n}\n\n'
    if solver == 'icoFoam':
        return ofheader + 'nu              nu [ 0 2 -1 0 0 0 0 ] 0.01;\n'
    else:
        return ofheader + 'transportModel  Newtonian;\n\nrho             rho [ 1 -3 0 0 0 0 0 ] 1;\n\nnu              nu [ 0 2 -1 0 0 0 0 ] 1e-05;\n\n' + \
        'CrossPowerLawCoeffs\n{\n    nu0             nu0 [ 0 2 -1 0 0 0 0 ] 1e-06;\n    nuInf           nuInf [ 0 2 -1 0 0 0 0 ] 1e-06;\n    m               m [ 0 0 1 0 0 0 0 ] 1;\n' + \
        '    n               n [ 0 0 0 0 0 0 0 ] 1;\n}\n\n' + \
        'BirdCarreauCoeffs\n{\n    nu0             nu0 [ 0 2 -1 0 0 0 0 ] 1e-06;\n    nuInf           nuInf [ 0 2 -1 0 0 0 0 ] 1e-06;\n' + \
        '    k               k [ 0 0 1 0 0 0 0 ] 0;\n    n               n [ 0 0 0 0 0 0 0 ] 1;\n}'
        
def fvraswrite(turb):
    ofheader = 'FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       dictionary;\n    location    "constant";\n    object      RASProperties;\n}\n\n'
    return ofheader + 'RASModel        {};\n\nturbulence      on;\n\nprintCoeffs     on;\n'.format(turb)
    
def fvshmwrite(node, o, **kwargs):    
    layersurf = '({}|{})'.format(kwargs['ground'][0].name, o.name) if kwargs and kwargs['ground'] else o.name 
    ofheader = 'FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       dictionary;\n    object      snappyHexMeshDict;\n}\n\n'
    ofheader += 'castellatedMesh    {};\nsnap    {};\naddLayers    {};\ndebug    {};\n\n'.format('true', 'true', 'true', 0)
    ofheader += 'geometry\n{{\n    {0}.obj\n    {{\n        type triSurfaceMesh;\n        name {0};\n    }}\n}};\n\n'.format(o.name)
    ofheader += 'castellatedMeshControls\n{{\n  maxLocalCells {};\n  maxGlobalCells {};\n  minRefinementCells {};\n  maxLoadUnbalance 0.10;\n  nCellsBetweenLevels {};\n'.format(node.lcells, node.gcells, int(node.gcells/100), node.ncellsbl)
    ofheader += '  features\n  (\n    {{\n      file "{}.eMesh";\n      level {};\n    }}\n  );\n\n'.format(o.name, node.level)
    ofheader += '  refinementSurfaces\n  {{\n    {}\n    {{\n      level ({} {});\n    }}\n  }}\n\n  '.format(o.name, node.surflmin, node.surflmax) 
    ofheader += '  resolveFeatureAngle 30;\n  refinementRegions\n  {}\n\n'
    ofheader += '  locationInMesh ({} {} {});\n  allowFreeStandingZoneFaces true;\n}}\n\n'.format(0.1, 0.1, 0.1)
    ofheader += 'snapControls\n{\n  nSmoothPatch 3;\n  tolerance 2.0;\n  nSolveIter 30;\n  nRelaxIter 5;\n  nFeatureSnapIter 10;\n  implicitFeatureSnap false;\n  explicitFeatureSnap true;\n  multiRegionFeatureSnap false;\n}\n\n'
    ofheader += 'addLayersControls\n{{\n  relativeSizes true;\n  layers\n  {{\n    "{}.*"\n    {{\n      nSurfaceLayers {};\n    }}\n  }}\n\n'.format(layersurf, node.layers)
    ofheader += '  expansionRatio 1.0;\n  finalLayerThickness 0.3;\n  minThickness 0.1;\n  nGrow 0;\n  featureAngle 60;\n  slipFeatureAngle 30;\n  nRelaxIter 3;\n  nSmoothSurfaceNormals 1;\n  nSmoothNormals 3;\n' + \
                '  nSmoothThickness 10;\n  maxFaceThicknessRatio 0.5;\n  maxThicknessToMedialRatio 0.3;\n  minMedianAxisAngle 90;\n  nBufferCellsNoExtrude 0;\n  nLayerIter 50;\n}\n\n'
    ofheader += 'meshQualityControls\n{\n  #include "meshQualityDict"\n  nSmoothScale 4;\n  errorReduction 0.75;\n}\n\n'
    ofheader += 'writeFlags\n(\n  scalarLevels\n  layerSets\n  layerFields\n);\n\nmergeTolerance 1e-6;\n'
    return ofheader

def fvmqwrite():
    ofheader = 'FoamFile\n{\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  object      meshQualityDict;\n}\n\n'
    ofheader += '#include "$WM_PROJECT_DIR/etc/caseDicts/meshQualityDict"'
    return ofheader
    
def fvsfewrite(oname):
    ofheader = 'FoamFile\n{\n  version     2.0;\n  format      ascii;\n  class       dictionary;\n  object      surfaceFeatureExtractDict;\n}\n\n'
    ofheader += '{}.obj\n{{\n  extractionMethod    extractFromSurface;\n\n  extractFromSurfaceCoeffs\n  {{\n    includedAngle   150;\n  }}\n\n    writeObj\n    yes;\n}}\n'.format(oname)
    return ofheader

def fvobjwrite(scene, o, bmo):
    objheader = '# FloVi obj exporter\no {}\n'.format(o.name)
    objheader = '# FloVi obj exporter\n'
    bmomw, bmovs = bmo.matrix_world, [vert for vert in bmo.data.vertices]
    omw, ovs = o.matrix_world, [vert for vert in o.data.vertices]
    xvec, yvec, zvec = (bmomw*bmovs[3].co - bmomw*bmovs[0].co).normalized(), (bmomw*bmovs[2].co - bmomw*bmovs[3].co).normalized(), (bmomw*bmovs[4].co - bmomw*bmovs[0].co).normalized() 
    ofvpos = [[(omw*ov.co - bmomw*bmovs[0].co)*vec for vec in (xvec, yvec, zvec)] for ov in ovs]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    vcos = ''.join(['v {} {} {}\n'.format(*ofvpo) for ofvpo in ofvpos])
    with open(os.path.join(scene['viparams']['ofctsfilebase'], '{}.obj'.format(o.name)), 'w') as objfile:
        objfile.write(objheader+vcos)
        for m, mat in enumerate(o.data.materials):
            objfile.write('g {}\n'.format(mat.name) + ''.join(['f {} {} {}\n'.format(*[v.index + 1 for v in f.verts]) for f in bmesh.ops.triangulate(bm, faces = bm.faces)['faces'] if f.material_index == m]))
        objfile.write('#{}'.format(len(bm.faces)))
    bm.free()
#    print(objheader + vcos + fverts)
    
def sunpos(scene, node, frames, sun):
    if node.bl_label == 'EnVi Simulation':
        allresdict = node['allresdict']
#        node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        datetime.datetime(datetime.datetime.now().year, 1, 1, 12, 0)
        times = [datetime.datetime(datetime.datetime.now().year, int(allresdict['Month'][h]), int(allresdict['Day'][h]), int(allresdict['Hour'][h]) - 1, 0) for h in range(len(allresdict['Month']))]
#    simtime = node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
    else:
        sun.data.shadow_method, sun.data.shadow_ray_samples, sun.data.sky.use_sky = 'RAY_SHADOW', 8, 1
        shaddict = {'0': (0.01, 5), '1': (3, 3)}
        (sun.data.shadow_soft_size, sun.data.energy) = shaddict[str(node['skynum'])]
    for t, time in enumerate(times):
        scene.frame_set(t)
        solalt, solazi, beta, phi = solarPosition(time.timetuple()[7], time.hour + (time.minute)*0.016666, scene['latitude'], scene['longitude'])
#        if node['skynum'] < 2:
        sun.location, sun.rotation_euler = [x*20 for x in (-sin(phi), -cos(phi), tan(beta))], [(pi/2) - beta, 0, -phi]
        if scene.render.engine == 'CYCLES' and bpy.data.worlds['World'].use_nodes:
            if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)#sin(phi), -cos(phi), -2* beta/math.pi
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].keyframe_insert(data_path = 'sun_direction', frame = t)
        sun.keyframe_insert(data_path = 'location', frame = t)
        sun.keyframe_insert(data_path = 'rotation_euler', frame = t)
            
        bpy.ops.object.select_all()
    sun.data.cycles.use_multiple_importance_sampling = True