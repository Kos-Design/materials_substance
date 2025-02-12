import bpy
from pathlib import Path
from . propertieshandler import props, shader_links, node_links, PropertiesHandler,lines,p_lines,MaterialHolder,texture_importer,line_index
import json
import colorsys

propper = PropertiesHandler()

class NodeHandler(MaterialHolder):
    def __init__(self):
        super().__init__()
        self.coord_node = None
        self.mapping_node = None
        self.displaced = None
        self.has_normal = None
        self.has_height = None
        self.add_curve = None
        self.add_ramp = None
        self.output_node = None
        self.new_image_node = None
        self.extra_node = None
        self.bump_map_node = None
        self.normal_map_node = None
        self.base_loc = (300.0, 300.0)
        self.offsetter_x = None
        self.offsetter_y = None
        self.shader_node = None
        self.report_content = []
        self.ao_mix = None
        self.socket = 'no_socket'
        self.separate_rgb = None
        self.iterator = 0
        self.directx_converter = None
        self.has_ao = False

    def handle_nodes(self,only_setup_nodes=False):
        propper.refresh_shader_links()
        selected = self.get_target_mats(bpy.context)

        self.report_content.clear()
        for mat in selected:
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
        self.clean_props()
        method = self.setup_nodes if only_setup_nodes else self.assign_images
        self.mat.use_nodes = True
        method()

    def clean_props(self):
        self.coord_node = None
        self.mapping_node = None
        self.output_node = None
        self.base_loc = (300.0, 300.0)
        self.offsetter_x = -312
        self.offsetter_y = -312
        self.shader_node = None
        self.report_content.clear()
        self.iterator = 0

    def clean_line_params(self):
        self.displaced = None
        self.has_normal = None
        self.has_height = None
        self.add_curve = None
        self.add_ramp = None
        self.separate_rgb = None
        ao_nodes = [nod for nod in self.nodes if "NODES_Ambient_Occlusion_mixer" in nod.name]
        self.ao_mix = ao_nodes[0] if len(ao_nodes) else None
        self.socket = 'no_socket'
        self.new_image_node = None
        self.extra_node = None
        self.bump_map_node = None
        self.normal_map_node = None
        self.directx_converter = None
        self.disp_vec_node = None
        self.disp_map_node = None
        self.has_ao = False

    def set_shader_node(self):
        shader_node = self.get_first_node()
        if self.node_invalid(shader_node) or props().replace_shader or props().clear_nodes:
            if props().replace_shader or not shader_node:
                substitute_shader = props().shaders_list
            else:
                substitute_shader = shader_node.bl_idname
            if props().include_ngroups:
                #handles custom shaders
                if substitute_shader in bpy.data.node_groups.keys():
                    shader_node = self.nodes.new('ShaderNodeGroup')
                    shader_node.node_tree = bpy.data.node_groups[substitute_shader]
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
            if hasattr(bpy.types,substitute_shader) :
                shader_node = self.nodes.new(substitute_shader)
            shader_node.name = "NODE_" + shader_node.name
            self.links.new(shader_node.outputs[0], self.output_node.inputs[0])
        if not (self.node_invalid(shader_node) or props().clear_nodes):
            self.copy_bsdf_parameters(self.get_first_node(), shader_node)
            #if props().replace_shader:
            #    self.nodes.remove(self.get_first_node())
        self.shader_node = shader_node

    def get_first_node(self):
        sur_node = self.output_node.inputs['Surface']
        first_node = None
        if sur_node.is_linked:
            first_node = sur_node.links[0].from_node
        return first_node

    def set_output_node(self):
        self.output_node = None
        out_nodes = [n for n in list(self.nodes) if n.type in "OUTPUT_MATERIAL"]
        for node in list(self.nodes):
            if node.is_active_output:
                self.output_node = node
                break
        if not self.output_node :
            self.output_node = self.nodes.new("ShaderNodeOutputMaterial")
        self.output_node.location = self.base_loc
        self.base_loc = self.output_node.location

    def node_invalid(self,node):
        invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
        return (node.type in invalidtypes if node else True) or not self.output_node.inputs['Surface'].is_linked

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

    def check_split_rgb(self,line):
        if line.split_rgb:
            self.separate_rgb = self.nodes.new(type="ShaderNodeSeparateColor")
            self.separate_rgb.name=f"NODE_split_{line.name}"
            self.separate_rgb.label=f"split_{line.name}"

    def make_new_image_node(self,line):
        self.new_image_node = self.nodes.new(type="ShaderNodeTexImage")
        self.new_image_node.name = "NODE_" + Path(line.file_name).name
        self.new_image_node.label = line.name
        self.new_image_node.use_custom_color = True
        self.new_image_node.color = self.get_colors()[line_index(line)]
        self.links.new(self.mapping_node.outputs[0], self.new_image_node.inputs['Vector'])
        self.check_split_rgb(line)

    def set_bools_params(self,line):
        socket = line.input_sockets
        self.displaced = "Displacement" in [propper.check_special_keywords(w) for w in line.name.lower().strip().split(",") ]
        self.has_normal = "Normal" in [propper.check_special_keywords(w) for w in line.name.lower().strip().split(",") ]
        self.has_height = "bump" in [propper.check_special_keywords(w) for w in line.name.lower().strip().split(",") ]
        self.has_ao = "Ambient Occlusion" in [propper.check_special_keywords(w) for w in line.name.lower().strip().split(",") ]
        if props().tweak_levels:
            skip_ramps = len([x for x in ["subsurface radius", "normal","disp. vector", "tangent"] if line.name.lower() in x]) > 0
            self.add_curve = not self.has_height and "color" in socket.lower() or self.has_normal or "disp vector" in socket.lower() or "emission" in socket.lower() or line.split_rgb
            self.add_ramp = self.has_height or (not (("color" in socket.lower()) or ("emission" in socket.lower())) and (not skip_ramps) )

    def check_add_extras(self,line):
        self.extra_node = None
        if props().tweak_levels:
            if self.add_curve:
                self.extra_node = self.nodes.new('ShaderNodeRGBCurve')
                self.links.new(self.new_image_node.outputs[0], self.extra_node.inputs[1])
            elif self.add_ramp:
                ramp = self.nodes.new('ShaderNodeValToRGB')
                self.extra_node = ramp
                self.links.new(self.new_image_node.outputs[0], ramp.inputs[0])
            if self.extra_node:
                self.extra_node.label = f"{self.extra_node.name}"
                self.extra_node.name = f"NODE_{self.extra_node.name}"

    def check_bump_node(self,line):
        if not (self.has_height and not props().skip_normals):
            return
        self.bump_map_node = self.nodes.new('ShaderNodeBump')
        self.bump_map_node.name = f"NODE_{self.bump_map_node.name}"
        self.links.new(self.new_image_node.outputs[0], self.bump_map_node.inputs[2])
        self.bump_map_node.inputs[0].default_value = .5
        if props().tweak_levels:
            self.links.new(self.extra_node.outputs[0], self.bump_map_node.inputs[2])

    def check_ao_mix(self,line):
        if self.has_ao:
            self.prepare_ao(line)

    def check_shader_displacement(self,line):
        if not self.displaced or ('Disp Vector' in line.input_sockets) or ('Disp Vector' in [propper.check_special_keywords(w) for w in line.name.lower().strip().split(",") ]) :
            return
        self.disp_map_node = self.nodes.new('ShaderNodeDisplacement')
        self.disp_map_node.name = f"NODE_{self.disp_map_node.name}"
        self.links.new(self.disp_map_node.outputs[0], self.output_node.inputs['Displacement'])
        if props().tweak_levels:
            self.links.new(self.extra_node.outputs[0], self.disp_map_node.inputs['Height'])
        if self.has_height and not props().skip_normals:
            pass
        if self.has_normal and not props().skip_normals:
            self.links.new(self.normal_map_node.outputs[0], self.disp_map_node.inputs['Normal'])
        if (not self.has_normal or props().skip_normals) and not props().tweak_levels:
            self.links.new(self.new_image_node.outputs[0], self.disp_map_node.inputs['Height'])

    def check_vector_displacement(self,line):
        if not ('Disp Vector' in line.input_sockets):
            return
        self.disp_vec_node = self.nodes.new('ShaderNodeVectorDisplacement')
        self.disp_vec_node.name = f"NODE_{self.disp_vec_node.name}"
        self.links.new(self.disp_vec_node.outputs[0], self.output_node.inputs['Displacement'])
        if props().tweak_levels:
            if self.extra_node:
                self.links.new(self.extra_node.outputs[0], self.disp_vec_node.inputs['Vector'])
        if self.has_normal and not props().skip_normals:
            self.links.new(self.normal_map_node.outputs[0], self.disp_vec_node.inputs['Vector'])
        if (not self.has_normal or props().skip_normals) and not props().tweak_levels:
            self.links.new(self.new_image_node.outputs[0], self.disp_vec_node.inputs['Vector'])

    def prepare_ao(self,line):
        if not len([nod for nod in self.nodes if "NODES_Ambient_Occlusion_mixer" in nod.name]):
            self.ao_mix = self.nodes.new('ShaderNodeMixShader')
            self.ao_mix.name = "NODES_Ambient_Occlusion_mixer"
            self.ao_mix.label = f"AO converter {line.name}"
            self.links.new(self.ao_mix.outputs['Shader'], self.output_node.inputs['Surface'])
            self.links.new(self.shader_node.outputs[0], self.ao_mix.inputs[2])

    def check_normal_map_node(self,line):
        if self.has_normal and not props().skip_normals:
            self.normal_map_node = self.nodes.new('ShaderNodeNormalMap')
            self.normal_map_node.name = f"NODE_{self.normal_map_node.name}"

    def check_opengl_mode(self,line):
        if props().mode_opengl:
            return
        if self.has_normal or self.disp_vec_node :
            self.directx_converter = self.make_rgb_green_inverted()
            self.directx_converter.name = f"NODE_directx_{line.name}"
            self.directx_converter.label = line.name
        if self.directx_converter and self.extra_node:
            self.nodes.remove(self.extra_node)
            self.extra_node = None

    def handle_bumps(self,line):
        self.check_add_extras(line)
        self.check_normal_map_node(line)
        self.check_bump_node(line)
        self.check_ao_mix(line)
        self.check_vector_displacement(line)
        self.check_shader_displacement(line)
        self.check_opengl_mode(line)

    def plug_node(self,socket,val):
        if self.shader_node.inputs.get(val,''):
            self.links.new(socket, self.shader_node.inputs[val])

    def plug_multi(self,line):
        self.links.new(self.new_image_node.outputs[0], self.separate_rgb.inputs[0])
        for i,sock in enumerate(line.channels.socket):
            if self.shader_node.inputs.get(sock.input_sockets,''):
                self.plug_node(self.separate_rgb.outputs[i],sock.input_sockets)
            if self.has_height and 'Normal' in sock.input_sockets:
                if not props().skip_normals:
                    self.plug_node(self.bump_map_node.outputs[0],sock.input_sockets)
                    self.links.new(self.separate_rgb.outputs[i], self.bump_map_node.inputs[2])
                else:
                    self.plug_node(self.separate_rgb.outputs[i],sock.input_sockets)
            if self.has_ao and 'Ambient Occlusion' in sock.input_sockets:
                self.links.new(self.separate_rgb.outputs[i], self.ao_mix.inputs[0])
            if 'Displacement' in sock.input_sockets and self.disp_map_node:
                self.links.new(self.separate_rgb.outputs[i], self.disp_map_node.inputs[0])

        if self.add_curve:
            self.links.new(self.new_image_node.outputs[0], self.extra_node.inputs[1])
            self.links.new(self.extra_node.outputs[0], self.separate_rgb.inputs[0])

    def plug_nodes_links(self,line):
        # plug image
        # plug ramps
        # plug converter
        # plug shader
        # plug disp
        if line.split_rgb:
            self.plug_multi(line)
            return

        if self.has_height and not props().skip_normals:
            if self.displaced:
                self.links.new(self.bump_map_node.outputs[0], self.output_node.inputs[2])
            else:
                self.plug_node(self.bump_map_node.outputs[0],line.input_sockets)
        if not (self.has_height or self.has_normal) or props().skip_normals:
            if self.ao_mix:
                if line.name in self.ao_mix.label and "Ambient Occlusion" in line.input_sockets:
                    self.links.new(self.new_image_node.outputs[0], self.ao_mix.inputs[0])
            elif not self.disp_vec_node and not self.disp_map_node :
                self.plug_node(self.new_image_node.outputs[0],line.input_sockets)
        if not props().tweak_levels:
            if self.has_normal:
                if self.normal_map_node:
                    self.links.new(self.new_image_node.outputs[0], self.normal_map_node.inputs[1])
                    self.plug_node(self.normal_map_node.outputs[0],line.input_sockets)
                if props().skip_normals:
                    if self.normal_map_node:
                        self.nodes.remove(self.normal_map_node)
                        self.normal_map_node = None
                    if not props().mode_opengl and not self.disp_vec_node and not self.ao_mix:
                        self.plug_node(self.directx_converter.outputs[0],line.input_sockets)
            if self.displaced and not props().skip_normals and self.normal_map_node:
                self.links.new(self.normal_map_node.outputs[0], self.output_node.inputs[2])
        else:
            if not self.directx_converter:
                if self.normal_map_node:
                    self.links.new(self.new_image_node.outputs[0], self.normal_map_node.inputs[1])
            if self.has_height:
                if self.bump_map_node:
                    self.links.new(self.extra_node.outputs[0], self.bump_map_node.inputs[2])
                    self.plug_node(self.bump_map_node.outputs[0],line.input_sockets)

        if props().tweak_levels and self.extra_node and not self.has_height and not self.normal_map_node and not self.disp_map_node and not self.disp_vec_node and not self.ao_mix:
            self.plug_node(self.extra_node.outputs[0],line.input_sockets)
        if props().tweak_levels and self.extra_node and self.normal_map_node :
            self.plug_node(self.normal_map_node.outputs[0],line.input_sockets)
            self.links.new(self.extra_node.outputs[0], self.normal_map_node.inputs[1])
        if props().tweak_levels and self.extra_node and self.disp_vec_node :
            self.links.new(self.extra_node.outputs[0], self.disp_vec_node.inputs[0])
        if props().tweak_levels and self.extra_node and self.ao_mix:
            self.links.new(self.extra_node.outputs[0], self.ao_mix.inputs[0])
        if not props().mode_opengl and self.directx_converter:
            self.links.new(self.new_image_node.outputs[0], self.directx_converter.inputs[0])
            if self.normal_map_node :
                self.links.new(self.directx_converter.outputs[0], self.normal_map_node.inputs[1])
                self.plug_node(self.normal_map_node.outputs[0],line.input_sockets)
            else :
                self.plug_node(self.directx_converter.outputs[0],line.input_sockets)
        if self.directx_converter and self.disp_vec_node :
            self.links.new(self.directx_converter.outputs[0], self.disp_vec_node.inputs[0])
            self.links.new(self.new_image_node.outputs[0], self.directx_converter.inputs[0])

    def clean_stm_nodes(self):
        for node in reversed(self.nodes):
            if node.name.startswith("NODE_") and not node.bl_idname in props().shaders_list:
                self.nodes.remove(node)

    def copy_bsdf_parameters(self,source_node, target_node):
        if source_node.bl_idname == target_node.bl_idname :
            for input_source, input_target in zip(source_node.inputs, target_node.inputs):
                if hasattr(input_source, 'default_value'):
                    input_target.default_value = input_source.default_value
        else:
            print(f"cant copy {source_node.name} to {target_node.name}")

    def make_rgb_green_inverted(self):
        material = self.mat
        if material:
            material.use_nodes = True
            nodes = self.nodes
            rgb_curves_node = nodes.new(type="ShaderNodeRGBCurve")
            green_curve = rgb_curves_node.mapping.curves[1]
            for i,point in enumerate(green_curve.points):
                point.location = (point.location.x, (1.0-point.location.y)*(1-i))
            return rgb_curves_node
        return None

    def setup_nodes(self):
        self.offsetter_x=-312
        self.offsetter_y=-312
        self.clean_stm_nodes()
        self.set_output_node()
        self.set_shader_node()
        if len(p_lines()) == 0:
            return
        keep_nodes = [self.output_node,self.shader_node]
        if props().clear_nodes:
            for nodes in [nd for nd in self.nodes if nd not in keep_nodes]:
                self.nodes.remove(nodes)
        self.make_tex_mapping_nodes()
        for line in p_lines():
            self.clean_line_params()
            if not line.manual:
                self.detect_a_map(line)
            self.set_bools_params(line)
            self.make_new_image_node(line)
            self.handle_bumps(line)
            self.plug_nodes_links(line)
            self.iterator += 1
            self.report_content.append(f"Image texture node created in {self.mat.name} for {line.name} map ")
        self.move_nodes()

    def detect_relevant_maps(self):
        for line in p_lines():
            self.detect_a_map(line)

    def detect_a_map(self,line):
        mat_name = self.mat_name_cleaner()
        if mat_name:
            line.file_name = self.find_file(line)
            propper.default_sockets(line)
            line.file_is_real = False
            if line.file_name != "" :
                line.file_is_real = Path(line.file_name).exists() and Path(line.file_name).is_file()

    def find_file(self,line):
        if line.manual:
            return line.file_name
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
        if props().dup_mat_compatible:
            mat_name = mat_name.split(".0")[0]
        return mat_name

    def assign_images(self):
        mat_name = self.mat_name_cleaner()
        for line in p_lines():
            line.file_name = self.find_file(line)
            if not line.file_name:
                self.report_content.append(f"No image found matching {line.name} for material: {self.mat.name} in folder {Path(props().usr_dir).name if props().usr_dir else 'SELECT MAPS FOLDER !'}")
                continue
            image_name = Path(line.file_name).name
            node_images = self.nodes.find(f"NODE_{image_name}")
            if not node_images:
                self.report_content.append(f"node {image_name} not found, run Setup Nodes before ")
                continue
            if not Path(line.file_name).is_file():
                self.report_content.append(f"Texture {image_name} not found ")
                continue
            nodes = [node for node in self.nodes if node.label and node.label in line.name]
            if len(nodes) and nodes[0]:
                image = bpy.data.images.load(filepath=line.file_name) if not image_name in bpy.data.images else bpy.data.images[image_name]
                if not line.name.replace(" ","").lower() in ["color", "basecolor", "emit", "emission", "albedo"]:
                    image.colorspace_settings.name = 'Non-Color'
                    print (f"{line.name.replace(' ','').lower()} not in color ? {line.name.replace(' ','').lower() in 'color'}")
                nodes[0].image = bpy.data.images[image.name]
                self.report_content.append(f"Texture file {image_name} assigned to {line.name} node in {self.mat.name} ")

    def strip_digits(self,_text):
        if "NODE_" in _text :
            _text = _text.replace("NODE_", "")
        if _text[-3:].isdigit():
            _text = _text[:-4]
        return _text

    def move_nodes(self):
        imgs = [nod for nod in self.nodes if nod.type == 'TEX_IMAGE']
        node_set = set([nod.bl_idname for nod in self.nodes])
        aos = [nod for nod in self.nodes if nod.bl_idname in ["ShaderNodeMixShader","ShaderNodeDisplacement","ShaderNodeVectorDisplacement"]]
        bumps = [nod for nod in self.nodes if nod.bl_idname in "ShaderNodeBump"]
        ramps = [nod for nod in self.nodes if nod.bl_idname in "ShaderNodeValToRGB"]
        norm = [nod for nod in self.nodes if nod.bl_idname in "ShaderNodeNormalMap"]
        curves = [nod for nod in self.nodes if nod.bl_idname in "ShaderNodeRGBCurve"]
        splitters = [nod for nod in self.nodes if nod.bl_idname in "ShaderNodeSeparateColor"]
        not_empty = len(p_lines())
        new_cluster_height = 0
        delta = -self.shader_node.width
        spacer = -50
        delta = -self.shader_node.width + spacer
        cols = 0.0
        ao = 0
        node_set = set([nod.bl_idname for nod in self.nodes])
        if len(aos):
            ao = 1
        if len(ramps) or len(curves):
            cols += 1
        if len(bumps) or len(norm):
            cols += 0.5
        if len(splitters):
            cols += 0.5
        self.mapping_node.location.x = self.output_node.location.x + delta*(cols+3) + delta*ao -1.5*spacer
        self.mapping_node.location.y += 250
        self.coord_node.location.x = self.output_node.location.x + delta*(cols+3) + delta*ao +2*spacer
        self.coord_node.location.y += 250
        self.shader_node.location.x = self.output_node.location.x + delta*(1+ao) - 0.5*spacer - 1.5*spacer*ao
        self.shader_node.location.y += 250
        remaining_nodes = [nod for nod in self.nodes if not nod in [self.output_node,self.shader_node,self.coord_node,self.mapping_node]]
        for nod in remaining_nodes:
            nod.location.y += 250
            nod.location = self.shader_node.location
            if nod.bl_idname in ["ShaderNodeMixShader","ShaderNodeDisplacement","ShaderNodeVectorDisplacement"]:
                nod.location.x += -delta/2 - 3*spacer
            if nod.bl_idname in ["ShaderNodeNormalMap","ShaderNodeBump"]:
                nod.location.x += delta - 2.25*spacer
            if nod.bl_idname in "ShaderNodeSeparateColor":
                nod.location.x += delta*(cols) - 6*spacer*int(bool(len(ramps) or len(curves))) + cols*spacer -0.75*spacer*int(bool(len(bumps) or len(norm)))
                nod.location.x += spacer*int(1-bool(len(ramps) or len(curves)))
            if nod.bl_idname in ["ShaderNodeRGBCurve","ShaderNodeValToRGB"]:
                nod.location.x += delta*(max(1,cols))+spacer
            if nod.bl_idname in "ShaderNodeTexImage" :
                nod.location.x += (delta)*(cols+1) +spacer

        for i,nod in enumerate(imgs):
            nod.location.y += (len(imgs)*150)/2 -50
            nod.location.y += i*-300
        for i,nod in enumerate(bumps+norm):
            nod.location.y += 100 -(nod.height + 150) + i*-250
        for i,nod in enumerate(aos):
            nod.location.y += (len(aos)*150)/2
            nod.location.y += i*-250
        for i,nod in enumerate(splitters):
            nod.location.y += ((len(splitters))*150)/2
            nod.location.y += i*-(nod.height + 150)
        for i,nod in enumerate(curves):
            nod.location.y += ((len(curves) + len(ramps))*150)/2
            nod.location.y += i*-(nod.height + 250)
        for i,nod in enumerate(ramps):
            nod.location.y += -(nod.height + 250)*len(curves) + ((len(curves) + len(ramps))*150)/2
            nod.location.y += i*-(nod.height + 150)

    def get_colors(self):
        return [(0.8,0.353,0.352),(0.8,0.541,0.282),(0.702,0.639,0.247),(0.361,0.600,0.361),(0.318,0.624,0.8),
                        (0.553,0.349,0.855),(0.776,0.451,0.722),(0.6,0.312,0.422),(0.5,0.5,0.5)]

