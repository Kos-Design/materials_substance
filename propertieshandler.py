import bpy
from pathlib import Path
import json

def props():
    return getattr(bpy.context.preferences.addons[__package__].preferences, "props", None)

def node_links():
    return getattr(bpy.context.preferences.addons[__package__].preferences, "node_links", None)

def shader_links():
    return getattr(bpy.context.preferences.addons[__package__].preferences, "shader_links", None)

def texture_importer():
    return getattr(bpy.context.preferences.addons[__package__].preferences, "maps", None)

def texture_index():
    return getattr(texture_importer(), "texture_index", None)

def lines():
    return getattr(texture_importer(), "textures", None)

def p_lines():
    return [line for line in lines() if line.line_on]

def line_index(line):
    for i,liner in enumerate(lines()) :
        if liner == line:
            return i
    return

def set_wish(self):
    print("wish set")
    self.wish = {line.name: (line['input_sockets'],[getattr(ch,'input_sockets') for ch in line.channels.socket]) for line in lines()}

def get_wish(self):
    for name, value in self.wish.items():
        try:
            print("wishing line")
            lines()[name]['input_sockets'] = value[0]
        except:
            print("reset line")
            lines()[name]['input_sockets'] = 0
        for i,ch in enumerate(lines()[name].channels.socket):
            try:
                print("wish ch")
                setattr(ch,'input_sockets',value[1][i])
            except:
                print("reset ch")
                setattr(ch,'input_sockets','no_socket')

def sockets_holder(func):
    def wrapper(self, *args, **kwargs):  # Ensure `self` is passed
        set_wish(self)
        print('whisher')
        result = func(self, *args, **kwargs)  # Call the original method
        get_wish(self)
        return result
    return wrapper

class MaterialHolder():
    def __init__(self):
        self.wish = {}
        self._mat = None
        self._tree = None
        self._nodes = None
        self._links = None

    @property
    def mat(self):
        if self._mat is None and bpy.context.object.active_material:
            try :
                self.mat = bpy.context.object.active_material
                return bpy.context.object.active_material
            except:
                pass
        return self._mat

    @mat.setter
    def mat(self, value):
        if value is None or isinstance(value, bpy.types.Material):
            self._mat = value
        else:
            raise ValueError("mat must be a bpy.types.Material or None")
        self._update_tree_and_nodes()

    @property
    def tree(self):
        return self._tree

    @tree.setter
    def tree(self, value):
        self._tree = value

    @property
    def nodes(self):
        if not self._nodes :
            self._nodes = self.mat.node_tree.nodes
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = value

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, value):
        self._links = value

    def _update_tree_and_nodes(self):
        if self._mat is not None:
            self._tree = getattr(self._mat, 'node_tree', None)
            self._nodes = getattr(self._tree, 'nodes', None)
            self._links = getattr(self._tree, 'links', None)
        else:
            self._tree = None
            self._nodes = None
            self._links = None

class PropertiesHandler(MaterialHolder):
    def __init__(self):
        super().__init__()

    def get_shaders_list_eve(self):
        shaders_list = [
            ('ShaderNodeVolumePrincipled', 'Principled Volume', ''),
            ('ShaderNodeVolumeScatter', 'Volume Scatter', ''),
            ('ShaderNodeVolumeAbsorption', 'Volume Absorption', ''),
            ('ShaderNodeEmission', 'Emission', ''),
            ('ShaderNodeBsdfDiffuse', 'Diffuse BSDF', ''),
            ('ShaderNodeBsdfGlass', 'Glass BSDF', ''),
            ('ShaderNodeBsdfGlossy', 'Glossy BSDF', ''),
            ('ShaderNodeBsdfRefraction', 'Refraction BSDF', ''),
            ('ShaderNodeSubsurfaceScattering', 'Subsurface Scattering BSSRDF', ''),
            ('ShaderNodeEeveeSpecular', 'Specular BSDF', ''),
            ('ShaderNodeBsdfTranslucent', 'Translucent BSDF', ''),
            ('ShaderNodeBsdfTransparent', 'Transparent BSDF', ''),
            ('ShaderNodeBsdfPrincipled', 'Principled BSDF', ''),
        ]
        if props().include_ngroups:
            for i in range(len(node_links())):
                item = node_links()[i].nodetype
                shaders_list.append((item, item, ''), )
        shaders_list.reverse()
        return shaders_list

    def get_shaders_list(self):
        if bpy.context.scene.render.engine == 'BLENDER_EEVEE_NEXT' :
            return self.get_shaders_list_eve()
        if bpy.context.scene.render.engine == 'CYCLES' :
            return self.get_shaders_list_cycles()

    def make_clean_channels(self,line):
        line.channels.socket.clear()
        for i in range(3):
            item = line.channels.socket.add()
            item.name = ['R','G','B'][i]

    def initialize_defaults(self):
        lines().clear()
        maps = ["Color","Roughness","Metallic","Normal"]
        for i in range(4):
            item = lines().add()
            item.name = f"{maps[i]}"
            self.make_clean_channels(item)
            self.default_sockets(item)

    @sockets_holder
    def safe_refresh(self,context=None):
        self.clean_input_sockets()
        self.refresh_shader_links()

    def get_shaders_list_cycles(self):
        shaders_list = [
            ('ShaderNodeBsdfHairPrincipled', 'Principled-Hair BSDF', ''),
            ('ShaderNodeVolumePrincipled', 'Principled Volume', ''),
            ('ShaderNodeVolumeScatter', 'Volume Scatter', ''),
            ('ShaderNodeVolumeAbsorption', 'Volume Absorption', ''),
            ('ShaderNodeEmission', 'Emission', ''),
            ('ShaderNodeBsdfDiffuse', 'Diffuse BSDF', ''),
            ('ShaderNodeBsdfGlass', 'Glass BSDF', ''),
            ('ShaderNodeBsdfGlossy', 'Glossy BSDF', ''),
            ('ShaderNodeBsdfRefraction', 'Refraction BSDF', ''),
            ('ShaderNodeSubsurfaceScattering', 'Subsurface Scattering BSSRDF', ''),
            ('ShaderNodeBsdfToon', 'Toon BSDF', ''),
            ('ShaderNodeBsdfTranslucent', 'Translucent BSDF', ''),
            ('ShaderNodeBsdfTransparent', 'Transparent BSDF', ''),
            ('ShaderNodeBsdfHair', 'Hair BSDF', ''),
            ('ShaderNodeBsdfSheen', 'Sheen BSDF', ''),
            ('ShaderNodeBsdfPrincipled', 'Principled BSDF', ''),
        ]
        if props().include_ngroups:
            for i in range(len(node_links())):
                item = node_links()[i].nodetype
                shaders_list.append((item, item, ''), )
        shaders_list.reverse()
        return shaders_list

    def set_nodes_groups(self):
        ng = bpy.data.node_groups
        node_links().clear()
        mat_tmp = bpy.data.materials.new(name="tmp_mat")
        mat_tmp.use_nodes = True
        for nd in ng:
            noder = mat_tmp.node_tree.nodes.new('ShaderNodeGroup')
            noder.node_tree = nd
            if conectable := len(noder.inputs) and len(noder.outputs):
                new_link = node_links().add()
                new_link.name = nd.name
                new_link.label = nd.name
                new_link.nodetype = nd.name
                for socket in [i for i in noder.outputs if conectable]:
                    validoutput = socket.type == "SHADER"
                    if validoutput:
                        new_link.outputsockets = socket.name
                        break
                socks = [str(socket.name) for socket in [n for n in noder.inputs if conectable] if socket.type != "SHADER"]
                if not len(socks):
                    new_link.input_sockets = "{'0':'0'}"
                else:
                    new_link.input_sockets = json.dumps((dict(zip(range(len(socks)), socks))))
        mat_tmp.node_tree.nodes.clear()
        bpy.data.materials.remove(mat_tmp)

    def load_props(self):
        args = json.loads(props().stm_all)
        line_names = args['line_names']
        mismatch = len(line_names) - len(lines())
        if mismatch:
            #instanciate channels in    add line funct
            self.adjust_lines_count(mismatch)
        for attr in args['attributes']:
            if isinstance(getattr(props(),attr),bool):
                setattr(props(), attr,'True' in args[attr])
            else:
                setattr(props(), attr,args[attr])
        self.refresh_inputs()
        for i,line in enumerate(lines()):
            line.name = line_names[i]
            try :
                line.input_sockets = args[line.name]['input_sockets']
            except (Exception,TypeError):
                pass
            line['line_on'] = 'True' in args[line.name]['line_on']
            line['file_name'] = args[line.name]['file_name']
            line['manual'] = 'True' in args[line.name]['manual']
            line['split_rgb'] = 'True' in args[line.name]['split_rgb']
            for i in range(3):
                line['channels']["RGB"[i]].input_sockets = args[line.name]['channels']["RGB"[i]]['input_sockets']
        bpy.context.view_layer.update()

    def adjust_lines_count(self,difference):
        method = self.del_panel_line if difference < 0 else self.add_panel_lines
        for i in range(abs(difference)):
            method()

    def del_panel_line(self):
        if 0 <= texture_index() < len(lines()):
            lines().remove(texture_index())
            texture_importer().texture_index = max(0, texture_index() - 1)

    def add_panel_lines(self):
        texture = lines().add()
        texture.name = self.get_available_name()
        texture_importer().texture_index = len(lines()) - 1
        self.make_clean_channels(texture)

    def get_available_name(self):
        new_index = 0
        new_name = "Custom map 1"
        while new_name in [item.name for item in lines()]:
            new_index += 1
            new_name = f"Custom map {new_index}"
        return new_name

    def refresh_shader_links(self):
        shader_links().clear()
        mat_tmp = bpy.data.materials.new(name="tmp_mat")
        mat_tmp.use_nodes = True
        for shader_enum in self.get_shaders_list_eve():
            node_type = str(shader_enum[0])
            if node_type is not None and node_type != '0' :
                if node_type in bpy.data.node_groups.keys():
                    new_node = mat_tmp.node_tree.nodes.new(type='ShaderNodeGroup')
                    new_node.node_tree = bpy.data.node_groups[str(shader_enum[1])]
                else:
                    new_node = mat_tmp.node_tree.nodes.new(type=node_type)
                new_shader_link = shader_links().add()
                new_shader_link.name = str(shader_enum[1])
                new_shader_link.shadertype = node_type
                new_shader_link.input_sockets = json.dumps((dict(zip(range(len(new_node.inputs)), [inputs for inputs in new_node.inputs.keys() if not inputs == 'Weight']))))
                new_shader_link.outputsockets = json.dumps((dict(zip(range(len(new_node.outputs)), [outputs.name for outputs in new_node.outputs]))))
        for shader_enum in self.get_shaders_list_cycles():
            node_type = str(shader_enum[0])
            if node_type is not None and node_type != '0' :
                if node_type in bpy.data.node_groups.keys():
                    new_node = mat_tmp.node_tree.nodes.new(type='ShaderNodeGroup')
                    new_node.node_tree = bpy.data.node_groups[str(shader_enum[1])]
                else:
                    new_node = mat_tmp.node_tree.nodes.new(type=node_type)
                new_shader_link = shader_links().add()
                new_shader_link.name = str(shader_enum[1])
                new_shader_link.shadertype = node_type
                new_shader_link.input_sockets = json.dumps((dict(zip(range(len(new_node.inputs)), [inputs for inputs in new_node.inputs.keys() if not inputs == 'Weight' ]))))
                new_shader_link.outputsockets = json.dumps((dict(zip(range(len(new_node.outputs)), [outputs.name for outputs in new_node.outputs]))))
        mat_tmp.node_tree.nodes.clear()
        bpy.data.materials.remove(mat_tmp)

    def refresh_inputs(self):
        self.clean_input_sockets()
        if props().include_ngroups:
            node_links().clear()
            self.set_nodes_groups()
        self.refresh_shader_links()

    def set_enum_sockets_items(self):
        if not self.mat :
            try:
                self.mat = bpy.context.object.active_material
            except:
                print("No material")
        rawdata = []
        #if not self.wish:
            #set_wish(self)
        if not props().replace_shader:
            #get_wish(self)
            print(f"got wish {self.wish}")
            print(lines()['Normal'].channels.socket['R'].input_sockets)
            rawdata = self.get_shader_inputs()
        else:
            selectedshader = props().shaders_list
            for i in range(len(shader_links())):
                if shader_links()[i].shadertype in selectedshader :
                    rawdata = [v for (k,v) in json.loads(shader_links()[i].input_sockets).items()]
            for i in range(len(node_links())):
                if node_links()[i].nodetype in selectedshader:
                    rawdata = [v for (k,v) in json.loads(node_links()[i].input_sockets).items()]
        if not rawdata:
            self.clean_input_sockets()
            rawdata = [v for (k,v) in json.loads(props().sockets).items()]
        else:
            rawdata.append('Ambient Occlusion')

        props().sockets = json.dumps((dict(zip(range(len(rawdata)), rawdata))))

    def get_sockets_enum_items(self):
        if not len(json.loads(props().sockets)):
            self.set_enum_sockets_items()
        return self.format_enum([v for (k,v) in json.loads(props().sockets).items()])

    def get_linked_node(self, _socket):
        if _socket and _socket.is_linked:
            return _socket.links[0].from_node
        return None

    def trace_shader_node(self, node):
        if not node:
            return None
        if node.type in {"MIX_SHADER", "ADD_SHADER"}:
            return self.trace_shader_node(self.get_linked_node(node.inputs[1])) or \
                   self.trace_shader_node(self.get_linked_node(node.inputs[2]))
        elif node.type == "SEPARATE_COLOR":
            return None
        return node

    def get_shader_node(self,origin):
        print(f"from:{origin}")
        shader_node = None
        output_node = self.get_output_node()
        if output_node :
            shader_node = self.trace_shader_node(self.get_linked_node(output_node.inputs["Surface"]))
        print(f"sha is {shader_node.name if shader_node else 'found squat'}")
        return shader_node

    def get_output_node(self):
        if not self.nodes:
            print("aborted no nodes")
            return None
        out_nodes = [n for n in self.nodes if n.type in "OUTPUT_MATERIAL"]
        for node in out_nodes:
            print(f"found {node.name}")
            if node.is_active_output:
                return node
        print("aborted no node returned")
        return None

    def check_special_keywords(self,term):
        if "," in term:
            return None
        #no spaces
        matcher = {"Ambient Occlusion":["ambientocclusion","ambientocclusion","ambient","occlusion","ao","ambocc","ambient_occlusion"],
                    "Displacement":["relief","displacement","displace","displace_map"],
                    "Disp Vect":["dispvect","dispvector","disp_vector","vector_disp","vectordisplacement","displacementvector", "displacement_vector", "vector_displacement"],
                    "Normal":["normal","normalmap","normalmap", "norm", "tangent"],
                    "bump":["bump","bumpmap","bump map", "height", "heightmap","weight","weight map"]
                    }
        for k,v in matcher.items():
            if self.find_in_sockets(term.strip(),v):
                return k
        return None

    def find_in_sockets(self,term,target_list=None):
        if term in "":
            return None
        if not target_list:
            target_list = [sock[0] for sock in self.get_sockets_enum_items()]
        for sock in target_list:
            match_1 = term.replace(" ", "").lower() in sock.replace(" ", "").lower()
            match_2 = term.replace(" ", "").lower() in ("").join(sock.split()).lower()
            if match_1 or match_2 :
                return sock
        return None

    def detect_multi_socket(self,line):
        splitted = line.name.split(',')
        if len(splitted) > 1 or line.split_rgb:
            if not (props().advanced_mode and line.split_rgb):
                props().advanced_mode = True
                line.split_rgb = True
            if len(splitted) != 3 :
                for i in range(3-len(splitted)):
                    splitted.append("no_socket")
            for i,_sock in enumerate(splitted):
                if i > 2:
                    return False
                sock = self.find_in_sockets(_sock)
                if not sock:
                    sock = self.check_special_keywords(_sock)
                    if not sock:
                        sock = [sock[0] for sock in self.get_sockets_enum_items()][0]
                    if sock in "bump" :
                        sock = 'Normal'
                if sock in [sock[0] for sock in self.get_sockets_enum_items()]:
                    line.channels.socket[i].input_sockets = sock
            return True
        return False

    def default_sockets(self,line):
        if not line.auto_mode or self.detect_multi_socket(line):
            return
        sock = self.find_in_sockets(line.name)
        if not sock:
            sock = self.check_special_keywords(line.name)
            if not sock:
                sock = [sock[0] for sock in self.get_sockets_enum_items()][0]
            if "bump" in sock:
                sock = 'Normal'
        if sock in [sock[0] for sock in self.get_sockets_enum_items()]:
            line.input_sockets = sock

    def guess_sockets(self):
        for line in p_lines():
            self.default_sockets(line)

    def fill_settings(self):
        args = {}
        args['internals'] = ['type','rna_type','dir_content','poll_props','custom_preset_enum','content','bl_rna','name','stm_all','texture_importer']
        args['attributes'] = [attr for attr in props().bl_rna.properties.keys() if attr not in args['internals'] and attr[:2] != "__"]
        args['line_names'] = []
        for attr in args['attributes']:
            if isinstance(getattr(props(),attr),bool):
                args[attr] = f"{getattr(props(),attr)}"
            else:
                args[attr] = getattr(props(),attr)
        for line in lines():
            args['line_names'].append(line.name)
            args[line.name] = {}
            args[line.name]['input_sockets'] = line.input_sockets
            args[line.name]['line_on'] = f"{line.line_on}"
            args[line.name]['file_name'] = line.file_name
            args[line.name]['manual'] = f"{line.manual}"
            args[line.name]['split_rgb'] = f"{line.split_rgb}"
            args[line.name]['channels'] = {}
            for i in range(3):
                args[line.name]['channels']["RGB"[i]] = {}
                try:
                    args[line.name]['channels']['RGB'[i]]['input_sockets'] = line['channels']['RGB'[i]].input_sockets
                except KeyError:
                    # no ['RGB'[i]].name on 284???
                    # no inputs sockets neither...
                    print(f"Error during preset {args[line.name]}{args[line.name]['channels']['RGB'[i]]}{args[line.name]['channels']['RGB'[i]].items()}")
        try:        #{line['channels']['RGB'[i]]}     {getattr(line['channels'],'RGB'[i])} {getattr(line['channels']['RGB'[i]],'input_sockets')}
            return json.dumps(args)
        except (TypeError, OverflowError) as e:
            print("An error occurred, Preset File is empty",e)
        return json.dumps({'0':''})

    def clean_input_sockets(self):
        #required to avoid warning errors
        for line in lines():
            line['input_sockets'] = 0
            #line.input_sockets = 'no_socket'
            for ch in line.channels.socket:
                ch['input_sockets'] = 0
                #ch.input_sockets = 'no_socket'

    def get_shader_inputs(self):
        shd = self.get_shader_node("get_shader_inputs")
        if shd and shd.inputs:
            return shd.inputs.keys()
        return None

    def read_preset(self):
        print(f'preset is {props().custom_preset_enum}')
        if not props().custom_preset_enum in '0':
            try:
                print(f"attempting to open {props().custom_preset_enum}")
                with open(f"{props().custom_preset_enum}", "r", encoding="utf-8") as w:
                    props().stm_all = w.read()
                    self.load_props()
                    return f"Applied preset: {Path(props().custom_preset_enum).stem}"
            except Exception as e:
                print(e)
                return f"Error {e}"
        return "Error"

    def format_enum(self,rawdata):
        default = ('no_socket', '-- Unmatched Socket --', '')
        if rawdata == []:
            return [default]
        dispitem = [('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', '')]
        items = [(item, item, '') for item in rawdata]
        items.extend(dispitem)
        items.reverse()
        items.append(default)
        items.reverse()
        return items
