import bpy
from pathlib import Path
import itertools

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
    
    def set_file_name(self,context,**params):
        panel_line = params['line']
        file_name = self.find_file(context,**{'line':panel_line, 'mat_name':params['mat_active'].name})
        if file_name is not None :
            panel_line.file_name = panel_line.probable = file_name

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
                input_sockets = (i for i in ng[nd].inputs if conectable)
                new_link.input_sockets = ";;;".join(str(socket.name) for socket in input_sockets if socket.type != "SHADER")
    
    def get_sockets_enum_items(self,context):
        scene = context.scene
        shaders_links = scene.shader_links
        nodes_links = scene.node_links
        bsmprops = scene.bsmprops
        selectedshader = scene.bsmprops.shaders_list
        rawdata = []
        for i in range(len(shaders_links)):
            if selectedshader in shaders_links[i].shadertype:
                rawdata = shaders_links[i].input_sockets.split(";;;")
        for i in range(len(nodes_links)):
            if selectedshader in nodes_links[i].nodetype:
                rawdata = nodes_links[i].input_sockets.split(";;;")
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

    def detect_relevant_maps(self,context):
        props = context.scene.bsmprops
        for i in range(props.panel_rows):
            panel_line = eval(f"bpy.context.scene.panel_line{i}")
            args = {'line':panel_line,'mat_name':self.mat_name_cleaner(context)[1]}
            map_found = self.find_file(context,**args)
            if map_found is not None:
                panel_line.line_on = True
                panel_line.file_is_real = True

    def clean_input_sockets(self,context):
        for i in range(context.scene.bsmprops.panel_rows):
            input_sockets = eval(f"context.scene.panel_line{i}.input_sockets")
            #inputs = panel_line.input_sockets
            #if not inputs.isalnum() :
            input_sockets = '0'     
        return

    def check_names(self,context):
        panel_lines = [k for k in range(context.scene.bsmprops.panel_rows) if not eval(f"bpy.context.scene.panel_line{k}.manual")]
        for ks in panel_lines:
            bpy.ops.bsm.name_checker(line_number=ks, called=False, lorigin="bsmprops")
        return

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
        dispitem = [('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', '')]
        default = ('0', '', '')
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
    
    def list_from_string(self,string="",sep=";;;"):
        return string.split(sep)

    def file_tester(self, context):
    
        panel_line = context
        bsmprops = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(bsmprops.dir_content)
        if panel_line.file_name in dir_content:
            return True
        return False
            
    def find_file(self,context,**args):
        panel_line = args['line']
        mat_name = args['mat_name']
        props = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(props.dir_content)
        lower_dir_content = props.dir_content.lower().split(";;;")
        map_name = panel_line.map_label
        
        for map_file in lower_dir_content:
            if mat_name.lower() in map_file and map_name.lower() in map_file:
                return str(Path(props.usr_dir).joinpath(Path(dir_content[lower_dir_content.index(map_file)])))
        return None
                   