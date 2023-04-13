import bpy
from pathlib import Path
from . propertieshandler import PropertiesHandler as ph
 

class SelectionSet():
    """
    Selection saved and restored after script execution
    
    """

    def __init__(self):
        """Stores selection safely"""
        bpy.context.view_layer.update()
        self.selection = [obj.name for obj in bpy.context.selected_objects]
        self.active = bpy.context.active_object
        
    def __enter__(self):
        """Clears original selection"""
        for obj in self.selection:
            bpy.context.view_layer.objects[obj].select_set(False)
       
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Restoring selection"""
        bpy.context.view_layer.objects.active = self.active
        for obj in self.selection :
            bpy.context.view_layer.objects[obj].select_set(True)
        self.active.select_set(True)


class NodeHandler():

    def handle_nodes(self,context,**params):
        method = eval(f"self.{params['method']}")
        self.refresh_shader_links(context)
        selected = self.selector(context)
        already_done = []
        with SelectionSet():    
            for obj in selected:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                already_done = self.process_materials(context,**{'method':method,'selection':obj,'already_done':already_done})
                obj.select_set(False)

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
        method = params['method']
        obj = params['selection']
        mat_slots = [mat.material for mat in obj.material_slots]
        props = context.scene.bsmprops
        og_mat = obj.active_material
        if props.only_active_mat:
            mat_slots = [obj.active_material]
        for mat_active in mat_slots:
            if mat_active is not None :
                obj.active_material = mat_active
                if mat_active.name not in already_done:
                    mat_active.use_nodes = True
                    method(context,**{'mat_active':mat_active})
                    already_done.append(mat_active.name)
        obj.active_material = og_mat
        return already_done

    def get_shader_node(self,context,**params):
        props = context.scene.bsmprops
        tree_nodes = params['mat_active'].node_tree.nodes
        tree_links = params['mat_active'].node_tree.links
        shader_node = params['first_node']
        if params['inv'] or props.replace_shader:
            substitute_shader = props.shaders_list
            #handles custom shaders
            if substitute_shader in context.scene.node_links:
                new_node = tree_nodes.new('ShaderNodeGroup')
                new_node.node_tree = bpy.data.node_groups[substitute_shader]
            else:
                new_node = tree_nodes.new(substitute_shader)
            tree_links.new(new_node.outputs[0], params['mat_output'].inputs[0])
            shader_node = new_node
        if shader_node.type == 'BSDF_PRINCIPLED':
            shader_node.inputs['Specular'].default_value = 0

        return shader_node

    def get_output_node(self,context,**params):
        tree_nodes = params['mat_active'].node_tree.nodes
        out_nodes = [n for n in tree_nodes if n.type == "OUTPUT_MATERIAL"]
        for node in out_nodes:
            if node.is_active_output:
                return node
        return tree_nodes.new("ShaderNodeOutputMaterial")
        
    def get_first_node(self,context,**params):
        sur_node = params['mat_output'].inputs['Surface']
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
    
    def make_tex_mapping_nodes(self,context,**params):
        tree_nodes = params['mat_active'].node_tree.nodes
        tree_links = params['mat_active'].node_tree.links
        map_node = tree_nodes.new('ShaderNodeMapping')
        map_node.label = f"{params['mat_active'].name} Mapping"
        tex_coord_node = tree_nodes.new('ShaderNodeTexCoord')
        tex_coord_node.label = f"{params['mat_active'].name} Coordinates"
        if not tex_coord_node.outputs[0].is_linked:
                tree_links.new(tex_coord_node.outputs['UV'], map_node.inputs['Vector'])
        return map_node,tex_coord_node

    def make_new_image_node(self,context,**params):
        panel_line = params['line']
        map_name = params['map_name']
        tree_links = params['mat_active'].node_tree.links
        tree_nodes = params['mat_active'].node_tree.nodes
        new_image_node = tree_nodes.new(type="ShaderNodeTexImage")
        new_image_node.name = Path(panel_line.file_name).name
        new_image_node.label = map_name
        tree_links.new(params['map_node'].outputs[0], new_image_node.inputs['Vector'])
        return new_image_node

    def set_bools_params(self,context,**params):
        panel_line = params['line'] 
        socket = panel_line.input_sockets
        map_name = params['map_name']
        props = params['props']
        displaced = ("displacement" in socket.lower())
        has_normal = ("normal" in map_name.lower())
        has_height = ("height" in map_name.lower())
        add_extras = props.tweak_levels and not (has_normal or has_height)
        skip_ramps = len([x for x in ["subsurface radius", "normal", "tangent"] if map_name.lower() in x]) > 0
        add_curve = ((("color" in socket.lower()) or ("emission" in socket.lower())) and not displaced)
        add_ramp = (not (("color" in socket.lower()) or ("emission" in socket.lower())) and (not skip_ramps)) or (displaced and has_height)
        return {'skip_normals':props.skip_normals,'displaced':displaced,'has_normal':has_normal,'has_height':has_height,'add_extras':add_extras,'add_curve':add_curve,'add_ramp':add_ramp}
    
    def check_add_extras(self,context,**params):
        bools = params['bools']
        tree_nodes = params['mat_active'].node_tree.nodes
        if bools['add_extras']:
            if bools['add_curve']:
                curve_ramp = tree_nodes.new('ShaderNodeRGBCurve')
                extra_node = curve_ramp
                extra_node.label = f"{extra_node.name}{map_name}"
                tree_links.new(new_image_node.outputs[0], curve_ramp.inputs[1])

            if bools['add_ramp']:
                ramp = tree_nodes.new('ShaderNodeValToRGB')
                extra_node = ramp
                tree_links.new(new_image_node.outputs[0], ramp.inputs[0])
            if bools['add_ramp'] or bools['add_curve']:
                extra_node.label = extra_node.name + map_name
            return extra_node
        return None

    def handle_bumps(self,context,**params):
        bools = params['bools']
        tree_links = params['mat_active'].node_tree.links
        tree_nodes = params['mat_active'].node_tree.nodes
        new_image_node = params['new_image_node']
        iterator = int(params['iterator'])
        panel_line = params['line'] 
        socket = panel_line.input_sockets
        extra_node = self.check_add_extras(context,**params)
        new_image_node.location = (
                                  (params['base_x'] + params['offsetter_x'] * (int(bools['add_extras']) + int(bools['has_normal'] or bools['has_height']) + 1)),
                                  (params['base_y'] + params['offsetter_y'] * iterator)
                                  )
        if bools['has_normal'] and not bools['skip_normals']:
            normal_map_node = tree_nodes.new('ShaderNodeNormalMap')
            tree_links.new(new_image_node.outputs[0], normal_map_node.inputs[1])
        if bools['has_height'] and not bools['skip_normals']:
            bump_map_node = tree_nodes.new('ShaderNodeBump')
            tree_links.new(new_image_node.outputs[0], bump_map_node.inputs[2])
            bump_map_node.inputs[0].default_value = .5
            if bools['add_extras']:
                tree_links.new(extra_node.outputs[0], bump_map_node.inputs[2])
        if socket != "0" and not bools['displaced'] and not ('Disp Vector' in socket):
            if bools['has_normal'] and not bools['skip_normals']:
                if bools['displaced']:
                    tree_links.new(normal_map_node.outputs[0], params['mat_output'].inputs[2])
                else:
                    tree_links.new(normal_map_node.outputs[0], params['shader_node'].inputs[socket])
            if bools['has_height'] and not bools['skip_normals']:
                if bools['displaced']:
                    tree_links.new(bump_map_node.outputs[0], params['mat_output'].inputs[2])
                else:
                    tree_links.new(bump_map_node.outputs[0], params['shader_node'].inputs[socket])
            if not (bools['has_height'] or bools['has_normal']) or bools['skip_normals']:
                if bools['add_extras']:
                    tree_links.new(extra_node.outputs[0], params['shader_node'].inputs[socket])
                else:
                    tree_links.new(new_image_node.outputs[0], params['shader_node'].inputs[socket])
        if bools['displaced']:
            disp_map_node = tree_nodes.new('ShaderNodeDisplacement')
            disp_map_node.location = (params['mat_output'].location[0] - 256, params['mat_output'].location[1])
            tree_links.new(disp_map_node.outputs[0], params['mat_output'].inputs['Displacement'])
            if bools['add_extras']:
                tree_links.new(extra_node.outputs[0], disp_map_node.inputs['Height'])
            if bools['has_height'] and not bools['skip_normals']:
                pass
            if bools['has_normal'] and not bools['skip_normals']:
                tree_links.new(normal_map_node.outputs[0], disp_map_node.inputs['Normal'])
            if (not bools['has_normal'] or bools['skip_normals']) and not bools['add_extras']:
                tree_links.new(new_image_node.outputs[0], disp_map_node.inputs['Height'])
        # TODO implement link sanity check
        if ('Disp Vector' in socket):  
            disp_vec_node = tree_nodes.new('ShaderNodeVectorDisplacement')
            disp_vec_node.location = (params['mat_output'].location[0] - 256, params['mat_output'].location[1])
            tree_links.new(disp_vec_node.outputs[0], params['mat_output'].inputs['Displacement'])
            if bools['add_extras']:
                tree_links.new(extra_node.outputs[0], disp_vec_node.inputs['Vector'])
            if bools['has_normal'] and not bools['skip_normals']:
                tree_links.new(normal_map_node.outputs[0], disp_vec_node.inputs['Vector'])
                # not sure it makes any sense
            if (not bools['has_normal'] or bools['skip_normals']) and not bools['add_extras']:
                tree_links.new(new_image_node.outputs[0], disp_vec_node.inputs['Vector'])
        if bools['add_extras']:  # again to be sure
            extra_node.location = (
                (params['base_x'] + params['offsetter_x'] * (int(bools['has_normal'] or bools['has_height']) + 1)), (params['base_y'] + params['offsetter_y'] * iterator))
        if bools['has_height'] and not bools['skip_normals']:
            bump_map_node.location = (params['base_x'] + params['offsetter_x'], params['base_y'] + params['offsetter_y'] * iterator)
        if bools['has_normal'] and not bools['skip_normals']:
            normal_map_node.location = (params['base_x'] + params['offsetter_x'], params['base_y'] + params['offsetter_y'] * iterator)
        iterator += 1
        return iterator
            
    def arrange_last_nodes(self,context,**params):
        bools = params['bools']
        params['shader_node'].location[1] = self.get_sockets_center(context,**params) + 128  
        params['shader_node'].location[0] += 128
        params['mat_output'].location[1] = params['shader_node'].location[1]
        bumped = int(len([x for x in params['maps'] if "height" in x.lower()]) + len([y for y in params['maps'] if "normal" in y.lower()]) > 0)
        params['map_node'].location = (params['base_x'] + params['offsetter_x'] * (int(bools['add_extras']) + bumped + 2) + params['offsetter_x'], params['base_y'])
        params['tex_coord_node'].location = (params['map_node'].location[0] + params['offsetter_x'], params['map_node'].location[1])
        params['map_node'].location[1] = self.map_links(context,**params)
        params['tex_coord_node'].location[1] = params['map_node'].location[1]
    
    def get_map_name(self,context,**params):
        panel_line = params['line']
        propper = ph()
        file_name = propper.find_file(context,**{'line':panel_line, 'mat_name':params['mat_active'].name})
        if file_name is not None :
            panel_line.file_name = panel_line.probable = file_name
        manual = panel_line.manual
        map_name = panel_line.map_label
        if manual:
            map_name = Path(panel_line.file_name).name
        return map_name
    
    def create_nodes(self,context,**params):
        m_params = self.get_mat_params(context)
        if len(m_params['maps']) == 0:
            return
        propper = ph()
        scene = context.scene
        props = scene.bsmprops
        if props.clear_nodes:
            params['mat_active'].node_tree.nodes.clear()
        args = {'offsetter_x':-312,'offsetter_y':-312,'mat_active':params['mat_active'],'props':props,'maps':m_params['maps']}
        args['mat_output'] = self.get_output_node(context,**args)
        first_node,invalid_shader = self.get_first_node(context,**args)
        args['first_node'] = first_node
        args['inv'] = invalid_shader
        args['shader_node'] = self.get_shader_node(context,**args)
        args['base_x'] = args['mat_output'].location[0] - 404 * 2
        args['base_y'] = args['mat_output'].location[1]
        self.move_nodes(context,**args)
        map_node,tex_coord_node = self.make_tex_mapping_nodes(context,**args)
        args['map_node'] = map_node
        args['tex_coord_node'] = tex_coord_node
        iterator = 0
        for i in m_params['indexer']:
            args['line'] = eval(f"scene.panel_line{i}")
            args['map_name'] = self.get_map_name(context,**args)
            args['bools'] = self.set_bools_params(context,**args)
            args['new_image_node'] = self.make_new_image_node(context,**args)
            args['iterator'] = iterator
            iterator = self.handle_bumps(context,**args)
        self.arrange_last_nodes(context,**args)
        
    def setup_nodes(self,context,**params):
        props = context.scene.bsmprops
        propper = ph()
        #TODO: for indexed in enabled
        panel_lines = [eval(f"bpy.context.scene.panel_line{i}") for i in range(props.panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
        for panel_line in panel_lines:
            args = {'line':panel_line,'mat_name':params['mat_active'].name}
            active_filepath = propper.find_file(context,**args)
            image_name = Path(active_filepath).name
            if params['mat_active'].node_tree.nodes.find(image_name) > 0:
                if Path(active_filepath).is_file():
                    file_path = Path(active_filepath).name
                    bpy.ops.image.open(filepath=active_filepath,show_multiview=False)
                    nodes_to_fill = [nod for nod in params['mat_active'].node_tree.nodes if nod.name == image_name]
                    for node in nodes_to_fill:
                        node.image = bpy.data.images[image_name]
                        if image_name.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                            node.image.colorspace_settings.name = 'Non-Color'
                    bpy.ops.bsm.reporter(reporting=f"Texture file {image_name} assigned in {params['mat_active'].name}")
                else:
                    bpy.ops.bsm.reporter(reporting=f"Texture {image_name} not found")
            else:
                bpy.ops.bsm.reporter(reporting=f"node label {image_name} not found")   
        
    def map_links(self,context,**params):
        
        tree_nodes = params['mat_active'].node_tree.nodes
        ylocs = []
        connected = list(linked for linked in params['map_node'].outputs[0].links if linked.is_valid)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.to_node.location[1])
        else:
            for nod in tree_nodes:
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
        params['shader_node'].location = (params['base_x'],params['base_y'])
        tree_nodes = params['mat_active'].node_tree.nodes
        props = scene.bsmprops
        replace = props.replace_shader
        panel_rows = props.panel_rows
        imgs = [nod for nod in tree_nodes if nod.type == 'TEX_IMAGE']
        lines = len([k for k in range(panel_rows) if eval(f"bpy.context.scene.panel_line{k}.line_on")])
        new_cluster_height = 0
        if bool(lines + int(replace)):
            existing = [nod for nod in tree_nodes if nod.type != "OUTPUT_MATERIAL" and not nod == params['shader_node']]
            new_cluster_height = 888 * (lines / 2)
            if not lines > 0 and replace:
                new_cluster_height = 1024
            params['offsetter_y'] = new_cluster_height

            for nodez in existing:
                nodez.location = (nodez.location[0] - 512, nodez.location[1] + params['offsetter_y'])

    def get_sockets_center(self,context,**params):
        params['shader_node'].location = (params['base_x'],params['base_y'])
        ylocs = []
        connected = list(linked for linked in params['shader_node'].inputs if linked.is_linked)
        if len(connected) > 0:
            for linked in connected:
                ylocs.append(linked.links[0].from_node.location[1])
        else:
            for node in params['mat_active'].node_tree.nodes:
                ylocs.append(node.location[1])
        ylocs.sort()
        center = (ylocs[0] + ylocs[-1]) / 2
        return center

