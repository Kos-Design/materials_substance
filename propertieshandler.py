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

            leobject = context.view_layer.objects.active

            material = leobject.active_material
            lematname = material.name
            if (".0" in lematname) and bsmprops.fix_name:
                lematname = lematname[:-4]
            matline = (material, lematname)
            return matline

    def set_nodes_groups(self,context):
        ng = bpy.data.node_groups
        nodes_links = context.scene.node_links
        nodes_links.clear()
        for nodez in range(len(list(ng))):
            conectable = len(ng[nodez].inputs) > 0 and len(ng[nodez].outputs) > 0
            if conectable:
                newentry = context.scene.node_links.add()
                newentry.name = ng[nodez].name
                newentry.nodetype = ng[nodez].name

                outputz = (i for i in ng[nodez].outputs if conectable)
                for socket in outputz:
                    validoutput = socket.type == "SHADER"
                    if validoutput:
                        newentry.outputsockets = socket.name
                        break
                        # only the first shaderoutput will be considered

                inputz = (i for i in ng[nodez].inputs if conectable)
                inplist = []
                for socket in inputz:
                    validinput = socket.type != "SHADER"
                    if validinput:
                        inplist.append(socket.name)

                newentry.input_sockets = "@-¯\(°_o)/¯-@".join(str(x) for x in inplist)

    def clean_input_sockets(self,context):
        for i in range(10):
            panel_line = eval(f"context.scene.panel_line{i}")
            inputs = panel_line.input_sockets
            if not inputs.isalnum() :
                panel_line.input_sockets = '0'
        return

    def check_names(self,context):
        allpanel_rows = 10
        panel_lines = list(k for k in range(allpanel_rows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
        for ks in panel_lines:
            bpy.ops.bsm.name_checker(line_number=ks, called=False, lorigin="bsmprops")
        return

    def get_shader_inputs(self,context,mat_used):
        #lematerial = __self__.mat_name_cleaner(context)[0]
        if mat_used != None:
            for lesnodes in mat_used.node_tree.nodes:
                validoutput = lesnodes.type == "OUTPUT_MATERIAL" and lesnodes.is_active_output and lesnodes.inputs['Surface'].is_linked
                if validoutput:
                    currentshader = lesnodes.inputs['Surface'].links[0].from_node
                    inputz = mat_used.node_tree.nodes[currentshader.name].inputs
                    if len(inputz) != 0:
                        keyz = inputz.keys()
                        return keyz
        return []

    def format_enum(self,context,rawdata):
        dispitem = [('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', '')]
        default = ('0', '', '')
        items = []
        for item in rawdata:
            items.append((item, item, ''))
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

    def update_file_is_real(self, context):
        bsmprops = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(bsmprops.dir_content)
        lower_dir_content = bsmprops.dir_content.lower().split(";;;")
        context.file_is_real = False
        if context.probable.lower() in lower_dir_content or context.file_name.lower() in lower_dir_content :
            context.file_is_real = True
        #TODO: check that
        if not context.file_is_real :
            pass
            
    def set_all_ext(self):
        print("setting ext")
        for i in range(bpy.context.scene.bsmprops.panel_rows):
            panel_line = eval(f"bpy.context.scene.panel_line{i}")
            extension_detected = self.get_first_valid_ext()
            panel_line.extension = extension_detected
            panel_line.map_ext = extension_detected
    
    def get_first_valid_ext(self):
        dir_content = self.list_from_string(string=bpy.context.scene.bsmprops.dir_content)
        all_ext = self.get_extensions(None)
        extensions = [x[0] for x in all_ext]
        for files in dir_content :
            try :
                
                ext = Path(files).suffix
                if ext in extensions :
                    #print(f"found {ext}")
                    return ext
            except IOError:
                print(f"error with {files}")
                continue
    
        return ".exr"

    def find_file(self,context,**args):
        panel_line = args['line']
        #mat_name = self.mat_name_cleaner(context)[1]
        mat_name = args['mat_name']
        props = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(props.dir_content)
        lower_dir_content = props.dir_content.lower().split(";;;")
       
        map_name = panel_line.map_label

        args['ext'] = panel_line.map_ext

        for map_file in lower_dir_content:
            if mat_name.lower() in map_file and map_name.lower() in map_file:
                return str(Path(props.usr_dir).joinpath(Path(dir_content[lower_dir_content.index(map_file)])))
        return None
                   