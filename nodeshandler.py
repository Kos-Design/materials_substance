import bpy
from pathlib import Path
from . propertieshandler import props, shader_links, node_links, PropertiesHandler,lines,p_lines,MaterialHolder,texture_importer
import json

propper = PropertiesHandler()


class NodeHandler(MaterialHolder):
    def __init__(self):
        super().__init__()
        self.coord_node = None
        self.mapping_node = None
        self.displaced = None
        self.has_normal = None
        self.has_height = None
        self.add_extras = None
        self.add_curve = None
        self.add_ramp = None
        self.output_node = None
        self.new_image_node = None
        self.extra_node = None
        self.bump_map_node = None
        self.normal_map_node = None
        self.base_loc = None
        self.offsetter_x = None
        self.offsetter_y = None
        self.shader_node = None
        self.report_content = []
        self.iterator = 0

    def handle_nodes(self,only_setup_nodes=False):
        propper.refresh_shader_links()
        selected = self.get_target_mats(bpy.context)

        self.report_content.clear()
        for mat in selected:
            self.clean_props()
            self.mat = mat
            self.process_materials(only_setup_nodes)

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


    def process_materials(self,only_setup_nodes=False):
        method = self.setup_nodes if only_setup_nodes else self.assign_imagess
        self.mat.use_nodes = True
        method()

    def clean_props(self):
        self.coord_node = None
        self.mapping_node = None
        self.displaced = None
        self.has_normal = None
        self.has_height = None
        self.add_extras = None
        self.add_curve = None
        self.add_ramp = None
        self.output_node = None
        self.new_image_node = None
        self.extra_node = None
        self.bump_map_node = None
        self.normal_map_node = None
        self.base_loc = None
        self.offsetter_x = -312
        self.offsetter_y = -312
        self.shader_node = None
        self.report_content.clear()
        self.iterator = 0

    def set_shader_node(self):
        shader_node = self.get_first_node()
        if self.node_invalid(shader_node) or props().replace_shader or props().clear_nodes:
            substitute_shader = props().shaders_list
            #handles custom shaders
            if substitute_shader in bpy.data.node_groups.keys():
                shader_node = self.nodes.new('ShaderNodeGroup')
                shader_node.node_tree = bpy.data.node_groups[substitute_shader]
            elif hasattr(bpy.types,substitute_shader) :
                shader_node = self.nodes.new(substitute_shader)
            else :
                node_links().clear()
                propper.set_nodes_groups()
                propper.refresh_shader_links()
                propper.guess_sockets()
                if substitute_shader in bpy.data.node_groups.keys():
                    shader_node = self.nodes.new('ShaderNodeGroup')
                    shader_node.node_tree = bpy.data.node_groups[substitute_shader]
                else:
                    print("Error during custom shaders gathering")
                    return
            shader_node.name = "NODE_" + shader_node.name
            self.links.new(shader_node.outputs[0], self.output_node.inputs[0])
        if not (self.node_invalid(shader_node) or props().clear_nodes):
            self.copy_bsdf_parameters(self.get_first_node(), shader_node)
            if props().replace_shader:
                self.nodes.remove(self.get_first_node())
        self.shader_node = shader_node

    def set_output_node(self):
        self.output_node = None
        out_nodes = [n for n in self.nodes if n.type == "OUTPUT_MATERIAL"]
        for node in out_nodes:
            if node.is_active_output:
                self.output_node = node
                break
        if not self.output_node :
            self.output_node = self.nodes.new("ShaderNodeOutputMaterial")

    def node_invalid(self,node):
        invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
        return (node.type in invalidtypes if node else True) or not self.output_node.inputs['Surface'].is_linked

    def get_first_node(self):
        sur_node = self.output_node.inputs['Surface']
        first_node = None
        if sur_node.is_linked:
            first_node = sur_node.links[0].from_node
        return first_node
    
    def create_coords_nodes(self):
        self.coord_node = self.nodes.new('ShaderNodeTexCoord')
        self.coord_node.label = f"{self.mat_name_cleaner()} Coordinates"
        self.coord_node.name = f"NODE_{self.coord_node.name}"

    def make_tex_mapping_nodes(self):
        mat_name = self.mat_name_cleaner()
        self.mapping_node = self.nodes.new('ShaderNodeMapping')
        self.mapping_node.label = f"{mat_name} Mapping"
        self.mapping_node.name = f"NODE_{self.mapping_node.name}"
        self.create_coords_nodes()
        self.links.new(self.coord_node.outputs['UV'], self.mapping_node.inputs['Vector'])

    def make_new_image_node(self,line):
        self.new_image_node = self.nodes.new(type="ShaderNodeTexImage")
        self.new_image_node.name = "NODE_" + Path(line.file_name).name
        self.new_image_node.label = line.name
        self.links.new(self.mapping_node.outputs[0], self.new_image_node.inputs['Vector'])

    def set_bools_params(self,line):
        socket = line.input_sockets
        self.displaced = ("displacement" in socket.lower())
        self.has_normal = ("normal" in line.name.lower())
        self.has_height = ("height" in line.name.lower())
        self.add_extras = props().tweak_levels and not (self.has_normal or self.has_height)
        skip_ramps = len([x for x in ["subsurface radius", "normal", "tangent"] if line.name.lower() in x]) > 0
        self.add_curve = ((("color" in socket.lower()) or ("emission" in socket.lower())) and not self.displaced)
        self.add_ramp = (not (("color" in socket.lower()) or ("emission" in socket.lower())) and (not skip_ramps)) or (self.displaced and self.has_height)

    def check_add_extras(self,line):
        if ( self.has_normal or self.displaced ) and not props().mode_opengl:
            directx_converter = self.make_rgb_green_inverted()
            directx_converter.name = f"NODE_directx_{line.name}"
            directx_converter.label = line.name
        
        self.extra_node = None
        if self.add_extras:
            if self.add_curve:
                curve_ramp = self.nodes.new('ShaderNodeRGBCurve')
                self.extra_node = curve_ramp
                self.links.new(self.new_image_node.outputs[0], curve_ramp.inputs[1])
            if self.add_ramp:
                ramp = self.nodes.new('ShaderNodeValToRGB')
                self.extra_node = ramp
                self.links.new(self.new_image_node.outputs[0], ramp.inputs[0])
            if self.add_ramp or self.add_curve:
                self.extra_node.label = f"{self.extra_node.name}"
                self.extra_node.name = f"NODE_{self.extra_node.name}"
            self.extra_node = extra_node

    def handle_disp_nodes_1(self,line):
        self.bump_map_node = self.nodes.new('ShaderNodeBump')
        self.bump_map_node.name = f"NODE_{self.bump_map_node.name}"
        self.links.new(self.new_image_node.outputs[0], self.bump_map_node.inputs[2])
        self.bump_map_node.inputs[0].default_value = .5
        if self.add_extras:
            self.links.new(self.extra_node.outputs[0], self.bump_map_node.inputs[2])

    def handle_disp_nodes_2(self,line):
        socket = line.input_sockets
        multi_sockets = line.channels.socket
        if self.has_normal and not props().skip_normals:
            if self.displaced:
                self.links.new(self.normal_map_node.outputs[0], self.output_node.inputs[2])
            else:
                self.links.new(self.normal_map_node.outputs[0], self.shader_node.inputs[socket])
        if self.has_height and not props().skip_normals:
            if self.displaced:
                self.links.new(self.bump_map_node.outputs[0], self.output_node.inputs[2])
            else:
                self.links.new(self.bump_map_node.outputs[0], self.shader_node.inputs[socket])
        if not (self.has_height or self.has_normal) or props().skip_normals:
            if self.add_extras:
                self.links.new(self.extra_node.outputs[0], self.shader_node.inputs[socket])
            elif line.split_rgb:
                separate_rgb = self.nodes.new(type="ShaderNodeSeparateColor")
                separate_rgb.location = self.shader_node.location
                separate_rgb.location.x -= 69
                self.links.new(self.new_image_node.outputs[0], separate_rgb.inputs[0])
                for i,sock in enumerate(line.channels.socket):
                    if '0' not in sock.input_sockets :
                        self.links.new(separate_rgb.outputs[i], self.shader_node.inputs[sock.input_sockets])
            else:
                self.links.new(self.new_image_node.outputs[0], self.shader_node.inputs[socket])

    def handle_disp_nodes_3(self):
        disp_map_node = self.nodes.new('ShaderNodeDisplacement')
        disp_map_node.name = f"NODE_{disp_map_node.name}"
        disp_map_node.location = (self.output_node.location[0] - 256, self.output_node.location[1])
        self.links.new(disp_map_node.outputs[0], self.output_node.inputs['Displacement'])
        if self.add_extras:
            self.links.new(self.extra_node.outputs[0], disp_map_node.inputs['Height'])
        if self.has_height and not props().skip_normals:
            pass
        if self.has_normal and not props().skip_normals:
            self.links.new(self.normal_map_node.outputs[0], disp_map_node.inputs['Normal'])
        if (not self.has_normal or props().skip_normals) and not self.add_extras:
            self.links.new(self.new_image_node.outputs[0], disp_map_node.inputs['Height'])

    def handle_disp_nodes_4(self):
        disp_vec_node = self.nodes.new('ShaderNodeVectorDisplacement')
        disp_vec_node.name = f"NODE_{disp_vec_node.name}"
        disp_vec_node.location = (self.output_node.location[0] - 256, self.output_node.location[1])
        self.links.new(disp_vec_node.outputs[0], self.output_node.inputs['Displacement'])
        if self.add_extras:
            self.links.new(self.extra_node.outputs[0], disp_vec_node.inputs['Vector'])
        if self.has_normal and not props().skip_normals:
            self.links.new(self.normal_map_node.outputs[0], disp_vec_node.inputs['Vector'])
        if (not self.has_normal or props().skip_normals) and not self.add_extras:
            self.links.new(self.new_image_node.outputs[0], disp_vec_node.inputs['Vector'])

    def handle_bumps(self,line):
        socket = line.input_sockets
        self.check_add_extras(line)
        self.new_image_node.location = (
                                  (self.base_loc.x + self.offsetter_x * (int(self.add_extras) + int(self.has_normal or self.has_height) + 1)),
                                  (self.base_loc.y + self.offsetter_y * self.iterator)
                                  )
        if self.has_normal and not props().skip_normals:
            self.normal_map_node = self.nodes.new('ShaderNodeNormalMap')
            self.normal_map_node.name = f"NODE_{self.normal_map_node.name}"
            self.links.new(self.new_image_node.outputs[0], self.normal_map_node.inputs[1])

        if self.has_height and not props().skip_normals:
            self.handle_disp_nodes_1(line)

        if socket != "0" and not self.displaced and not ('Disp Vector' in socket):
            self.handle_disp_nodes_2(line)

        if self.displaced:
            self.handle_disp_nodes_3(line)

        if ('Disp Vector' in socket):
            self.handle_disp_nodes_4(line)

        if self.add_extras:
            self.extra_node.location = (
                (self.base_loc.x + self.offsetter_x * (int(self.has_normal or self.has_height) + 1)), (self.base_loc.y + self.offsetter_y * self.iterator))
        if self.has_height and not props().skip_normals:
            self.bump_map_node.location = (self.base_loc.x + self.offsetter_x, self.base_loc.y + self.offsetter_y * self.iterator)
        if self.has_normal and not props().skip_normals:
            self.normal_map_node.location = (self.base_loc.x + self.offsetter_x, self.base_loc.y + self.offsetter_y * self.iterator)
        self.iterator += 1

    def arrange_last_nodes(self):
        nod = self.shader_node
        nod.location[1] = self.get_sockets_center() + 128
        nod.location[0] += 128
        self.output_node.location[1] = nod.location[1]
        map_names = [line.name for line in p_lines()]
        bumped = int(len([x for x in map_names if "height" in x.lower()]) + len([y for y in map_names if "normal" in y.lower()]) > 0)
        self.mapping_node.location = (self.base_loc.x + self.offsetter_x * (int(self.add_extras) + bumped + 2) + self.offsetter_x, self.base_loc.y)
        self.coord_node.location = (self.mapping_node.location[0] + self.offsetter_x, self.mapping_node.location[1])
        self.mapping_node.location[1] = self.map_links()
        self.coord_node.location[1] = self.mapping_node.location[1]

    def clean_stm_nodes(self):
        for node in reversed(self.nodes):
            if node.name.startswith("NODE_") and not node.bl_idname in props().shaders_list:
                self.nodes.remove(node)

    def copy_bsdf_parameters(self,source_node, target_node):
        if source_node.bl_idname == target_node.bl_idname :
            for input_source, input_target in zip(source_node.inputs, target_node.inputs):
                if hasattr(input_source, 'default_value'):
                    input_target.default_value = input_source.default_value

    def make_rgb_green_inverted(self):
        material = self.mat
        if material:
            material.use_nodes = True
            nodes = self.nodes
            rgb_curves_node = nodes.new(type="ShaderNodeRGBCurve")
            rgb_curves_node.location = (0, 0)
            green_curve = rgb_curves_node.mapping.curves[1]
            for i,point in enumerate(green_curve.points):
                point.location = (point.location.x, (1.0-point.location.y)*(1-i))
            return rgb_curves_node
        return None

    def setup_nodes(self):
        if props().clear_nodes:
            self.nodes.clear()
        self.offsetter_x=-312
        self.offsetter_y=-312
        self.clean_stm_nodes()
        self.set_output_node()
        self.set_shader_node()
        self.base_loc.x = self.output_node.location[0]
        self.base_loc.y = self.output_node.location[1]
        self.move_nodes()
        if len(p_lines()) == 0:
            return
        self.make_tex_mapping_nodes()
        self.iterator = 0
        for line in p_lines():
            if not line.manual:
                self.detect_a_map(line)
            self.set_bools_params(line)
            self.make_new_image_node(line)
            self.handle_bumps(line)
            self.report_content.append(f"Image texture node created in {self.mat.name} for {line.name} map ")
        self.arrange_last_nodes()

    def detect_relevant_maps(self):
        for line in p_lines():
            self.detect_a_map(line)

    def detect_a_map(self,line):
        mat_name = self.mat_name_cleaner()
        if mat_name:
            if not (props().advanced_mode and line.manual):
                line.file_name = self.find_file(line)
                propper.default_sockets(line)
            line.file_is_real = False
            if line.file_name != "" :
                line.file_is_real = Path(line.file_name).exists() and Path(line.file_name).is_file()

    def find_file(self,line):
        mat_name = self.mat_name_cleaner()
        if props().dir_content :
            dir_content = [v for (k,v) in json.loads(props().dir_content).items()]
            lower_dir_content = [v.lower() for v in dir_content]
            map_name = line.name
            for map_file in lower_dir_content:
                if mat_name.lower() in map_file and map_name.lower() in map_file:
                    return str(Path(props().usr_dir).joinpath(Path(dir_content[lower_dir_content.index(map_file)])))
        return ""

    def mat_name_cleaner(self):
        mat_name = self.mat.name
        print(f"mat_name is {mat_name}")
        if props().dup_mat_compatible:
            mat_name = mat_name.split(".0")[0]
        return mat_name

    def assign_imagess(self):
        mat_name = self.mat_name_cleaner()
        for line in p_lines():
            active_filepath = self.find_file(line)
            if not active_filepath != "" :
                self.report_content.append(f"No image found matching {line.name} for material: {self.mat.name} in folder {props().usr_dir}")
                return
            image_name = Path(active_filepath).name
            if not self.mat.node_tree.nodes.find(f"NODE_{image_name}") > 0:
                self.report_content.append(f"node {image_name} not found, run Setup Nodes before ")
                return
            if not Path(active_filepath).is_file():
                self.report_content.append(f"Texture {image_name} not found ")
                return
            file_path = Path(active_filepath).name
            image = bpy.data.images.load(filepath=active_filepath) if not image_name in bpy.data.images else bpy.data.images[image_name]
            nodes_to_fill = [nod for nod in self.mat.node_tree.nodes if self.strip_digits(nod.name).replace(" ", "").lower() in image_name.replace(" ", "").lower()]
            for node in nodes_to_fill:
                node.image = bpy.data.images[image.name]
                self.report_content.append(f"Texture file {image_name} assigned to {line.name} node in {self.mat.name} ")

                if image_name.lower() in ["normal", "nor", "norm", "normale", "normals"]:
                    node.image.colorspace_settings.name = 'Non-Color'

    def strip_digits(self,_text):
        if "NODE_" in _text :
            _text = _text.replace("NODE_", "")
        if _text[-3:].isdigit():
            _text = _text[:-4]
        return _text

    def map_links(self):
        locs_y = []
        connected = list(linked for linked in self.mapping_node.outputs[0].links if linked.is_valid)
        if len(connected) > 0:
            for linked in connected:
                locs_y.append(linked.to_node.location[1])
        else:
            for nod in self.nodes:
                locs_y.append(nod.location[1])
        locs_y.sort()
        center = (locs_y[0] + locs_y[-1]) / 2
        return center

    def move_nodes(self):
        self.shader_node.location = (self.base_loc.x,self.base_loc.y)
        replace = props().replace_shader
        imgs = [nod for nod in self.nodes if nod.type == 'TEX_IMAGE']
        not_empty = len(p_lines())
        new_cluster_height = 0
        if not_empty and replace:
            existing = [nod for nod in self.nodes if nod.type != "OUTPUT_MATERIAL" and not nod == self.shader_node]
            new_cluster_height = 888 * (not_empty / 2)
            if not not_empty > 0 and replace:
                new_cluster_height = 1024
            self.offsetter_y = new_cluster_height
            for node in existing:
                node.location = (node.location[0] - 512, node.location[1] + self.offsetter_y)

    def get_sockets_center(self):
        self.shader_node.location = (self.base_loc.x,self.base_loc.y)
        locs_y = []
        connected = list(linked for linked in self.shader_node.inputs if linked.is_linked)
        if len(connected) > 0:
            for linked in connected:
                locs_y.append(linked.links[0].from_node.location[1])
        else:
            for node in self.mat.node_tree.nodes:
                locs_y.append(node.location[1])
        locs_y.sort()
        center = (locs_y[0] + locs_y[-1]) / 2
        return center
    
