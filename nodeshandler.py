import bpy
from pathlib import Path

class NodeHandler():
 
    def get_mat_params(self, context):
        """dictionary generator {maps, channels, index}

        `helper` dict generated from properties stored in context.scene.bsmprops. Used by the method process_materials .
        For each panel_rows (rows in the ui panel) returns the string value of the map and the channel associated 
        as well as bool representing the state of that line in the UI panel:

        Args:
            self (self): The first parameter.
            context (context): The second parameter.

        Returns:
            [dict]: dictionary of of Maps and Channels names and the index of their line in the UI panel:
            {"maps":maps, "chans":chans, "indexer":indexer}

        .. More:
            https://www.python.org/dev/peps/pep-0484/

        """
        bsmprops = context.scene.bsmprops
        panel_rows = bsmprops.panel_rows
        maps = []
        chans = []
        indexer = [i for i in range(panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
        for i in indexer :
            panel_line = eval(f"bpy.context.scene.panel_line{i}")
            chans.append(panel_line.input_sockets)
            if panel_line.manual:
                maps.append(str(Path(panel_line.file_name).name))    
            else:
                maps.append(panel_line.map_label)
        line = {"maps":maps, "chans":chans, "indexer":indexer}
        return line

    def process_materials(self, **params):
        """helper function used to manipulate nodes

        `helper`  Used by the function BSM_OT_make_nodes and BSM_OT_assign_nodes.
        Set the nodes for each material in the material slots according to the maps and channels defined in the Ui panel:

        Args:
            self (self): The first parameter.
            context (context): The second parameter.
            params (array): [selected object, already_done, string tag "make_nodes" or "assign_nodes"]

        Returns:
            already_done : params[1] (to update the list)

        .. More:
            https://www.python.org/dev/peps/pep-0484/

        """
        context = params['context']
        already_done = params['already_done']
        leselected = params['selection']
        lafunction = params['caller']
        caller = params['ops']
        maslots = leselected.material_slots
        bsmprops = context.scene.bsmprops
        idx = leselected.active_material_index
        params = self.get_mat_params(context)
        if bsmprops.only_active_mat:
            maslots = [leselected.material_slots[idx]]
        for i in range(len(maslots)):
            leselected.active_material_index = i
            mat_active = leselected.active_material
            if mat_active != None:
                if mat_active.name not in already_done:
                    mat_active.use_nodes = True
                    enabled = params['indexer']
                    if lafunction == "assign_nodes":
                        for indexed in enabled:
                            sn_params = {'ops':caller, 'context':context, 'mat':mat_active, 'idx':indexed}
                            self.setup_nodes(**sn_params)
                    if lafunction == "make_nodes":
                        cn_params = {'context':context, 'maps':params['maps'], 'chans':params['chans'], 'mat':mat_active}
                        self.create_nodes(**cn_params)
                    already_done.append(mat_active.name)
        leselected.active_material_index = idx
        return already_done
        
    def create_nodes(self, **params):
        context = params['context']
        maps = params['maps']
        chans = params['chans']
        mat_active = params['mat']
        leoldshader = None
        scene = context.scene
        bsmprops = scene.bsmprops
        nodes_links = scene.node_links
        skip_normals = bsmprops.skip_normals
        selectedshader = bsmprops.shaders_list
        cutstomshd = selectedshader in nodes_links
        if bsmprops.clear_nodes:
            mat_active.node_tree.nodes.clear()
        nods = mat_active.node_tree.nodes
        treez = mat_active.node_tree
        linkz = treez.links
        lesoutputs = list(lesnodes for lesnodes in nods if lesnodes.type == "OUTPUT_MATERIAL")
        for lesnodes in lesoutputs:
            if lesnodes.is_active_output:
                mat_output = lesnodes
        if not len(lesoutputs) > 0:
            mat_output = nods.new("ShaderNodeOutputMaterial")
        offsetter1_x = -404
        offsetter1_y = 0
        baseloc0_x = mat_output.location[0]
        baseloc0_y = mat_output.location[1]
        surfinput = mat_output.inputs['Surface']
        if surfinput.is_linked:
            lafirstconnection = surfinput.links[0].from_node
            invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
            invalidshader = lafirstconnection.type in invalidtypes

        else:
            lafirstconnection = None
            invalidshader = True
        leoldshader = lafirstconnection
        replaceshader = invalidshader or (bsmprops.replace_shader)

        if replaceshader:

            if cutstomshd:
                lenewshader = nods.new('ShaderNodeGroup')
                lenewshader.node_tree = bpy.data.node_groups[selectedshader]

            else:
                lenewshader = nods.new(selectedshader)
            linkz.new(lenewshader.outputs[0], mat_output.inputs[0])
            lesurfaceshader = lenewshader

        else:
            lesurfaceshader = lafirstconnection

        if lesurfaceshader.type == 'BSDF_PRINCIPLED':
            lesurfaceshader.inputs['Specular'].default_value = 0
        baseloc0_x = mat_output.location[0]
        baseloc0_y = mat_output.location[1]
        lesurfaceshader.location = (baseloc0_x + offsetter1_x * 2, baseloc0_y)
        base_x = lesurfaceshader.location[0]
        base_y = lesurfaceshader.location[1]

        mapin = None
        lescoord = None
        mapnumbr = 0
        mn_params = {'context':context, 'mat':mat_active, 'shader':lesurfaceshader, 'nodes':nods, 'old_shader':leoldshader}

        self.move_nodes(**mn_params)

        if len(maps) > 0:
            
            #TODO: not sure why I do this , there is no reccursion
            if not mapin:
                mapin = nods.new('ShaderNodeMapping')
                mapin.label = mat_active.name + "Mapping"

            if not lescoord:
                lescoord = nods.new('ShaderNodeTexCoord')
                lescoord.label = mat_active.name + "Coordinates"

            if not lescoord.outputs[0].is_linked:
                linkz.new(lescoord.outputs['UV'], mapin.inputs['Vector'])
            lines = [i for i in range(bsmprops.panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
            for i in lines:
                panel_line = eval(f"scene.panel_line{i}")
                lamap = panel_line.map_label
                lechan = panel_line.input_sockets
                manual = panel_line.manual
                isdisplacement = ("Displacement" in lechan)
                islinked = (lechan != "0")
                isdispvector = 'Disp Vector' in lechan
                if manual:
                    lamap = Path(panel_line.file_name).name
                #TODO: there is a better way
                isnormal = ("normal" in lamap or "Normal" in lamap)
                isheight = ("height" in lamap or "Height" in lamap)
                washn = "height" in maps or "Height" in maps or "normal" in maps or "Normal" in maps
                addextras = bsmprops.tweak_levels and not (isnormal or isheight)
                colbool = ("Color" in lechan)
                emibool = ("Emission" in lechan)
                noramps = ["Subsurface Radius", "Normal", "Tangent"]
                innoramps = (lechan in noramps)
                okcurve = ((colbool or emibool) and not isdisplacement)
                okramp = (not (colbool or emibool) and (not lamap in noramps)) or (isdisplacement and isheight)
                offsetter_x = -312
                offsetter_y = -312
                lanewnode = nods.new(type="ShaderNodeTexImage")
                lanewnode.name = Path(panel_line.file_name).name
                lanewnode.label = lamap

                linkz.new(mapin.outputs[0], lanewnode.inputs['Vector'])

                if addextras:
                    if okcurve:
                        lacurveramp = nods.new('ShaderNodeRGBCurve')
                        extranode = lacurveramp
                        extranode.label = extranode.name + lamap
                        linkz.new(lanewnode.outputs[0], lacurveramp.inputs[1])

                    if okramp:
                        laramp = nods.new('ShaderNodeValToRGB')
                        extranode = laramp
                        linkz.new(lanewnode.outputs[0], laramp.inputs[0])

                        # linkz.new(lacurveramp.outputs[0] , mat_output.inputs[2])
                    if okramp or okcurve:
                        extranode.label = extranode.name + lamap

                if isnormal and not skip_normals:
                    normalmapnode = nods.new('ShaderNodeNormalMap')
                    linkz.new(lanewnode.outputs[0], normalmapnode.inputs[1])

                if isheight and not skip_normals:

                    bumpnode = nods.new('ShaderNodeBump')
                    linkz.new(lanewnode.outputs[0], bumpnode.inputs[2])
                    bumpnode.inputs[0].default_value = .5
                    if addextras:
                        linkz.new(extranode.outputs[0], bumpnode.inputs[2])

                if islinked and not isdisplacement and not isdispvector:

                    if isnormal and not skip_normals:
                        if isdisplacement:
                            linkz.new(normalmapnode.outputs[0], mat_output.inputs[2])

                        else:
                            linkz.new(normalmapnode.outputs[0], lesurfaceshader.inputs[lechan])

                    if isheight and not skip_normals:
                        if isdisplacement:
                            linkz.new(bumpnode.outputs[0], mat_output.inputs[2])

                        else:
                            linkz.new(bumpnode.outputs[0], lesurfaceshader.inputs[lechan])

                    if not (isheight or isnormal) or skip_normals:
                        if addextras:

                            linkz.new(extranode.outputs[0], lesurfaceshader.inputs[lechan])
                        else:
                            linkz.new(lanewnode.outputs[0], lesurfaceshader.inputs[lechan])

                if isdisplacement:
                    dispmapnode = nods.new('ShaderNodeDisplacement')
                    dispmapnode.location = (baseloc0_x - 256, baseloc0_y)
                    linkz.new(dispmapnode.outputs[0], mat_output.inputs['Displacement'])
                    if addextras:
                        linkz.new(extranode.outputs[0], dispmapnode.inputs['Height'])
                    if isheight and not skip_normals:
                        pass
                    if isnormal and not skip_normals:
                        linkz.new(normalmapnode.outputs[0], dispmapnode.inputs['Normal'])
                    if (not isnormal or skip_normals) and not addextras:
                        linkz.new(lanewnode.outputs[0], dispmapnode.inputs['Height'])
                # TODO implement link sanity check
                if isdispvector:  
                    dispvectnode = nods.new('ShaderNodeVectorDisplacement')
                    dispvectnode.location = (baseloc0_x - 256, baseloc0_y)
                    linkz.new(dispvectnode.outputs[0], mat_output.inputs['Displacement'])
                    if addextras:
                        linkz.new(extranode.outputs[0], dispvectnode.inputs['Vector'])
                    if isnormal and not skip_normals:
                        linkz.new(normalmapnode.outputs[0], dispvectnode.inputs['Vector'])
                        # not sure it makes any sense
                    if (not isnormal or skip_normals) and not addextras:
                        linkz.new(lanewnode.outputs[0], dispvectnode.inputs['Vector'])

                lanewnode.location = ((base_x + offsetter_x * (int(addextras) + int(isnormal or isheight) + 1)),
                                    (base_y + offsetter_y * mapnumbr))
                #todo: why ?
                if addextras:  # again to be sure
                    extranode.location = (
                        (base_x + offsetter_x * (int(isnormal or isheight) + 1)), (base_y + offsetter_y * mapnumbr))
                if isheight and not skip_normals:
                    bumpnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                if isnormal and not skip_normals:
                    normalmapnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                mapnumbr += 1
            gc_params = {'context':context,'shader':lesurfaceshader, 'nodes':nods}
            lesurfaceshader.location[1] = self.get_sockets_center(**gc_params) + 128  # just a bit higher
            lesurfaceshader.location[0] += 128
            mat_output.location[1] = lesurfaceshader.location[1]
            mapin.location = (base_x + offsetter_x * (int(addextras) + int(washn) + 2) + offsetter_x, base_y)
            lescoord.location = (mapin.location[0] + offsetter_x, mapin.location[1])
            ml_params = {'context':context, 'maps':mapin, 'nodes':nods}
            mapin.location[1] = self.map_links(**ml_params)
            lescoord.location[1] = mapin.location[1]

        return

    def setup_nodes(self, **params):
        context = params['context']
        lematerial = params['mat']
        index = params['idx']
        caller = params['ops']
        bsmprops = context.scene.bsmprops
        panel_line = eval(f"context.scene.panel_line{index}")
        manual = panel_line.manual
        """
        gofile = True
        if not manual:
            # bpy.ops.bsm.name_maker(line_num = index)
            gofile = (bpy.ops.bsm.name_checker(line_number=index, lorigin="assign_nodes", called=True) == {'FINISHED'})
        """
        
        active_filepath = panel_line.file_name

        imagename = lamap = Path(active_filepath).name
       
        #lamap = panel_line.map_label
        #if manual:
        #    lamap = Path(active_filepath).name

        if lematerial.node_tree.nodes.find(lamap) > 0:

            if Path(active_filepath).is_file():
               
                file_path = Path(active_filepath).name
                bpy.ops.image.open(filepath=active_filepath,show_multiview=False)
                nodestofill = (nod for nod in lematerial.node_tree.nodes if nod.name == lamap)
                for nods in nodestofill:
                    nods.image = bpy.data.images[imagename]
                    if lamap.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                        nods.image.colorspace_settings.name = 'Non-Color'

                toreport = "Texture file '" + imagename + "' assigned in "+ lematerial.name
                caller.report({'INFO'}, toreport)
            else:
                toreport = "Texture '" + imagename + "' not found"
                caller.report({'INFO'}, toreport)

        else:
            toreport = "node label " + lamap + " not found"
            caller.report({'INFO'}, toreport)

        return

    def map_links(self, **params):
        context = params['context']
        mapin = params['maps']
        nods = params['nodes']
        ylocs = []
        connected = list(linked for linked in mapin.outputs[0].links if linked.is_valid)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.to_node.location[1])
        else:
            for nod in nods:
                ylocs.append(nod.location[1])
        ylocs.sort()
        center = (ylocs[0] + ylocs[-1]) / 2
        return center   
    
    def selector(self, context):
        viewl = context.view_layer
        bsmprops = context.scene.bsmprops
        only_active_obj = bsmprops.only_active_obj
        applytoall = bsmprops.apply_to_all

        selection = viewl.objects.selected

        selected = []
        validtypes = ['SURFACE', 'CURVE', 'META', 'MESH', 'GPENCIL']
        if applytoall:
            selection = viewl.objects
        if only_active_obj:
            selection = [context.object]

        for obj in selection:
            if obj.type in validtypes:
                selected.append(obj)
                obj.select_set(False)

        return selected

    def move_nodes(self, **params):
        context = params['context']
        scene = context.scene
        mat_active = params['mat']
        lesurfaceshader = params['shader']
        nods = params['nodes']
        bsmprops = scene.bsmprops
        leoldshader = params['old_shader']
        replace = bsmprops.replace_shader
        panel_rows = bsmprops.panel_rows
        imgs = list(nod for nod in nods if nod.type == 'TEX_IMAGE')

        enabled = list(k for k in range(panel_rows) if eval(f"bpy.context.scene.panel_line{k}.line_on"))
        adding = len(enabled)
        listofshadernodes = []  # TODO get a list of all shadernodes
        ylocsall = []
        ylocsimg = []

        for nod in nods:
            replacedshader = replace and (nod != lesurfaceshader)
            if (nod in imgs) or replacedshader:
                ylocsimg.append(nod.location[1])
            ylocsall.append(nod.location[1])

        ylocsimg.sort()
        ylocsall.sort()
        distanceimgs = 0
        clustersize_y = 0
        newclustersize_y = 0
        distancenodes = 0
        if len(ylocsimg) > 1:
            distanceimgs = (ylocsimg[-1] - ylocsimg[0])
        if len(ylocsall) > 1:
            clustersize_y = (ylocsall[-1] - ylocsall[0])

        if bool(adding + int(replace)):
            existing = (nod for nod in nods if nod.type != "OUTPUT_MATERIAL" and not nod == lesurfaceshader)
            newclustersize_y = 888 * (adding / 2)
            if not adding > 0 and replace:
                newclustersize_y = 1024
            offsetter_y = newclustersize_y

            for nodez in existing:
                nodez.location = (nodez.location[0] - 512, nodez.location[1] + offsetter_y)

        return

    def get_sockets_center(self, **params):
        context = params['context']
        lesurfaceshader = params['shader']
        nods = params['nodes']
        ylocs = []
        connected = list(linked for linked in lesurfaceshader.inputs if linked.is_linked)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.links[0].from_node.location[1])
        else:
            for nod in nods:
                ylocs.append(nod.location[1])
        ylocs.sort()
        center = (ylocs[0] + ylocs[-1]) / 2
        return center

    