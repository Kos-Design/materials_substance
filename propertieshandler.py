import bpy
from pathlib import Path

from bpy.utils import (register_class,
                       unregister_class
                       )

class PropertiesHandler():

    def populate(self, context):

        nodes_links = context.scene.node_links

        lashaderlist = [

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
                lashaderlist.append((item, item, ''), )

        lashaderlist.reverse()

        return lashaderlist
    
    def mat_cleaner(self, context):
            bsmprops = context.scene.bsmprops

            leobject = context.view_layer.objects.active

            material = leobject.active_material
            lematname = material.name
            if (".0" in lematname) and bsmprops.fixname:
                lematname = lematname[:-4]
            matline = (material, lematname)
            return matline

    def findnodegroups(self, context):
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

                newentry.inputsockets = "@-¯\(°_o)/¯-@".join(str(x) for x in inplist)

    def cleaninputsockets(self,context):
        for i in range(10):
            panel_line = eval(f"context.scene.panel_line{i}")
            inputs = panel_line.inputsockets
            if not inputs.isalnum() :
                panel_line.inputsockets = '0'
        return

    def checknamefrombsmprops(self, context):
        allpanel_rows = 10
        panel_lines = list(k for k in range(allpanel_rows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
        for ks in panel_lines:
            bpy.ops.bsm.checkmaps(linen=ks, called=False, lorigin="bsmprops")
        return

    def assumenamefrombsmprops(self, context):
        allpanel_rows = 10
        panel_lines = list(k for k in range(allpanel_rows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
        for ks in panel_lines:
            bpy.ops.bsm.assumename(line_num=ks)

        return

    def currentshaderinputs(self, context,mat_used):
        #lematerial = __self__.mat_cleaner(context)[0]
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

    def arrangeinputlist(self, context, rawdata):
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

    def givelist(self, context):
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
    
    def other_positions(self, context, lefile):
        lematname = self.mat_cleaner(context)[1]

        separator = context.scene.bsmprops.separator
        extractargs = str(Path(lefile).stem).split(separator)
        position = None
        otherpositions = list(range(2))
        if lematname in extractargs:
            position = extractargs.index(lematname)
            otherpositions = list(p for p in list(range(3)) if p != position)
        result = [otherpositions, position]
        return result

    def interpretpattern(self, context, **inter_params):
        elements = inter_params['elements']
        bsmprops = context.scene.bsmprops
        pat = bsmprops.patterns
        prefix_pos = inter_params['px_pos']
        maplabel_pos = inter_params['mp_pos']
        mat_pos = inter_params['mt_pos']

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

    def poolprefix(self, context, lefile):
        folder = str(Path(lefile).parent)

        basename = Path(lefile).name

        bsmprops = context.scene.bsmprops
        separator = bsmprops.separator
        dir_content = [x.name for x in Path(folder).glob('*') ]
        print("scanning dir")
        reference = str(Path(lefile).stem).split(separator)
        refpositions = self.other_positions(context, lefile)[0]
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
                    if Path(files).is_file():
                        extractargs = str(Path(files).stem).split(separator)
                        positions = self.other_positions(context, files)[0]
                        if len(extractargs) > 1:

                            if str(prefix) == str(extractargs[positions[0]]):
                                prefixis1.append(1)
                            if prefix == str(extractargs[positions[1]]):
                                prefixis2.append(1)

                poolprefixis1 = (len(prefixis1) / len(dir_content)) * 100
                poolprefixis2 = (len(prefixis2) / len(dir_content)) * 100
                pos = positions[0]
                rate = poolprefixis1
                if poolprefixis1 < poolprefixis2:
                    rate = poolprefixis2
                    pos = positions[1]

                if rate > 50:
                    bsmprops.prefix = leprefix
                    break
                else:
                    leprefix = "DefaultPrefix"

        result = [leprefix, pos, rate]
        return result

    def reversepattern(self, context, lefile):
        scene = context.scene
        bsmprops = scene.bsmprops
        separator = bsmprops.separator
        lefolder = str(Path(lefile).parent)
        lematname = str(self.mat_cleaner(context)[1])
        basename = Path(lefile).name
        extractargs = str(Path(lefile).stem).split(separator)
        ext_tryout = str(Path(lefile).suffix).lower()
        filetypesraw = self.givelist(context)
        filetypes = []
        containsmatname = lematname in extractargs
        poolpe = self.poolprefix(context, lefile)

        if len(poolpe) > 0 :
            poolpe = list(poolpe)
        else:
            return 0    

        for i in range(len(filetypesraw)):
            filetypes.append(filetypesraw[i][0])

        patternof3detected = len(extractargs) == 3
        patternof2detected = len(extractargs) == 2
        patternof1detected = len(extractargs) == 1

        if ext_tryout in filetypes:

            self.mapext = ext_tryout
            if patternof3detected and containsmatname:

                if poolpe[2] > 50:
                    positions = self.other_positions(context, lefile)
                    mat_pos = positions[1]
                    prefix_pos = poolpe[1]
                    bsmprops.prefix = poolpe[0]
                    remainingpos = positions[0]
                    remainingpos.remove(poolpe[1])
                    maplabels_pos = remainingpos[0]
                    self.maplabels = extractargs[maplabels_pos]
                    params = {'px_pos':prefix_pos, 'mp_pos':maplabels_pos, 'mt_pos':mat_pos, 'elements':3}
                    self.interpretpattern(context, **params)

            if patternof2detected:
                remaining = extractargs[:]
                if containsmatname:
                    mat_pos = extractargs.index(lematname)
                    remaining.remove(lematname)
                    self.maplabels = remaining[0]
                    maplabels_pos = extractargs.index(self.maplabels)
                    params = {'px_pos':None, 'mp_pos':maplabels_pos, 'mt_pos':mat_pos, 'elements':2}
                    self.interpretpattern(context, **params)
                else:
                    if poolpe[0] in remaining :
                        remaining.remove(poolpe[0])
                    self.maplabels = remaining[0]
                    maplabels_pos = extractargs.index(self.maplabels)
                    params = {'px_pos':poolpe[1], 'mp_pos':maplabels_pos, 'mt_pos':None, 'elements':2}
                    self.interpretpattern(context, **params)
            if patternof1detected:
                self.maplabel = extractargs[0]
                params = {'px_pos':None, 'mp_pos':0, 'mt_pos':None, 'elements':1}

                self.interpretpattern(context, **params)
        # TODO check if no deathloop
        if bsmprops.usr_dir in str(Path.home()):
            # if default set as the first tex folder met
            bsmprops.usr_dir = lefolder
        rate = poolpe[2]
        return rate
    
    def patterns_list(self, context, params):
        Prefix = params[0]
        mapname = params[1]
        separator = context.scene.bsmprops.separator
        Extension = params[2]
        matname = params[3]

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

