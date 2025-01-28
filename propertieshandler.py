import bpy
from pathlib import Path
import json


class PropertiesHandler():
    def get_shaders_list_eve(self,context):
        nodes_links = context.scene.node_links
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
        if context.scene.bsmprops.include_ngroups:
            for i in range(len(nodes_links)):
                item = nodes_links[i].nodetype
                shaders_list.append((item, item, ''), )
        shaders_list.reverse()
        return shaders_list

    def get_shaders_list(self,context):
        if bpy.context.scene.render.engine == 'BLENDER_EEVEE' :
            return self.get_shaders_list_eve(context)
        if bpy.context.scene.render.engine == 'CYCLES' :
            return self.get_shaders_list_cycles(context)

    def get_shaders_list_cycles(self,context):
        nodes_links = context.scene.node_links
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
        if context.scene.bsmprops.include_ngroups:
            for i in range(len(nodes_links)):
                item = nodes_links[i].nodetype
                shaders_list.append((item, item, ''), )
        shaders_list.reverse()
        return shaders_list

    def mat_name_cleaner(self,context):
            props = context.scene.bsmprops
            obj = context.view_layer.objects.active
            if obj :
                material = obj.active_material
                mat_name = material.name
                if props.dup_mat_compatible:
                    mat_name = next(iter(mat_name.split(".0")))
                return (material, mat_name)
            return None

    def set_nodes_groups(self,context):
        ng = bpy.data.node_groups
        nodes_links = context.scene.node_links
        nodes_links.clear()
        mat_tmp = bpy.data.materials.new(name="tmp_mat")
        mat_tmp.use_nodes = True
        for nd in ng:
            noder = mat_tmp.node_tree.nodes.new('ShaderNodeGroup')
            noder.node_tree = nd
            if conectable := len(noder.inputs) and len(noder.outputs):
                new_link = context.scene.node_links.add()
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

    def get_sockets_enum_items(self,context):
        scene = context.scene
        shaders_links = scene.shader_links
        nodes_links = scene.node_links
        bsmprops = scene.bsmprops
        selectedshader = scene.bsmprops.shaders_list
        rawdata = []
        for i in range(len(shaders_links)):
            if shaders_links[i].shadertype in selectedshader :
                rawdata = [v for (k,v) in json.loads(shaders_links[i].input_sockets).items()]
        for i in range(len(nodes_links)):
            if nodes_links[i].nodetype in selectedshader:
                rawdata = [v for (k,v) in json.loads(nodes_links[i].input_sockets).items()]
        if not bsmprops.replace_shader:  # and valid mat
            mat_used = self.mat_name_cleaner(context)[0]
            rawdata = self.get_shader_inputs(context,mat_used)
        return self.format_enum(context, rawdata)

    def default_sockets(self,context,line):
        bsmprops = context.scene.bsmprops
        sockets_list = []
        for sock in self.get_sockets_enum_items(context):
            match_1 = line.map_label.strip().replace(" ", "").lower() in sock[0].replace(" ", "").lower()
            match_2 = line.map_label.strip().replace(" ", "").lower() in ('').join(sock[0].split()).lower()
            if match_1 or match_2 :
                sockets_list.append(sock)
        if len(sockets_list):
            line.input_sockets = sockets_list[0][0]
        else:
            sockets_list = [sock[0].replace(" ", "").lower() for sock in self.get_sockets_enum_items(context)]
            print(f"socket not found for {line.name} in {sockets_list} ")

    def guess_sockets(self,context):
        props = context.scene.bsmprops
        lines = props.texture_importer.textures
        for line in lines:
            self.default_sockets(context,line)

    def fill_settings(self,context):
        args = {}
        props = context.scene.bsmprops
        args['internals'] = ['type','rna_type','dir_content','content','bl_rna','name','bsm_all','texture_importer']
        args['attributes'] = [attr for attr in dir(props) if attr not in args['internals'] and attr[:2] != "__"]
        args['line_names'] = []
        for attr in args['attributes']:
            if isinstance(getattr(props,attr),bool):
                args[attr] = f"{getattr(props,attr)}"
            else:
                args[attr] = getattr(props,attr)
        lines = props.texture_importer.textures
        for line in lines:
            args['line_names'].append(line.name)
            args[line.name] = {}
            args[line.name]['map_label'] = line.map_label
            args[line.name]['input_sockets'] = line.input_sockets
            args[line.name]['line_on'] = f"{line.line_on}"
            args[line.name]['file_name'] = line.file_name
            args[line.name]['manual'] = f"{line.manual}"
        return json.dumps(args)

    def detect_a_map(self,context,line):
        props = context.scene.bsmprops
        mat_name = self.mat_name_cleaner(context)
        if mat_name:
            args = {'line':line,'mat_name':mat_name[1]}
            if not (props.advanced_mode and line.manual):
                line.file_name = self.find_file(context,**args)
                #replace_shader_up refresh ?
                self.default_sockets(context,line)
            line.file_is_real = False
            if line.file_name != "" :
                #line.line_on = True
                line.file_is_real = Path(line.file_name).exists() and Path(line.file_name).is_file()

    def detect_relevant_maps(self,context):
        props = context.scene.bsmprops
        lines = props.texture_importer.textures
        for line in lines:
            self.detect_a_map(context,line)

    def clean_input_sockets(self,context):
        props = context.scene.bsmprops
        lines = props.texture_importer.textures
        for line in lines:
            line.input_sockets = '0'

    def get_shader_inputs(self,context,mat_used):
        if mat_used != None:
            for nd in mat_used.node_tree.nodes:
                validoutput = nd.type == "OUTPUT_MATERIAL" and nd.is_active_output and nd.inputs['Surface'].is_linked
                if validoutput:
                    shd = nd.inputs['Surface'].links[0].from_node
                    input_sockets = mat_used.node_tree.nodes[shd.name].inputs
                    if len(input_sockets) != 0:
                        return input_sockets.keys()
        return []

    def format_enum(self,context,rawdata):
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

    def find_file(self,context,**args):
        line = args['line']
        mat_name = args['mat_name']
        props = bpy.context.scene.bsmprops
        if props.dir_content :
            dir_content = [v for (k,v) in json.loads(props.dir_content).items()]
            lower_dir_content = [v.lower() for v in dir_content]
            map_name = line.map_label
            for map_file in lower_dir_content:
                if mat_name.lower() in map_file and map_name.lower() in map_file:
                    return str(Path(props.usr_dir).joinpath(Path(dir_content[lower_dir_content.index(map_file)])))
        return ""
