import os
import bpy

class NodeHandler():
    """
    def __init__(self, project=None):
        #self._set()
        self.project = project
        self.tasks_types = None
    """
    def checklist(self, context):
        """dictionary generator {maps, channels, index}

        `helper` dict generated from properties stored in context.scene.bsmprops. Used by the method foreachmat .
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
        panel_rows = bsmprops.panelrows
        maps = []
        chans = []
        indexer = [i for i in range(panel_rows) if eval(f"bpy.context.scene.panel_line{i}.labelbools")]
        for i in indexer :
            panel_line = eval(f"bpy.context.scene.panel_line{i}")
            chans.append(panel_line.inputsockets)
            if panel_line.manual:
                maps.append(os.path.basename(panel_line.lefilename))    
            else:
                maps.append(panel_line.maplabels)
        line = {"maps":maps, "chans":chans, "indexer":indexer}
        return line

    def foreachmat(self, **mat_params):
        """helper function used to manipulate nodes

        `helper`  Used by the function BSM_OT_createnodes and BSM_OT_assignnodes.
        Set the nodes for each material in the material slots according to the maps and channels defined in the Ui panel:

        Args:
            self (self): The first parameter.
            context (context): The second parameter.
            mat_params (array): [selected object, matsdone (?), string tag "dothem" or "plug"]

        Returns:
            already_done : mat_params[1] (to update the list)

        .. More:
            https://www.python.org/dev/peps/pep-0484/

        """
        context = mat_params['context']
        already_done = mat_params['already_done']
        leselected = mat_params['selection']
        lafunction = mat_params['caller']
        maslots = leselected.material_slots
        bsmprops = context.scene.bsmprops
        idx = leselected.active_material_index
        params = self.checklist(context)
        if bsmprops.onlyamat:
            maslots = [leselected.material_slots[idx]]

        for i in range(len(maslots)):
            leselected.active_material_index = i
            lematos = leselected.active_material

            if lematos != None:

                if lematos.name not in already_done:
                    lematos.use_nodes = True
                    

                    enabled = params['indexer']
                    if lafunction == "plug":
                        for indexed in enabled:
                            pg_params = {'context':context, 'mat':lematos, 'idx':indexed}
                            self.plugthenodes(**pg_params)

                    if lafunction == "dothem":
                        do_params = {'context':context, 'maps':params['maps'], 'chans':params['chans'], 'mat':lematos}
                        self.dothenodes(**do_params)

                    already_done.append(lematos.name)

        leselected.active_material_index = idx
        return already_done
    
    def dothenodes(self, **do_params):
        context = do_params['context']
        maps = do_params['maps']
        chans = do_params['chans']
        lematos = do_params['mat']
        leoldshader = None
        scene = context.scene
        bsmprops = scene.bsmprops
        nodes_links = scene.node_links
        skipnormals = bsmprops.skipnormals
        selectedshader = bsmprops.shaderlist
        cutstomshd = selectedshader in nodes_links


        if bsmprops.eraseall:
            lematos.node_tree.nodes.clear()

        nods = lematos.node_tree.nodes
        treez = lematos.node_tree
        linkz = treez.links

        lesoutputs = list(lesnodes for lesnodes in nods if lesnodes.type == "OUTPUT_MATERIAL")
        for lesnodes in lesoutputs:
            if lesnodes.is_active_output:
                matos_output = lesnodes
        if not len(lesoutputs) > 0:
            matos_output = nods.new("ShaderNodeOutputMaterial")

        offsetter1_x = -404
        offsetter1_y = 0
        baseloc0_x = matos_output.location[0]
        baseloc0_y = matos_output.location[1]

        surfinput = matos_output.inputs['Surface']
        if surfinput.is_linked:
            lafirstconnection = surfinput.links[0].from_node
            invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
            invalidshader = lafirstconnection.type in invalidtypes

        else:
            lafirstconnection = None
            invalidshader = True
        leoldshader = lafirstconnection
        replaceshader = invalidshader or (bsmprops.shader)

        if replaceshader:

            if cutstomshd:
                lenewshader = nods.new('ShaderNodeGroup')
                lenewshader.node_tree = bpy.data.node_groups[selectedshader]

            else:
                lenewshader = nods.new(selectedshader)
            linkz.new(lenewshader.outputs[0], matos_output.inputs[0])
            lesurfaceshader = lenewshader

        else:
            lesurfaceshader = lafirstconnection

        if lesurfaceshader.type == 'BSDF_PRINCIPLED':
            lesurfaceshader.inputs['Specular'].default_value = 0
            # best to set specular to 0 if the PBR workflow doesn't require it (otherwise a spec map will overwrite it anyway)

        baseloc0_x = matos_output.location[0]
        baseloc0_y = matos_output.location[1]
        lesurfaceshader.location = (baseloc0_x + offsetter1_x * 2, baseloc0_y)
        base_x = lesurfaceshader.location[0]
        base_y = lesurfaceshader.location[1]

        mapin = None
        lescoord = None
        mapnumbr = 0
        mov_params = {'context':context, 'mat':lematos, 'shader':lesurfaceshader, 'nodes':nods, 'old_shader':leoldshader}

        self.move_existing(**mov_params)

        if len(maps) > 0:

            if not mapin:
                mapin = nods.new('ShaderNodeMapping')
                mapin.label = lematos.name + "Mapping"

            if not lescoord:
                lescoord = nods.new('ShaderNodeTexCoord')
                lescoord.label = lematos.name + "Coordinates"

            if not lescoord.outputs[0].is_linked:
                # lematos.node_tree.nodes['Texture Coordinate'].outputs['UV']
                linkz.new(lescoord.outputs['UV'], mapin.inputs['Vector'])

            line = (i for i in range(len(list(maps))) if f"bpy.context.scene.panel_line{i}.labelbools")

            for i in line:
                lamap = maps[i]
                lechan = chans[i]

                panel_line = eval(f"scene.panel_line{i}")
                manual = panel_line.manual
                isdisplacement = ("Displacement" in lechan)
                islinked = (lechan != "0")
                isdispvector = 'Disp Vector' in lechan
                if manual:
                    lamap = os.path.basename(panel_line.lefilename)[:-4]
                isnormal = ("normal" in lamap or "Normal" in lamap)
                isheight = ("height" in lamap or "Height" in lamap)
                washn = "height" in maps or "Height" in maps or "normal" in maps or "Normal" in maps
                addextras = bsmprops.extras and not (isnormal or isheight)
                colbool = ("Color" in lechan)
                emibool = ("Emission" in lechan)
                noramps = ["Subsurface Radius", "Normal", "Tangent"]
                innoramps = (lechan in noramps)
                okcurve = ((colbool or emibool) and not isdisplacement)
                okramp = (not (colbool or emibool) and (not lamap in noramps)) or (isdisplacement and isheight)
                offsetter_x = -312
                offsetter_y = -312

                lanewnode = nods.new(type="ShaderNodeTexImage")
                lanewnode.name = lamap
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

                        # linkz.new(lacurveramp.outputs[0] , matos_output.inputs[2])
                    if okramp or okcurve:
                        extranode.label = extranode.name + lamap

                if isnormal and not skipnormals:
                    normalmapnode = nods.new('ShaderNodeNormalMap')
                    linkz.new(lanewnode.outputs[0], normalmapnode.inputs[1])

                if isheight and not skipnormals:

                    bumpnode = nods.new('ShaderNodeBump')
                    linkz.new(lanewnode.outputs[0], bumpnode.inputs[2])
                    bumpnode.inputs[0].default_value = .5
                    if addextras:
                        linkz.new(extranode.outputs[0], bumpnode.inputs[2])

                if islinked and not isdisplacement and not isdispvector:

                    if isnormal and not skipnormals:
                        if isdisplacement:
                            linkz.new(normalmapnode.outputs[0], matos_output.inputs[2])

                        else:
                            linkz.new(normalmapnode.outputs[0], lesurfaceshader.inputs[lechan])

                    if isheight and not skipnormals:
                        if isdisplacement:
                            linkz.new(bumpnode.outputs[0], matos_output.inputs[2])

                        else:
                            linkz.new(bumpnode.outputs[0], lesurfaceshader.inputs[lechan])

                    if not (isheight or isnormal) or skipnormals:
                        if addextras:

                            linkz.new(extranode.outputs[0], lesurfaceshader.inputs[lechan])
                        else:
                            linkz.new(lanewnode.outputs[0], lesurfaceshader.inputs[lechan])

                if isdisplacement:
                    dispmapnode = nods.new('ShaderNodeDisplacement')
                    dispmapnode.location = (baseloc0_x - 256, baseloc0_y)
                    linkz.new(dispmapnode.outputs[0], matos_output.inputs['Displacement'])
                    if addextras:
                        linkz.new(extranode.outputs[0], dispmapnode.inputs['Height'])
                    if isheight and not skipnormals:
                        pass
                    if isnormal and not skipnormals:
                        linkz.new(normalmapnode.outputs[0], dispmapnode.inputs['Normal'])
                    if (not isnormal or skipnormals) and not addextras:
                        linkz.new(lanewnode.outputs[0], dispmapnode.inputs['Height'])
                if isdispvector:  # TODO implement link sanity
                    dispvectnode = nods.new('ShaderNodeVectorDisplacement')
                    dispvectnode.location = (baseloc0_x - 256, baseloc0_y)
                    linkz.new(dispvectnode.outputs[0], matos_output.inputs['Displacement'])
                    if addextras:
                        linkz.new(extranode.outputs[0], dispvectnode.inputs['Vector'])
                    if isnormal and not skipnormals:
                        linkz.new(normalmapnode.outputs[0], dispvectnode.inputs['Vector'])
                        # not sure it makes any sense
                    if (not isnormal or skipnormals) and not addextras:
                        linkz.new(lanewnode.outputs[0], dispvectnode.inputs['Vector'])

                lanewnode.location = ((base_x + offsetter_x * (int(addextras) + int(isnormal or isheight) + 1)),
                                    (base_y + offsetter_y * mapnumbr))

                if addextras:  # again to be sure
                    extranode.location = (
                        (base_x + offsetter_x * (int(isnormal or isheight) + 1)), (base_y + offsetter_y * mapnumbr))
                if isheight and not skipnormals:
                    bumpnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                if isnormal and not skipnormals:
                    normalmapnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                mapnumbr += 1
            sl_params = {'context':context,'shader':lesurfaceshader, 'nodes':nods}
            lesurfaceshader.location[1] = self.surfaceshaderlinks(**sl_params) + 128  # just a bit higher
            lesurfaceshader.location[0] += 128
            matos_output.location[1] = lesurfaceshader.location[1]
            mapin.location = (base_x + offsetter_x * (int(addextras) + int(washn) + 2) + offsetter_x, base_y)
            lescoord.location = (mapin.location[0] + offsetter_x, mapin.location[1])
            mp_params = {'context':context, 'maps':mapin, 'nodes':nods}
            mapin.location[1] = self.map_links(**mp_params)
            lescoord.location[1] = mapin.location[1]
            # for nodez in nods:
            #     nodez.location[1] = nodez.location[1] - 156

        return

    def plugthenodes(self, **pg_params):
        context = pg_params['context']
        lematerial = pg_params['mat']
        index = pg_params['idx']

        bsmprops = context.scene.bsmprops
        panel_line = eval(f"context.scene.panel_line{index}")
        manual = panel_line.manual
        gofile = True
        if not manual:
            # bpy.ops.bsm.assumename(line_num = index)
            gofile = (bpy.ops.bsm.checkmaps(linen=index, lorigin="plug", called=True) == {'FINISHED'})
        lefilepath = panel_line.lefilename

        imagename = os.path.basename(lefilepath)
        lamap = panel_line.maplabels
        if manual:
            lamap = imagename[:-4]

        if lematerial.node_tree.nodes.find(lamap) > 0:

            if os.path.isfile(lefilepath) == True and gofile:
                bpy.ops.image.open(
                    filepath=os.path.basename(lefilepath),
                    directory=os.path.dirname(lefilepath),
                    files=[{"name": os.path.basename(lefilepath), "name": os.path.basename(lefilepath)}],
                    show_multiview=False
                )
                nodestofill = (nod for nod in lematerial.node_tree.nodes if nod.label == lamap)
                for nods in nodestofill:
                    nods.image = bpy.data.images[imagename]
                    if lamap.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                        nods.image.colorspace_settings.name = 'Non-Color'

                toreport = "Texture file '" + imagename + "' assigned in "+ lematerial.name
                self.report({'INFO'}, toreport)
            else:
                toreport = "Texture '" + imagename + "' not found"
                self.report({'INFO'}, toreport)

        else:
            toreport = "node label " + lamap + " not found"
            self.report({'INFO'}, toreport)

        return

    def map_links(self, **mp_params):
        context = mp_params['context']
        mapin = mp_params['maps']
        nods = mp_params['nodes']
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

    def move_existing(self, **mov_params):
        context = mov_params['context']
        scene = context.scene
        lematos = mov_params['mat']
        lesurfaceshader = mov_params['shader']
        nods = mov_params['nodes']
        bsmprops = scene.bsmprops
        leoldshader = mov_params['old_shader']
        replace = bsmprops.shader
        panelrows = bsmprops.panelrows
        imgs = list(nod for nod in nods if nod.type == 'TEX_IMAGE')

        enabled = list(k for k in range(panelrows) if eval(f"bpy.context.scene.panel_line{k}.labelbools"))
        adding = len(enabled)
        listofshadernodes = []  # TODO get a lish of all shadernodes
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

            # addit = int((distanceimgs / (len(imgs) + adding)) * adding)
            # offsetter_y = 192 * (adding * 2 + len(imgs) * 2 )
            offsetter_y = newclustersize_y

            for nodez in existing:
                nodez.location = (nodez.location[0] - 512, nodez.location[1] + offsetter_y)

        return

    def surfaceshaderlinks(self, **sl_params):
        context = sl_params['context']
        lesurfaceshader = sl_params['shader']
        nods = sl_params['nodes']
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

