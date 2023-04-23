import bpy
from pathlib import Path
from . propertieshandler import PropertiesHandler as ph
import json 

class SelectionSet():
    """
    Selection saved and restored after script execution
    
    """

    def __init__(self):
        """Stores selection safely"""
        bpy.context.view_layer.update()
        self.selection = [obj.name for obj in bpy.context.selected_objects]
        self.active = bpy.context.active_object
        self.materials = bpy.data.materials
        
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
        out_args = {'already_done':[],'report':""}
        out_args2 = {'thing':"thing"}
        with SelectionSet():    
            for obj in selected:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                out_args = self.process_materials(context,**{'out_args':out_args,'method':params['method'],'selection':obj})
                obj.select_set(False)
            SelectionSet.materials = bpy.data.materials    
        return out_args

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
        # and eval(f"bpy.context.scene.panel_line{i}.input_sockets") != '' 
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
                new_shader_link.input_sockets = json.dumps((dict(zip(range(len(new_node.inputs)), [inputs.name for inputs in new_node.inputs]))))
                new_shader_link.outputsockets = json.dumps((dict(zip(range(len(new_node.outputs)), [outputs.name for outputs in new_node.outputs]))))

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
        out_args = params['out_args']
        already_done = out_args['already_done']
        method = eval(f"self.{params['method']}")
        obj = params['selection']
        mat_slots = [mat.material for mat in obj.material_slots]
        props = context.scene.bsmprops
        og_mat = obj.active_material
        if props.only_active_mat:
            mat_slots = [obj.active_material]
        for mat_active in mat_slots:
            if mat_active is not None :
                obj.active_material = mat_active
                if mat_active.name not in out_args['already_done']:
                    mat_active.use_nodes = True
                    out_args = method(context,**{'selection':obj,'out_args':out_args,'mat_active':mat_active,'tree_nodes':mat_active.node_tree.nodes,'tree_links':mat_active.node_tree.links})
                    out_args['already_done'].append(mat_active.name)
                else :
                    out_args['report'] = out_args['report'] + "\n" + f"skipping{mat_active.name} as it has already been processed" 
                    continue   
        obj.active_material = og_mat
        return out_args

    def get_shader_node(self,context,**params):
        props = context.scene.bsmprops
        shader_node = params['first_node']
        if params['inv'] or props.replace_shader:
            substitute_shader = props.shaders_list
            #handles custom shaders
            if substitute_shader in context.scene.node_links:
                new_node = params['tree_nodes'].new('ShaderNodeGroup')
                new_node.node_tree = bpy.data.node_groups[substitute_shader]
            else:
                new_node = params['tree_nodes'].new(substitute_shader)
            params['tree_links'].new(new_node.outputs[0], params['mat_output'].inputs[0])
            return new_node
        return shader_node

    def get_output_node(self,context,**params):
        out_nodes = [n for n in params['tree_nodes'] if n.type == "OUTPUT_MATERIAL"]
        for node in out_nodes:
            if node.is_active_output:
                return node
        return params['tree_nodes'].new("ShaderNodeOutputMaterial")
        
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
        propper = ph()
        mat_name = propper.mat_name_cleaner(context)[1] 
        map_node = params['tree_nodes'].new('ShaderNodeMapping')
        map_node.label = f"{mat_name} Mapping"
        tex_coord_node = params['tree_nodes'].new('ShaderNodeTexCoord')
        tex_coord_node.label = f"{mat_name} Coordinates"
        if not tex_coord_node.outputs[0].is_linked:
            params['tree_links'].new(tex_coord_node.outputs['UV'], map_node.inputs['Vector'])
        return map_node,tex_coord_node

    def make_new_image_node(self,context,**params):
        panel_line = params['line']
        new_image_node = params['tree_nodes'].new(type="ShaderNodeTexImage")
        #print(f"setting file name as {Path(panel_line.file_name).name}")
        new_image_node.name = Path(panel_line.file_name).name
        new_image_node.label = params['map_name']
        params['tree_links'].new(params['map_node'].outputs[0], new_image_node.inputs['Vector'])
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
        if bools['add_extras']:
            if bools['add_curve']:
                curve_ramp = params['tree_nodes'].new('ShaderNodeRGBCurve')
                extra_node = curve_ramp
                extra_node.label = f"{extra_node.name}{params['map_name']}"
                params['tree_links'].new(params['new_image_node'].outputs[0], curve_ramp.inputs[1])
            if bools['add_ramp']:
                ramp = params['tree_nodes'].new('ShaderNodeValToRGB')
                extra_node = ramp
                params['tree_links'].new(params['new_image_node'].outputs[0], ramp.inputs[0])
            if bools['add_ramp'] or bools['add_curve']:
                extra_node.label = f"{extra_node.name}{params['map_name']}"
            return extra_node
        return None

    def handle_disp_nodes_1(self,context,**params):
        bools = params['bools']
        params['bump_map_node'] = params['tree_nodes'].new('ShaderNodeBump')
        params['tree_links'].new(params['new_image_node'].outputs[0], params['bump_map_node'].inputs[2])
        params['bump_map_node'].inputs[0].default_value = .5
        if bools['add_extras']:
            params['tree_links'].new(params['extra_node'].outputs[0], params['bump_map_node'].inputs[2])
        return params['bump_map_node']

    def handle_disp_nodes_2(self,context,**params):
        bools = params['bools']
        socket = params['line'].input_sockets
        if bools['has_normal'] and not bools['skip_normals']:
            if bools['displaced']:
                params['tree_links'].new(params['normal_map_node'].outputs[0], params['mat_output'].inputs[2])
            else:
                params['tree_links'].new(params['normal_map_node'].outputs[0], params['shader_node'].inputs[socket])
        if bools['has_height'] and not bools['skip_normals']:
            if bools['displaced']:
                params['tree_links'].new(params['bump_map_node'].outputs[0], params['mat_output'].inputs[2])
            else:
                params['tree_links'].new(params['bump_map_node'].outputs[0], params['shader_node'].inputs[socket])
        if not (bools['has_height'] or bools['has_normal']) or bools['skip_normals']:
            if bools['add_extras']:
                params['tree_links'].new(params['extra_node'].outputs[0], params['shader_node'].inputs[socket])
            else: 
                params['tree_links'].new(params['new_image_node'].outputs[0], params['shader_node'].inputs[socket])
    
    def handle_disp_nodes_3(self,context,**params):
        bools = params['bools']
        disp_map_node = params['tree_nodes'].new('ShaderNodeDisplacement')
        disp_map_node.location = (params['mat_output'].location[0] - 256, params['mat_output'].location[1])
        params['tree_links'].new(disp_map_node.outputs[0], params['mat_output'].inputs['Displacement'])
        if bools['add_extras']:
            params['tree_links'].new(params['extra_node'].outputs[0], disp_map_node.inputs['Height'])
        if bools['has_height'] and not bools['skip_normals']:
            pass
        if bools['has_normal'] and not bools['skip_normals']:
            params['tree_links'].new(params['normal_map_node'].outputs[0], disp_map_node.inputs['Normal'])
        if (not bools['has_normal'] or bools['skip_normals']) and not bools['add_extras']:
            params['tree_links'].new(params['new_image_node'].outputs[0], disp_map_node.inputs['Height'])
    
    def handle_disp_nodes_4(self,context,**params):
        bools = params['bools']
        disp_vec_node = params['tree_nodes'].new('ShaderNodeVectorDisplacement')
        disp_vec_node.location = (params['mat_output'].location[0] - 256, params['mat_output'].location[1])
        params['tree_links'].new(disp_vec_node.outputs[0], params['mat_output'].inputs['Displacement'])
        if bools['add_extras']:
            params['tree_links'].new(params['extra_node'].outputs[0], disp_vec_node.inputs['Vector'])
        if bools['has_normal'] and not bools['skip_normals']:
            params['tree_links'].new(params['normal_map_node'].outputs[0], disp_vec_node.inputs['Vector'])
        if (not bools['has_normal'] or bools['skip_normals']) and not bools['add_extras']:
            params['tree_links'].new(params['new_image_node'].outputs[0], disp_vec_node.inputs['Vector'])
    
    def handle_bumps(self,context,**params):
        bools = params['bools']
        iterator = int(params['iterator'])
        socket = params['line'].input_sockets
        
        params['extra_node'] = self.check_add_extras(context,**params)

        params['new_image_node'].location = (
                                  (params['base_x'] + params['offsetter_x'] * (int(bools['add_extras']) + int(bools['has_normal'] or bools['has_height']) + 1)),
                                  (params['base_y'] + params['offsetter_y'] * iterator)
                                  )
        if bools['has_normal'] and not bools['skip_normals']:
            params['normal_map_node'] = params['tree_nodes'].new('ShaderNodeNormalMap')
            uvs = [uv.name for uv in params['selection'].data.uv_layers if uv.active_render]
            if len(uvs) > 0:
                params['normal_map_node'].uv_map = next(iter(uvs))
            params['tree_links'].new(params['new_image_node'].outputs[0], params['normal_map_node'].inputs[1])
        
        if bools['has_height'] and not bools['skip_normals']:
            params['bump_map_node'] = self.handle_disp_nodes_1(context,**params)
            
        if socket != "0" and not bools['displaced'] and not ('Disp Vector' in socket):
            self.handle_disp_nodes_2(context,**params)
            
        if bools['displaced']:
            self.handle_disp_nodes_3(context,**params)
        
        if ('Disp Vector' in socket):  
            self.handle_disp_nodes_4(context,**params)
        
        if bools['add_extras']:  # again to be sure
            params['extra_node'].location = (
                (params['base_x'] + params['offsetter_x'] * (int(bools['has_normal'] or bools['has_height']) + 1)), (params['base_y'] + params['offsetter_y'] * iterator))
        if bools['has_height'] and not bools['skip_normals']:
            params['bump_map_node'].location = (params['base_x'] + params['offsetter_x'], params['base_y'] + params['offsetter_y'] * iterator)
        if bools['has_normal'] and not bools['skip_normals']:
            params['normal_map_node'].location = (params['base_x'] + params['offsetter_x'], params['base_y'] + params['offsetter_y'] * iterator)
        iterator += 1
        return iterator

    def print_dict(self,args):
        msg = ""
        for k, v in args.items():
            if k not in ["already_done", "img_loaded"] and isinstance(v, dict):
                self.print_dict(v)
            elif(k not in ["already_done", "img_loaded"]):
                msg = f"{msg}{v}\n "
        return msg

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
        if params['line'].manual:
            return Path(params['line'].file_name).name
        return params['line'].map_label
    
    def create_nodes(self,context,**params):
        out_args = params['out_args']
        m_params = self.get_mat_params(context)
        if len(m_params['maps']) == 0:
            return
        propper = ph()
        scene = context.scene
        props = scene.bsmprops
        if props.clear_nodes:
            params['tree_nodes'].clear()
        args = {'selection':params['selection'],'tree_nodes':params['tree_nodes'],'tree_links':params['tree_links'],'offsetter_x':-312,'offsetter_y':-312,'mat_active':params['mat_active'],'props':props,'maps':m_params['maps']}
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
            #if there is a node plugged into a metallic socket spec should be 0 for PBR-related reasons
            if "metal" in args['line'].input_sockets.lower() and "Specular" in args['shader_node'].inputs:
                args['shader_node'].inputs['Specular'].default_value = 0
            args['bools'] = self.set_bools_params(context,**args)
            args['new_image_node'] = self.make_new_image_node(context,**args)
            args['iterator'] = iterator
            iterator = self.handle_bumps(context,**args)
            out_args['report'] = f"{out_args['report']} \n Image texture node created in {args['mat_active'].name} for {args['line'].map_label} map "
        self.arrange_last_nodes(context,**args)
        return out_args

    def setup_nodes(self,context,**params):
        props = context.scene.bsmprops
        propper = ph()
        out_args = params['out_args']
        panel_lines = [eval(f"bpy.context.scene.panel_line{i}") for i in range(props.panel_rows) if eval(f"bpy.context.scene.panel_line{i}.line_on")]
        out_args['img_loaded'] = 0
        mat_name = propper.mat_name_cleaner(context)[1]
        for panel_line in panel_lines:
            args = {'line':panel_line,'mat_name':mat_name}
            active_filepath = propper.find_file(context,**args)
            if active_filepath != "" :
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
                            out_args['img_loaded'] += 1
                        out_args['report'] = f"{out_args['report']} \n Texture file {image_name} assigned to {panel_line.map_label} node in {params['mat_active'].name} "
                    else:
                        out_args['report'] = f"{out_args['report']} \n Texture {image_name} not found "
                else:
                    out_args['report'] = f"{out_args['report']} \n node {image_name} not found, run Setup Nodes before " 
            else:
                out_args['report'] = f"{out_args['report']} \n No image found matching {panel_line.map_label} for material: {params['mat_active'].name} in folder {props.usr_dir}"
        return out_args    

    def map_links(self,context,**params):
        locs_y = []
        connected = list(linked for linked in params['map_node'].outputs[0].links if linked.is_valid)
        if len(connected) > 0:
            for linked in connected:
                locs_y.append(linked.to_node.location[1])
        else:
            for nod in params['tree_nodes']:
                locs_y.append(nod.location[1])
        locs_y.sort()
        center = (locs_y[0] + locs_y[-1]) / 2
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
        params['shader_node'].location = (params['base_x'],params['base_y'])
        replace = params['props'].replace_shader
        panel_rows = params['props'].panel_rows
        imgs = [nod for nod in params['tree_nodes'] if nod.type == 'TEX_IMAGE']
        lines = len([k for k in range(panel_rows) if eval(f"bpy.context.scene.panel_line{k}.line_on")])
        new_cluster_height = 0
        if bool(lines + int(replace)):
            existing = [nod for nod in params['tree_nodes'] if nod.type != "OUTPUT_MATERIAL" and not nod == params['shader_node']]
            new_cluster_height = 888 * (lines / 2)
            if not lines > 0 and replace:
                new_cluster_height = 1024
            params['offsetter_y'] = new_cluster_height
            for node in existing:
                node.location = (node.location[0] - 512, node.location[1] + params['offsetter_y'])

    def get_sockets_center(self,context,**params):
        params['shader_node'].location = (params['base_x'],params['base_y'])
        locs_y = []
        connected = list(linked for linked in params['shader_node'].inputs if linked.is_linked)
        if len(connected) > 0:
            for linked in connected:
                locs_y.append(linked.links[0].from_node.location[1])
        else:
            for node in params['mat_active'].node_tree.nodes:
                locs_y.append(node.location[1])
        locs_y.sort()
        center = (locs_y[0] + locs_y[-1]) / 2
        return center

