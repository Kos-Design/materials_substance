import bpy
from pathlib import Path
from . propertieshandler import props, shader_links, node_links, PropertiesHandler,lines
import json

propper = PropertiesHandler()

class NodeHandler():

    def handle_nodes(self,context,create=False):
        propper.refresh_shader_links(context)
        selected = self.get_target_mats(context)
        p_lines = [line for line in lines() if line.line_on]
        out_args = {'already_done':[],'report':""}
        for mat in selected:
            out_args = self.process_materials(context,**{'out_args':out_args,'create':create,'p_lines':p_lines,'mat':mat})
        return out_args

    def get_target_mats(self,context):
        mat_list = []
        validtypes = ['SURFACE', 'CURVE', 'META', 'MESH', 'GPENCIL']
        match props().target:
            case "selected_objects":
                if len(context.view_layer.objects):
                    mat_list = list({mat.material for obj in context.view_layer.objects.selected if obj.type in validtypes for mat in obj.material_slots if mat.material is not None})
            case "all_visible":
                if len(context.view_layer.objects):
                    mat_list = list({mat.material for obj in context.view_layer.objects if obj.visible_get() and obj.type in validtypes for mat in obj.material_slots if mat.material is not None})
            case "all_objects":
                if len(bpy.data.objects):
                    mat_list = list({mat.material for obj in bpy.data.objects if obj.type in validtypes for mat in obj.material_slots if mat.material is not None})
            case "all_materials":
                mat_list = bpy.data.materials
            case "active_obj":
                obj = context.view_layer.objects.active if context.view_layer.objects.active in list(context.view_layer.objects.selected) else None
                if obj and obj.type in validtypes:
                    mat_list = list({mat.material for mat in obj.material_slots if mat.material is not None})
        return mat_list

    def get_mat_params(self,context):
        maps = []
        chans = []
        p_lines = [line for line in lines() if line.line_on]
        for line in p_lines:
            chans.append(line.input_sockets)
            if line.manual:
                maps.append(str(Path(line.file_name).name))
            else:
                maps.append(line.name)
        return {"maps":maps, "chans":chans, "p_lines":p_lines}

    def process_materials(self,context,**params):
        out_args = params['out_args']
        already_done = out_args['already_done']
        method = self.create_nodes if params['create'] else self.setup_nodes
        mat = params['mat']
        p_lines = params['p_lines']
        mat.use_nodes = True
        out_args = method(context,**{'out_args':out_args,'p_lines':p_lines,
                                    'mat':mat,'tree_nodes':mat.node_tree.nodes,
                                    'tree_links':mat.node_tree.links})
        out_args['already_done'].append(mat.name)
        return out_args

    def get_shader_node(self,context,**params):
        shader_node = params['first_node']
        if params['inv'] or props().replace_shader or props().clear_nodes:
            substitute_shader = props().shaders_list
            #handles custom shaders
            if substitute_shader in bpy.data.node_groups.keys():
                shader_node = params['tree_nodes'].new('ShaderNodeGroup')
                shader_node.node_tree = bpy.data.node_groups[substitute_shader]
            elif hasattr(bpy.types,substitute_shader) :
                shader_node = params['tree_nodes'].new(substitute_shader)
            else :
                node_links().clear()
                propper.set_nodes_groups(context)
                propper.refresh_shader_links(context)
                propper.guess_sockets(context)
                if substitute_shader in bpy.data.node_groups.keys():
                    shader_node = params['tree_nodes'].new('ShaderNodeGroup')
                    shader_node.node_tree = bpy.data.node_groups[substitute_shader]
                else:
                    print("Error during custom shaders gathering")
                    return
            shader_node.name = "NODE_" + shader_node.name
            params['tree_links'].new(shader_node.outputs[0], params['mat_output'].inputs[0])
            context.view_layer.update()
        if not (params['inv'] or props().clear_nodes):
            self.copy_bsdf_parameters(params['first_node'], shader_node)
            if props().replace_shader:
                params['tree_nodes'].remove(params['first_node'])
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
        mat_name = propper.mat_name_cleaner(context)[1]
        map_node = params['tree_nodes'].new('ShaderNodeMapping')
        map_node.label = f"{mat_name} Mapping"
        map_node.name = f"NODE_{map_node.name}"
        tex_coord_node = params['tree_nodes'].new('ShaderNodeTexCoord')
        tex_coord_node.label = f"{mat_name} Coordinates"
        tex_coord_node.name = f"NODE_{tex_coord_node.name}"
        if not tex_coord_node.outputs[0].is_linked:
            params['tree_links'].new(tex_coord_node.outputs['UV'], map_node.inputs['Vector'])
        return map_node,tex_coord_node

    def make_new_image_node(self,context,**params):
        line = params['line']
        new_image_node = params['tree_nodes'].new(type="ShaderNodeTexImage")
        new_image_node.name = "NODE_" + Path(line.file_name).name
        new_image_node.label = params['map_name']
        params['tree_links'].new(params['map_node'].outputs[0], new_image_node.inputs['Vector'])
        return new_image_node

    def set_bools_params(self,context,**params):
        line = params['line']
        socket = line.input_sockets
        map_name = params['map_name']
        displaced = ("displacement" in socket.lower())
        has_normal = ("normal" in map_name.lower())
        has_height = ("height" in map_name.lower())
        add_extras = props().tweak_levels and not (has_normal or has_height)
        skip_ramps = len([x for x in ["subsurface radius", "normal", "tangent"] if map_name.lower() in x]) > 0
        add_curve = ((("color" in socket.lower()) or ("emission" in socket.lower())) and not displaced)
        add_ramp = (not (("color" in socket.lower()) or ("emission" in socket.lower())) and (not skip_ramps)) or (displaced and has_height)
        return {'skip_normals':props().skip_normals,'displaced':displaced,'has_normal':has_normal,
                'has_height':has_height,'add_extras':add_extras,'add_curve':add_curve,'add_ramp':add_ramp}

    def check_add_extras(self,context,**params):
        bools = params['bools']
        if bools['add_extras']:
            if bools['add_curve']:
                curve_ramp = params['tree_nodes'].new('ShaderNodeRGBCurve')
                extra_node = curve_ramp
                params['tree_links'].new(params['new_image_node'].outputs[0], curve_ramp.inputs[1])
            if bools['add_ramp']:
                ramp = params['tree_nodes'].new('ShaderNodeValToRGB')
                extra_node = ramp
                params['tree_links'].new(params['new_image_node'].outputs[0], ramp.inputs[0])
            if bools['add_ramp'] or bools['add_curve']:
                extra_node.label = f"{extra_node.name}{params['map_name']}"
                extra_node.name = f"NODE_{extra_node.name}"
            return extra_node
        return None

    def handle_disp_nodes_1(self,context,**params):
        bools = params['bools']
        params['bump_map_node'] = params['tree_nodes'].new('ShaderNodeBump')
        params['bump_map_node'].name = f"NODE_{params['bump_map_node'].name}"
        params['tree_links'].new(params['new_image_node'].outputs[0], params['bump_map_node'].inputs[2])
        params['bump_map_node'].inputs[0].default_value = .5
        if bools['add_extras']:
            params['tree_links'].new(params['extra_node'].outputs[0], params['bump_map_node'].inputs[2])
        return params['bump_map_node']

    def handle_disp_nodes_2(self,context,**params):
        bools = params['bools']
        socket = params['line'].input_sockets
        multi_sockets = params['line'].channels.socket
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
            elif params['line'].split_rgb:
                separate_rgb = params['tree_nodes'].new(type="ShaderNodeSeparateColor")
                separate_rgb.location = params['shader_node'].location
                separate_rgb.location.x -= 69
                params['tree_links'].new(params['new_image_node'].outputs[0], separate_rgb.inputs[0])
                for i,sock in enumerate(params['line'].channels.socket):
                    if '0' not in sock.input_sockets :
                        params['tree_links'].new(separate_rgb.outputs[i], params['shader_node'].inputs[sock.input_sockets])
            else:
                params['tree_links'].new(params['new_image_node'].outputs[0], params['shader_node'].inputs[socket])

    def handle_disp_nodes_3(self,context,**params):
        bools = params['bools']
        disp_map_node = params['tree_nodes'].new('ShaderNodeDisplacement')
        disp_map_node.name = f"NODE_{disp_map_node.name}"
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
        disp_vec_node.name = f"NODE_{disp_vec_node.name}"
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
            params['normal_map_node'].name = f"NODE_{params['normal_map_node'].name}"
            """
            #need object using this mat to get uv map name, but I think it is fine to let it blank
            uvs = [uv.name for uv in params['selection'].data.uv_layers if uv.active_render]
            if len(uvs) > 0:
                params['normal_map_node'].uv_map = next(iter(uvs))
            """
            params['tree_links'].new(params['new_image_node'].outputs[0], params['normal_map_node'].inputs[1])

        if bools['has_height'] and not bools['skip_normals']:
            params['bump_map_node'] = self.handle_disp_nodes_1(context,**params)

        if socket != "0" and not bools['displaced'] and not ('Disp Vector' in socket):
            self.handle_disp_nodes_2(context,**params)

        if bools['displaced']:
            self.handle_disp_nodes_3(context,**params)

        if ('Disp Vector' in socket):
            self.handle_disp_nodes_4(context,**params)

        if bools['add_extras']:
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
        return params['line'].name

    def clean_stm_nodes(self,context,**params):
        for node in params['tree_nodes']:
            if node.name.startswith("NODE_") and not node.bl_idname in props().shaders_list:
                params['tree_nodes'].remove(node)

    def copy_bsdf_parameters(self,source_node, target_node):
        # Ensure both nodes are Principled BSDF nodes
        if source_node.bl_idname == target_node.bl_idname :
            for input_source, input_target in zip(source_node.inputs, target_node.inputs):
                # Check if the input has a valid default_value attribute to copy (skip non-scalar inputs like sockets)
                if hasattr(input_source, 'default_value'):
                    input_target.default_value = input_source.default_value

    def create_nodes(self,context,**params):
        out_args = params['out_args']
        if props().clear_nodes:
            params['tree_nodes'].clear()
            context.view_layer.update()
            params['tree_nodes'] = params['mat'].node_tree.nodes
        m_params = self.get_mat_params(context)
        args = {'tree_nodes':params['tree_nodes'],'tree_links':params['tree_links'],
                'offsetter_x':-312,'offsetter_y':-312,'mat':params['mat'],
                'p_lines':params['p_lines'],'maps':m_params['maps']}
        self.clean_stm_nodes(context,**args)
        args['mat_output'] = self.get_output_node(context,**args)
        first_node,invalid_shader = self.get_first_node(context,**args)
        args['first_node'] = first_node
        args['inv'] = invalid_shader
        args['shader_node'] = self.get_shader_node(context,**args)
        args['base_x'] = args['mat_output'].location[0] - 404 * 2
        args['base_y'] = args['mat_output'].location[1]
        self.move_nodes(context,**args)
        if len(m_params['maps']) == 0:
            return out_args
        map_node,tex_coord_node = self.make_tex_mapping_nodes(context,**args)
        args['map_node'] = map_node
        args['tex_coord_node'] = tex_coord_node
        iterator = 0
        for line in m_params['p_lines']:
            args['line'] = line
            if not args['line'].manual:
                propper.detect_a_map(context, line)
            args['map_name'] = self.get_map_name(context,**args)
            #if there is a node plugged into a metallic socket spec should be 0 for PBR-related reasons
            if "metal" in args['line'].input_sockets.lower() and "Specular" in args['shader_node'].inputs:
                args['shader_node'].inputs['Specular'].default_value = 0
            args['bools'] = self.set_bools_params(context,**args)
            args['new_image_node'] = self.make_new_image_node(context,**args)
            args['iterator'] = iterator
            iterator = self.handle_bumps(context,**args)
            out_args['report'] = f"{out_args['report']} \n Image texture node created in {args['mat'].name} for {args['line'].name} map "
        self.arrange_last_nodes(context,**args)
        return out_args

    def setup_nodes(self,context,**params):
        out_args = params['out_args']
        p_lines = [line for line in lines() if line.line_on]
        out_args['img_loaded'] = 0
        mat_name = propper.mat_name_cleaner(context)[1]
        for line in p_lines:
            args = {'line':line,'mat_name':mat_name}
            active_filepath = propper.find_file(context,**args)
            if active_filepath != "" :
                image_name = Path(active_filepath).name
                if params['mat'].node_tree.nodes.find(f"NODE_{image_name}") > 0:
                    if Path(active_filepath).is_file():
                        file_path = Path(active_filepath).name
                        image = bpy.data.images.load(filepath=active_filepath) if not image_name in bpy.data.images else bpy.data.images[image_name]
                        nodes_to_fill = [nod for nod in params['mat'].node_tree.nodes if self.strip_digits(nod.name).replace(" ", "").lower() in image_name.replace(" ", "").lower()]
                        for node in nodes_to_fill:
                            node.image = bpy.data.images[image.name]
                            if image_name.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                                node.image.colorspace_settings.name = 'Non-Color'
                            out_args['img_loaded'] += 1
                        out_args['report'] = f"{out_args['report']} \n Texture file {image_name} assigned to {line.name} node in {params['mat'].name} "
                    else:
                        out_args['report'] = f"{out_args['report']} \n Texture {image_name} not found "
                else:
                    out_args['report'] = f"{out_args['report']} \n node {image_name} not found, run Setup Nodes before "
            else:
                out_args['report'] = f"{out_args['report']} \n No image found matching {line.name} for material: {params['mat'].name} in folder {props().usr_dir}"
        return out_args

    def strip_digits(self,_text):
        if "NODE_" in _text :
            _text = _text.replace("NODE_", "")
        if _text[-3:].isdigit():
            _text = _text[:-4]
        return _text

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

    def move_nodes(self,context,**params):
        params['shader_node'].location = (params['base_x'],params['base_y'])
        replace = props().replace_shader
        imgs = [nod for nod in params['tree_nodes'] if nod.type == 'TEX_IMAGE']
        not_empty = len(params['p_lines'])
        new_cluster_height = 0
        if not_empty and replace:
            existing = [nod for nod in params['tree_nodes'] if nod.type != "OUTPUT_MATERIAL" and not nod == params['shader_node']]
            new_cluster_height = 888 * (not_empty / 2)
            if not not_empty > 0 and replace:
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
            for node in params['mat'].node_tree.nodes:
                locs_y.append(node.location[1])
        locs_y.sort()
        center = (locs_y[0] + locs_y[-1]) / 2
        return center
