import bpy
from pathlib import Path
import json

def props():
    return getattr(bpy.context.scene, "stm_props", None)

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

class MaterialHolder():
    def __init__(self):
        self._mat = None
        self._tree = None
        self._nodes = None
        self._links = None

    @property
    def mat(self):
        return self._mat

    @mat.setter
    def mat(self, value):
        if value is None or isinstance(value, bpy.types.Material):
            self._mat = value
            self._update_tree_and_nodes()
        else:
            raise ValueError("mat must be a bpy.types.Material or None")

    @property
    def tree(self):
        return self._tree

    @tree.setter
    def tree(self, value):
        self._tree = value

    @property
    def nodes(self):
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
            item.name = f"{maps[i]} map"
            item.name = f"{maps[i]}"
            self.make_clean_channels(item)
            self.default_sockets(item)

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
        make_clean_channels(texture)

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

    def get_sockets_enum_items(self):
        selectedshader = props().shaders_list
        rawdata = []
        for i in range(len(shader_links())):
            if shader_links()[i].shadertype in selectedshader :
                rawdata = [v for (k,v) in json.loads(shader_links()[i].input_sockets).items()]
        for i in range(len(node_links())):
            if node_links()[i].nodetype in selectedshader:
                rawdata = [v for (k,v) in json.loads(node_links()[i].input_sockets).items()]
        if not props().replace_shader:
            rawdata = self.get_shader_inputs(self.mat)
        return self.format_enum(rawdata)

    def default_sockets(self,line):
        if not props().match_sockets:
            return
        sockets_list = []
        for sock in self.get_sockets_enum_items():
            match_1 = line.name.strip().replace(" ", "").lower() in sock[0].replace(" ", "").lower()
            match_2 = line.name.strip().replace(" ", "").lower() in ('').join(sock[0].split()).lower()
            if match_1 or match_2 :
                sockets_list.append(sock)
        if not len(sockets_list):
            sockets_list = [sock[0].replace(" ", "").lower() for sock in self.get_sockets_enum_items()]
        line.input_sockets = sockets_list[0][0]

    def guess_sockets(self):
        if props().match_sockets:
            self.clean_input_sockets()
            for line in lines():
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
                    print(f"{args[line.name]}{args[line.name]['channels']['RGB'[i]]}{args[line.name]['channels']['RGB'[i]].items()}")
                    #no line['channels']...
                    print(f"{dir(line)}     ")
        try:        #{line['channels']['RGB'[i]]}     {getattr(line['channels'],'RGB'[i])} {getattr(line['channels']['RGB'[i]],'input_sockets')}
            return json.dumps(args)
        except (TypeError, OverflowError) as e:
            print("An error occurred, Preset File is empty",e)
        return json.dumps({'0':''})

    def clean_input_sockets(self):
        for line in lines():
            line.input_sockets = '0'

    def get_shader_inputs(self,mat_used):
        if mat_used != None:
            for nd in mat_used.node_tree.nodes:
                validoutput = nd.type == "OUTPUT_MATERIAL" and nd.is_active_output and nd.inputs['Surface'].is_linked
                if validoutput:
                    shd = nd.inputs['Surface'].links[0].from_node
                    input_sockets = mat_used.node_tree.nodes[shd.name].inputs
                    if len(input_sockets) != 0:
                        return input_sockets.keys()
        return []
    
    def read_preset(self):
        print(f'preset is {props().custom_preset_enum}')
        if not props().custom_preset_enum in '0':
            try:
                print(f"attempting to open {props().custom_preset_enum}")
                with open(f"{props().custom_preset_enum}", "r", encoding="utf-8") as w:
                    props().stm_all = w.read()
                    self.load_props()
                    print(f"loaded")
                    return f"Applied preset: {Path(props().custom_preset_enum).stem}"
            except Exception as e:
                print(e)
                return f"Error {e}"
        return "Error"

    def format_enum(self,rawdata):
        default = ('0', '-- Select Socket --', '')
        if rawdata == []:
            return [default]
        dispitem = [('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', '')]
        items = [(item, item, '') for item in rawdata]
        items.extend(dispitem)
        items.reverse()
        items.append(default)
        items.reverse()
        return items
