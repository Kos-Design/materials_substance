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
        if context.scene.bsmprops.custom_shader_on:
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

    def make_names(self,context):
        if len(context.scene.shader_links) == 0:
            bpy.ops.bsm.make_nodetree()
        allpanel_rows = 10
        panel_lines = list(k for k in range(allpanel_rows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
        for ks in panel_lines:
            bpy.ops.bsm.name_maker(line_num=ks)

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
    
    def positions_order(self,context,active_file):
        lematname = self.mat_name_cleaner(context)[1]

        separator = context.scene.bsmprops.separator
        extractargs = str(Path(active_file).stem).split(separator)
        position = None
        otherpositions = list(range(2))
        if lematname in extractargs:
            position = extractargs.index(lematname)
            otherpositions = list(p for p in list(range(3)) if p != position)
        result = [otherpositions, position]
        return result

    def set_patterns(self,context,**params):
        elements = params['elements']
        bsmprops = context.scene.bsmprops
        pat = bsmprops.patterns
        prefix_pos = params['px_pos']
        maplabel_pos = params['mp_pos']
        mat_pos = params['mt_pos']

        if elements == 3:

            if prefix_pos == 0 and maplabel_pos == 1 and mat_pos == 2:
                pat = 10
            if prefix_pos == 0 and maplabel_pos == 2 and mat_pos == 1:
                pat = 9
            if prefix_pos == 1 and maplabel_pos == 2 and mat_pos == 0:
                pat = 6
            if prefix_pos == 1 and maplabel_pos == 0 and mat_pos == 2:
                pat = 8
            if prefix_pos == 2 and maplabel_pos == 0 and mat_pos == 1:
                pat = 7
            if prefix_pos == 2 and maplabel_pos == 1 and mat_pos == 0:
                pat = 5

        if elements == 2:
            if maplabel_pos == 1 and mat_pos == 0:
                pat = 1
            if maplabel_pos == 0 and mat_pos == 1:
                pat = 3
            if maplabel_pos == 1 and prefix_pos == 0:
                pat = 0
            if maplabel_pos == 0 and prefix_pos == 1:
                pat = 2
        if elements == 1:
            pat = 4
        bsmprops.patterns = str(pat)

        return

    def guess_prefix(self,context,active_file):
        folder = str(Path(active_file).parent)

        basename = Path(active_file).name

        bsmprops = context.scene.bsmprops
        separator = bsmprops.separator
        dir_content = [x.name for x in Path(folder).glob('*.*') ]
        print("scanning dir")
        reference = str(Path(active_file).stem).split(separator)
        refpositions = self.positions_order(context, active_file)[0]
        positions = refpositions
        prefixis1 = []
        prefixis2 = []
        leprefix = None
        pos = None
        rate = 0
        if len(reference) > 1:

            prefixes = [reference[(refpositions[0])], reference[(refpositions[1])]]
            for prefix in prefixes:

                leprefix = prefix

                for files in dir_content:
                    try:
                        if Path(files).is_file():
                            extractargs = str(Path(files).stem).split(separator)
                            positions = self.positions_order(context, files)[0]
                            if len(extractargs) > 1:

                                if str(prefix) == str(extractargs[positions[0]]):
                                    prefixis1.append(1)
                                if prefix == str(extractargs[positions[1]]):
                                    prefixis2.append(1)
                    except IOError:
                        continue
                guess_is_1 = (len(prefixis1) / len(dir_content)) * 100
                guess_is_2 = (len(prefixis2) / len(dir_content)) * 100
                pos = positions[0]
                rate = guess_is_1
                if guess_is_1 < guess_is_2:
                    rate = guess_is_2
                    pos = positions[1]

                if rate > 50:
                    bsmprops.prefix = leprefix
                    break
                else:
                    leprefix = "DefaultPrefix"

        result = [leprefix, pos, rate]
        return result

    def pattern_weight(self,context,active_file):
        scene = context.scene
        bsmprops = scene.bsmprops
        separator = bsmprops.separator
        lefolder = str(Path(active_file).parent)
        lematname = str(self.mat_name_cleaner(context)[1])
        basename = Path(active_file).name
        extractargs = str(Path(active_file).stem).split(separator)
        ext_tryout = str(Path(active_file).suffix).lower()
        filetypesraw = self.get_extensions(context)
        filetypes = []
        containsmatname = lematname in extractargs
        guessed = self.guess_prefix(context, active_file)

        if len(guessed) > 0 :
            guessed = list(guessed)
        else:
            return 0    

        for i in range(len(filetypesraw)):
            filetypes.append(filetypesraw[i][0])

        patternof3detected = len(extractargs) == 3
        patternof2detected = len(extractargs) == 2
        patternof1detected = len(extractargs) == 1

        if ext_tryout in filetypes:

            self.map_ext = ext_tryout
            if patternof3detected and containsmatname:
                
                if guessed[2] > 50:
                    positions = self.positions_order(context, active_file)
                    mat_pos = positions[1]
                    prefix_pos = guessed[1]
                    bsmprops.prefix = guessed[0]
                    remainingpos = positions[0]
                    remainingpos.remove(guessed[1])
                    map_label_pos = remainingpos[0]
                    self.map_label = extractargs[map_label_pos]
                    params = {'px_pos':prefix_pos, 'mp_pos':map_label_pos, 'mt_pos':mat_pos, 'elements':3}
                    self.set_patterns(context, **params)

            if patternof2detected:
                remaining = extractargs[:]
                if containsmatname:
                    mat_pos = extractargs.index(lematname)
                    remaining.remove(lematname)
                    self.map_label = remaining[0]
                    map_label_pos = extractargs.index(self.map_label)
                    params = {'px_pos':None, 'mp_pos':map_label_pos, 'mt_pos':mat_pos, 'elements':2}
                    self.set_patterns(context, **params)
                else:
                    if guessed[0] in remaining :
                        remaining.remove(guessed[0])
                    self.map_label = remaining[0]
                    map_label_pos = extractargs.index(self.map_label)
                    params = {'px_pos':guessed[1], 'mp_pos':map_label_pos, 'mt_pos':None, 'elements':2}
                    self.set_patterns(context, **params)
            if patternof1detected:
                self.maplabel = extractargs[0]
                params = {'px_pos':None, 'mp_pos':0, 'mt_pos':None, 'elements':1}

                self.set_patterns(context, **params)
        # TODO check if no deathloop
        if bsmprops.usr_dir in str(Path.home()):
            # if default set as the first tex folder met
            bsmprops.usr_dir = lefolder
        rate = guessed[2]
        return rate
    
    def list_from_string(self,string="",sep=";;;"):
        return string.split(sep)

    def get_patterns(self):
        fake_params = {'prefix':"Prefix",'map_name':"MapName",'ext':".ext",'mat_name':"Material"}
        return self.get_variations(None,**fake_params)

    def get_variations(self,context,**params):
        Prefix = params['prefix']
        mapname = params['map_name']
        separator = bpy.context.scene.bsmprops.separator
        Extension = params['ext']
        matname = params['mat_name']

        items = [
            ('0', Prefix + separator + mapname + Extension, ''),
            ('1', matname + separator + mapname + Extension, ''),
            ('2', mapname + separator + Prefix + Extension, ''),
            ('3', mapname + separator + matname + Extension, ''),
            ('4', mapname + Extension,
             '(Consider using Advanced Mode and Enable Manual to select the File name directly)'),
            ('5', matname + separator + mapname + separator + Prefix + Extension, ''),
            ('6', matname + separator + Prefix + separator + mapname + Extension, ''),
            ('7', mapname + separator + matname + separator + Prefix + Extension, ''),
            ('8', mapname + separator + Prefix + separator + matname + Extension, ''),
            ('9', Prefix + separator + matname + separator + mapname + Extension, ''),
            ('10', Prefix + separator + mapname + separator + matname + Extension, ''),

            # Add your own patterns following this format
        ]
        return items

    def file_in_dir(self,context):
        props = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(props.dir_content)
        lower_dir_content = props.dir_content.lower().split(";;;")
        #get material
        args = {'prefix':props.prefix, 'map_name':context.map_label, 'mat_name':"material", 'ext':context.map_ext}
        
        for i in range(len(self.get_patterns())):
            if self.get_variations(context,**args)[i][1].lower() in lower_dir_content :
                return True
        return False

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
        if not context.file_is_real :
            pass
            
    def guess_prefix_light(self,context):
        print("guessing prefix")
        dir_content = self.list_from_string(string=bpy.context.scene.bsmprops.dir_content)
        sep = bpy.context.scene.bsmprops.separator
        for files in dir_content:
            
            try:
                first = str(Path(files).stem).split(sep)
                bpy.context.scene.bsmprops.prefix = first[0]       
            except IOError:
                continue

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

    def compare_lower(self,context):
        #unused
        props = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(props.dir_content)
        lower_dir_content = props.dir_content.lower().split(";;;")
        #get material
        args = {'prefix':props.prefix, 'map_name':context.map_label, 'mat_name':"material", 'ext':context.map_ext}
        
        for i in range(len(self.get_patterns())):
            if self.get_variations(context,**args)[i][1].lower() in lower_dir_content :
                idx = lower_dir_content.index(self.get_variations(context,**args)[i][1].lower())
                #print(f"{i} for {self.get_variations(context,**args)[i][1]}")
                context.file_name = context.probable = str(Path(props.usr_dir).joinpath(Path(dir_content[idx])))
                #print(context.file_name)
                break

    def find_file(self,context,**args):
        props = bpy.context.scene.bsmprops
        dir_content = self.list_from_string(props.dir_content)
        lower_dir_content = props.dir_content.lower().split(";;;")
        for i in range(len(self.get_patterns())):
            if self.get_variations(context,**args)[i][1].lower() in lower_dir_content :
                idx = lower_dir_content.index(self.get_variations(context,**args)[i][1].lower())
                #print(f"{i} for {self.get_variations(context,**args)[i][1]}")
                return str(Path(props.usr_dir).joinpath(Path(dir_content[idx])))
                         