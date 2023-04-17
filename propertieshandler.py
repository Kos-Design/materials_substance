import bpy
from pathlib import Path
import json

class PropertiesHandler():

    def get_shaders_list(self,context):
        nodes_links = context.scene.node_links

        shaders_list = [

            ('ShaderNodeBsdfAnisotropic', 'Anisotropic BSDF', ''),
            ('ShaderNodeBsdfDiffuse', 'Diffuse BSDF', ''),
            ('ShaderNodeBsdfGlass', 'Glass BSDF', ''),
            ('ShaderNodeBsdfGlossy', 'Glossy BSDF', ''),
            ('ShaderNodeBsdfRefraction', 'Refraction BSDF', ''),
            ('ShaderNodeSubsurfaceScattering', 'Subsurface Scattering BSSRDF', ''),
            ('ShaderNodeBsdfToon', 'Toon BSDF', ''),
            ('ShaderNodeBsdfTranslucent', 'Translucent BSDF', ''),
            ('ShaderNodeBsdfTransparent', 'Transparent BSDF', ''),
            ('ShaderNodeBsdfVelvet', 'Velvet BSDF', ''),
            ('ShaderNodeBsdfPrincipled', 'Principled BSDF', ''),
        ]
        if context.scene.bsmprops.include_ngroups:
            for i in range(len(nodes_links)):
                item = nodes_links[i].nodetype
                shaders_list.append((item, item, ''), )
        shaders_list.reverse()
        return shaders_list
    
    def mat_name_cleaner(self,context):
            bsmprops = context.scene.bsmprops
            obj = context.view_layer.objects.active
            material = obj.active_material
            mat_name = material.name
            return (material, mat_name)

    def set_nodes_groups(self,context):
        ng = bpy.data.node_groups
        nodes_links = context.scene.node_links
        nodes_links.clear()
        for nd in range(len(list(ng))):
            if conectable := len(ng[nd].inputs) > 0 and len(ng[nd].outputs) > 0:
                new_link = context.scene.node_links.add()
                new_link.name = ng[nd].name
                new_link.nodetype = ng[nd].name
                for socket in [i for i in ng[nd].outputs if conectable]:
                    validoutput = socket.type == "SHADER"
                    if validoutput:
                        new_link.outputsockets = socket.name
                        break    
                socks = [str(socket.name) for socket in [n for n in ng[nd].inputs if conectable] if socket.type != "SHADER"]
                if len(socks) == 0:
                    new_link.input_sockets = '{"0":"0"}'
                else:
                    new_link.input_sockets = json.dumps((dict(zip(range(len(socks)), socks))))
                
    def get_sockets_enum_items(self,context):
        scene = context.scene
        shaders_links = scene.shader_links
        nodes_links = scene.node_links
        bsmprops = scene.bsmprops
        selectedshader = scene.bsmprops.shaders_list
        rawdata = []
        for i in range(len(shaders_links)):
            if selectedshader in shaders_links[i].shadertype:
                rawdata = [v for (k,v) in json.loads(shaders_links[i].input_sockets).items()]
        for i in range(len(nodes_links)):
            if selectedshader in nodes_links[i].nodetype:
                rawdata = [v for (k,v) in json.loads(nodes_links[i].input_sockets).items()]
        if not bsmprops.replace_shader:  # and valid mat
            mat_used = self.mat_name_cleaner(context)[0]
            rawdata = self.get_shader_inputs(context,mat_used) 
        return self.format_enum(context, rawdata)
    
    def default_sockets(self,context,panel_line):
        bsmprops = context.scene.bsmprops
        sockets_list = self.get_sockets_enum_items(context)
        for socket in sockets_list:
            if socket[0].replace(" ", "").lower() in panel_line.map_label.replace(" ", "").lower():
                panel_line.input_sockets = socket[0]
                break
    
    def guess_sockets(self,context):
        props = context.scene.bsmprops
        for i in range(props.panel_rows):
            panel_line = eval(f"bpy.context.scene.panel_line{i}")
            self.default_sockets(context,panel_line) 
    
    def detect_a_map(self,context,i):
        props = context.scene.bsmprops
        panel_line = eval(f"bpy.context.scene.panel_line{i}")
        args = {'line':panel_line,'mat_name':self.mat_name_cleaner(context)[1]}
        panel_line.file_name = self.find_file(context,**args)
        panel_line.file_is_real = False
        if panel_line.file_name != "" :
            panel_line.line_on = True
            panel_line.file_is_real = Path(panel_line.file_name).is_file()
    
    def detect_relevant_maps(self,context):
        props = context.scene.bsmprops
        for i in range(props.panel_rows):
            self.detect_a_map(context,i)

    def clean_input_sockets(self,context):
        for i in range(context.scene.bsmprops.panel_rows):
            panel_line = eval(f"context.scene.panel_line{i}")
            panel_line.input_sockets = '0'     

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
        default = ('0', '', '')
        if rawdata == []:
            return [default]
        dispitem = [('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', '')]
        items = [(item, item, '') for item in rawdata]    
        items.extend(dispitem)
        items.reverse()
        items.append(default)
        items.reverse()
        return items

    def get_extensions(self,context):
        filetypes = [
            ('.exr', 'EXR', ''),
            ('.bmp', 'BMP', ''),
            ('.png', 'PNG', ''),
            ('.jpg', 'JPEG', ''),
            ('.tga', 'TARGA', ''),
            ('.dpx', 'DPX', ''),
            ('.hdr', 'HDR', ''),
            ('.tif', 'TIFF', ''),
            ('.avi', 'AVI', ''),
            ('.mp4', 'MP4', ''),
            # ('', 'FFMPEG', ''),
            # ('', 'IRIS', ''),
            # ('.tga_raw', 'TARGA_RAW', ''),
            # ('.cineon', 'CINEON', ''),
            # ('', 'JPEG2000', ''),
        ]
        return filetypes
    
    def find_file(self,context,**args):
        panel_line = args['line']
        mat_name = args['mat_name']
        props = bpy.context.scene.bsmprops
        dir_content = [v for (k,v) in json.loads(props.dir_content).items()]
        lower_dir_content = [v.lower() for v in dir_content]
        map_name = panel_line.map_label
        for map_file in lower_dir_content:
            if mat_name.lower() in map_file and map_name.lower() in map_file:
                return str(Path(props.usr_dir).joinpath(Path(dir_content[lower_dir_content.index(map_file)])))
        return ""
                   