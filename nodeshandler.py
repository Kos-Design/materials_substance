import bpy
from pathlib import Path
from . propertieshandler import PropertiesHandler as ph
 

class NodeHandler():
 
    def get_mat_params(self,context):
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
        props = context.scene.bsmprops
        panel_rows = props.panel_rows
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
        return {"maps":maps, "chans":chans, "indexer":indexer}
    
    def make_tree(self, context):
        """Method used to repopulate the enum items for the Shader list dropdown and associated sockets

        `helper`  Creates a temporary material, adds various shader nodes to it to get their sockets names 
                  and stores them in the shader_links CollectionPoperty.

        """
        context.scene.shader_links.clear()
        propper = ph()
        mat_tmp = bpy.data.materials.new(name="tmp_mat")
        mat_tmp.use_nodes = True
        for shader_enum in propper.get_shaders_list(context):
            node_type = str(shader_enum[0])
            if node_type is not None and node_type != '0' :
                new_node = mat_tmp.node_tree.nodes.new(type=node_type)
                new_shader_link = context.scene.shader_links.add()
                new_shader_link.name = str(shader_enum[1])
                new_shader_link.shadertype = node_type
                new_shader_link.input_sockets = ";;;".join(inputs.name for inputs in new_node.inputs)
                new_shader_link.outputsockets = ";;;".join(outputs.name for outputs in new_node.outputs)
        mat_tmp.node_tree.nodes.clear()
        bpy.data.materials.remove(mat_tmp)

    def refresh_shader_links(self,context):
        if len(context.scene.shader_links) == 0:
            self.make_tree(context)   

    def process_materials(self,context,**params):
        """helper function used to manipulate nodes

        `helper`  Used by the function BSM_OT_make_nodes and BSM_OT_assign_nodes.
        Set the nodes for each material in the material slots according to the maps and channels defined in the Ui panel:

        Args:
            self (self): The first parameter.
            context (context): The second parameter.
            params (array): [selected object, already_done]

        Returns:
            already_done : list of materials already processed

        .. More:
            https://www.python.org/dev/peps/pep-0484/

        """
        already_done = params['already_done']
        executable = params['executable']
        obj = params['selection']
        caller = params['ops']
        mat_slots = [mat.material for mat in obj.material_slots]
        props = context.scene.bsmprops
        og_mat = obj.active_material
        if props.only_active_mat:
            mat_slots = [obj.active_material]
        for mat in mat_slots:
            if mat is not None :
                obj.active_material = mat
                if mat.name not in already_done:
                    mat.use_nodes = True
                    params = {'mat':mat}
                    executable(context,**params)
                    already_done.append(mat.name)
        obj.active_material = og_mat
        
        return already_done

    def get_shader_node(self,context,**params):
        props = context.scene.bsmprops
        mat_active = params['mat']
        tree_nodes = mat_active.node_tree.nodes
        tree_links = mat_active.node_tree.links
        if params['inv'] or props.replace_shader:
            substitute_shader = props.shaders_list
            #handles custom shaders
            if substitute_shader in nodes_links:
                new_node = tree_nodes.new('ShaderNodeGroup')
                new_node.node_tree = bpy.data.node_groups[substitute_shader]
            else:
                new_node = tree_nodes.new(substitute_shader)
            tree_links.new(new_node.outputs[0], mat_output.inputs[0])
            return new_node
        return params['shader_node']

    def get_output_node(self,context,**params):
        tree_nodes = params['tree_nodes']
        out_nodes = [n for n in tree_nodes if n.type == "OUTPUT_MATERIAL"]
        for node in out_nodes:
            if node.is_active_output:
                return node
        return tree_nodes.new("ShaderNodeOutputMaterial")
        
    def get_first_node(self,context,**params):
        sur_node = params['sur_node']
        invalid_shader = False
        first_node = None
        if sur_node.is_linked:
            first_node = sur_node.links[0].from_node
            invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
            invalid_shader = first_node.type in invalidtypes
        else:
            first_node = None
            invalid_shader = True
        return first_node,invalid_shader

    def create_nodes(self,context,**params):
        m_params = self.get_mat_params(context)
        maps = m_params['maps']
        chans = m_params['chans']
        mat_active = params['mat']
        propper = ph()
        scene = context.scene
        props = scene.bsmprops
        nodes_links = scene.node_links
        tree_nodes = mat_active.node_tree.nodes
        
        if props.clear_nodes:
            tree_nodes.clear()

        tree_links = mat_active.node_tree.links
        tn_params={'tree_nodes':tree_nodes}
        mat_output = self.get_output_node(context,**tn_params)
        
        offsetter1_x = -404
        offsetter1_y = 0
        
        baseloc0_x = mat_output.location[0]
        baseloc0_y = mat_output.location[1]

        nf_params = {'sur_node':mat_output.inputs['Surface']}
        first_node,invalid_shader = self.get_first_node(context,**nf_params)
        old_shader = first_node
        sh_params = {'inv':invalid_shader,'shader_node':first_node,'mat':mat_active}
        shader_node = self.get_shader_node(context,**sh_params)
        if shader_node.type == 'BSDF_PRINCIPLED':
            shader_node.inputs['Specular'].default_value = 0
        
        baseloc0_x = mat_output.location[0]
        baseloc0_y = mat_output.location[1]
        
        shader_node.location = (baseloc0_x + offsetter1_x * 2, baseloc0_y)
        base_x = shader_node.location[0]
        base_y = shader_node.location[1]

        mapin = None
        lescoord = None
        mapnumbr = 0
        mn_params = {'mat':mat_active, 'shader':shader_node, 'nodes':tree_nodes, 'old_shader':old_shader}

        self.move_nodes(context,**mn_params)

        if len(maps) > 0:
            
            #TODO: not sure why I do this , there is no reccursion
            if not mapin:
                mapin = tree_nodes.new('ShaderNodeMapping')
                mapin.label = mat_active.name + "Mapping"

            if not lescoord:
                lescoord = tree_nodes.new('ShaderNodeTexCoord')
                lescoord.label = mat_active.name + "Coordinates"

            if not lescoord.outputs[0].is_linked:
                tree_links.new(lescoord.outputs['UV'], mapin.inputs['Vector'])
            lines = [i for i in range(props.panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
            skip_normals = props.skip_normals
            for i in lines:
                panel_line = eval(f"scene.panel_line{i}")
                args = {'line':panel_line, 'mat_name':mat_active.name}
                file_name = propper.find_file(context,**args)
                if file_name is not None :
                    panel_line.file_name = panel_line.probable = file_name
                map_name = panel_line.map_label
                lechan = panel_line.input_sockets
                manual = panel_line.manual
                isdisplacement = ("Displacement" in lechan)
                islinked = (lechan != "0")
                isdispvector = 'Disp Vector' in lechan
                if manual:
                    map_name = Path(panel_line.file_name).name
                #TODO: there is a better way
                isnormal = ("normal" in map_name or "Normal" in map_name)
                isheight = ("height" in map_name or "Height" in map_name)
                washn = "height" in maps or "Height" in maps or "normal" in maps or "Normal" in maps
                addextras = props.tweak_levels and not (isnormal or isheight)
                colbool = ("Color" in lechan)
                emibool = ("Emission" in lechan)
                noramps = ["Subsurface Radius", "Normal", "Tangent"]
                innoramps = (lechan in noramps)
                okcurve = ((colbool or emibool) and not isdisplacement)
                okramp = (not (colbool or emibool) and (not map_name in noramps)) or (isdisplacement and isheight)
                offsetter_x = -312
                offsetter_y = -312
                lanewnode = tree_nodes.new(type="ShaderNodeTexImage")
                lanewnode.name = Path(panel_line.file_name).name
                lanewnode.label = map_name

                tree_links.new(mapin.outputs[0], lanewnode.inputs['Vector'])

                if addextras:
                    if okcurve:
                        lacurveramp = tree_nodes.new('ShaderNodeRGBCurve')
                        extranode = lacurveramp
                        extranode.label = extranode.name + map_name
                        tree_links.new(lanewnode.outputs[0], lacurveramp.inputs[1])

                    if okramp:
                        laramp = tree_nodes.new('ShaderNodeValToRGB')
                        extranode = laramp
                        tree_links.new(lanewnode.outputs[0], laramp.inputs[0])

                        # tree_links.new(lacurveramp.outputs[0] , mat_output.inputs[2])
                    if okramp or okcurve:
                        extranode.label = extranode.name + map_name

                if isnormal and not skip_normals:
                    normalmapnode = tree_nodes.new('ShaderNodeNormalMap')
                    tree_links.new(lanewnode.outputs[0], normalmapnode.inputs[1])

                if isheight and not skip_normals:

                    bumpnode = tree_nodes.new('ShaderNodeBump')
                    tree_links.new(lanewnode.outputs[0], bumpnode.inputs[2])
                    bumpnode.inputs[0].default_value = .5
                    if addextras:
                        tree_links.new(extranode.outputs[0], bumpnode.inputs[2])

                if islinked and not isdisplacement and not isdispvector:

                    if isnormal and not skip_normals:
                        if isdisplacement:
                            tree_links.new(normalmapnode.outputs[0], mat_output.inputs[2])

                        else:
                            tree_links.new(normalmapnode.outputs[0], shader_node.inputs[lechan])

                    if isheight and not skip_normals:
                        if isdisplacement:
                            tree_links.new(bumpnode.outputs[0], mat_output.inputs[2])

                        else:
                            tree_links.new(bumpnode.outputs[0], shader_node.inputs[lechan])

                    if not (isheight or isnormal) or skip_normals:
                        if addextras:

                            tree_links.new(extranode.outputs[0], shader_node.inputs[lechan])
                        else:
                            tree_links.new(lanewnode.outputs[0], shader_node.inputs[lechan])

                if isdisplacement:
                    dispmapnode = tree_nodes.new('ShaderNodeDisplacement')
                    dispmapnode.location = (baseloc0_x - 256, baseloc0_y)
                    tree_links.new(dispmapnode.outputs[0], mat_output.inputs['Displacement'])
                    if addextras:
                        tree_links.new(extranode.outputs[0], dispmapnode.inputs['Height'])
                    if isheight and not skip_normals:
                        pass
                    if isnormal and not skip_normals:
                        tree_links.new(normalmapnode.outputs[0], dispmapnode.inputs['Normal'])
                    if (not isnormal or skip_normals) and not addextras:
                        tree_links.new(lanewnode.outputs[0], dispmapnode.inputs['Height'])
                # TODO implement link sanity check
                if isdispvector:  
                    dispvectnode = tree_nodes.new('ShaderNodeVectorDisplacement')
                    dispvectnode.location = (baseloc0_x - 256, baseloc0_y)
                    tree_links.new(dispvectnode.outputs[0], mat_output.inputs['Displacement'])
                    if addextras:
                        tree_links.new(extranode.outputs[0], dispvectnode.inputs['Vector'])
                    if isnormal and not skip_normals:
                        tree_links.new(normalmapnode.outputs[0], dispvectnode.inputs['Vector'])
                        # not sure it makes any sense
                    if (not isnormal or skip_normals) and not addextras:
                        tree_links.new(lanewnode.outputs[0], dispvectnode.inputs['Vector'])

                lanewnode.location = ((base_x + offsetter_x * (int(addextras) + int(isnormal or isheight) + 1)),
                                    (base_y + offsetter_y * mapnumbr))
                #TODO: why ?
                if addextras:  # again to be sure
                    extranode.location = (
                        (base_x + offsetter_x * (int(isnormal or isheight) + 1)), (base_y + offsetter_y * mapnumbr))
                if isheight and not skip_normals:
                    bumpnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                if isnormal and not skip_normals:
                    normalmapnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
                mapnumbr += 1
            gc_params = {'shader':shader_node, 'nodes':tree_nodes}
            shader_node.location[1] = self.get_sockets_center(context,**gc_params) + 128  # just a bit higher
            shader_node.location[0] += 128
            mat_output.location[1] = shader_node.location[1]
            mapin.location = (base_x + offsetter_x * (int(addextras) + int(washn) + 2) + offsetter_x, base_y)
            lescoord.location = (mapin.location[0] + offsetter_x, mapin.location[1])
            ml_params = {'maps':mapin, 'nodes':tree_nodes}
            mapin.location[1] = self.map_links(context,**ml_params)
            lescoord.location[1] = mapin.location[1]

        return

    def setup_nodes(self,context,**params):
        mat = params['mat']
        props = context.scene.bsmprops
        propper = ph()
        #TODO: for indexed in enabled
        panel_lines = [eval(f"bpy.context.scene.panel_line{i}") for i in range(props.panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
        for panel_line in panel_lines:
            args = {'line':panel_line,'mat_name':mat.name}
            active_filepath = propper.find_file(context,**args)
            imagename = imagename = Path(active_filepath).name
            if mat.node_tree.nodes.find(imagename) > 0:
                if Path(active_filepath).is_file():
                    file_path = Path(active_filepath).name
                    bpy.ops.image.open(filepath=active_filepath,show_multiview=False)
                    nodestofill = [nod for nod in mat.node_tree.nodes if nod.name == imagename]
                    for node in nodestofill:
                        node.image = bpy.data.images[imagename]
                        if imagename.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                            node.image.colorspace_settings.name = 'Non-Color'

                    bpy.ops.bsm.reporter(reporting=f"Texture file {imagename} assigned in {mat.name}")
                else:
                    bpy.ops.bsm.reporter(reporting=f"Texture {imagename} not found")
            else:
                bpy.ops.bsm.reporter(reporting=f"node label {imagename} not found")   
        return

    def map_links(self,context,**params):
        mapin = params['maps']
        nodes = params['nodes']
        ylocs = []
        connected = list(linked for linked in mapin.outputs[0].links if linked.is_valid)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.to_node.location[1])
        else:
            for nod in nodes:
                ylocs.append(nod.location[1])
        ylocs.sort()
        center = (ylocs[0] + ylocs[-1]) / 2
        return center   
    
    def selector(self,context):
        viewl = context.view_layer
        props = context.scene.bsmprops
        only_active_obj = props.only_active_obj
        applytoall = props.apply_to_all

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
                

        return selected
    
    def move_nodes(self,context,**params):
        scene = context.scene
        mat_active = params['mat']
        shader_node = params['shader']
        nodes = params['nodes']
        props = scene.bsmprops
        #TODO: useless:
        old_shader = params['old_shader']
        replace = props.replace_shader
        panel_rows = props.panel_rows
        imgs = list(nod for nod in nodes if nod.type == 'TEX_IMAGE')

        enabled = list(k for k in range(panel_rows) if eval(f"bpy.context.scene.panel_line{k}.line_on"))
        adding = len(enabled)
        listofshadernodes = []  # TODO get a list of all shadernodes
        ylocsall = []
        ylocsimg = []

        for nod in nodes:
            replacedshader = replace and (nod != shader_node)
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
            existing = (nod for nod in nodes if nod.type != "OUTPUT_MATERIAL" and not nod == shader_node)
            newclustersize_y = 888 * (adding / 2)
            if not adding > 0 and replace:
                newclustersize_y = 1024
            offsetter_y = newclustersize_y

            for nodez in existing:
                nodez.location = (nodez.location[0] - 512, nodez.location[1] + offsetter_y)

        return

    def get_sockets_center(self,context,**params):
        shader_node = params['shader']
        nodes = params['nodes']
        ylocs = []
        connected = list(linked for linked in shader_node.inputs if linked.is_linked)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.links[0].from_node.location[1])
        else:
            for nod in nodes:
                ylocs.append(nod.location[1])
        ylocs.sort()
        center = (ylocs[0] + ylocs[-1]) / 2
        return center

