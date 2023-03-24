import bpy
import os

from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty, FloatVectorProperty,
    EnumProperty,
)

from bpy.types import (PropertyGroup, UIList,
                       WindowManager, Scene,
                       )
from bpy.utils import (register_class,
                       unregister_class
                       )

class BsmInit():
    def exec(self, context):

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
        if context.scene.bsmprops.customshader:
            for i in range(len(nodes_links)):
                item = nodes_links[i].nodetype
                lashaderlist.append((item, item, ''), )

        lashaderlist.reverse()

        return lashaderlist


def checknamefrombsmprops(self, context):
    allpanelrows = 10
    panel_lines = list(k for k in range(allpanelrows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
    for ks in panel_lines:
        bpy.ops.bsm.checkmaps(linen=ks, called=False, lorigin="bsmprops")
    return


def bsm_init_cb(self, context):
    lashaderlist = BsmInit.exec(self, context)
    return lashaderlist


def appendecustomshaders(self, context):
    if context.scene.bsmprops.customshader:
        CustomNodeGroups.findnodegroups(self, context)
    else:
        context.scene.node_links.clear()
    cleaninputsockets(self,context)
    return


class CustomNodeGroups():
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


class ShaderLinks(PropertyGroup):
    # shaders_links
    ID: IntProperty(
        name="ID",
        default=0
    )
    name: StringProperty(
        name="named",
        default="Unknown name"
    )
    shadertype: StringProperty(
        name="internal name",
        default="Unknownrawdata"
    )
    inputsockets: StringProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        default="Unknownrawdata"
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default="Unknownrawdata"
    )
    hasoutputs: BoolProperty(
        name="hasoutputs",
        default=False
    )
    hasinputs: BoolProperty(
        name="hasoutputs",
        default=False
    )
    hasnormal: BoolProperty(
        name="hasoutputs",
        default=False
    )


class NodesLinks(PropertyGroup):
    # nodes_links
    ID: IntProperty(
        name="ID",
        default=0
    )
    name: StringProperty(
        name="named",
        default="Unknown name"
    )
    nodetype: StringProperty(
        name="internal name",
        default="Unknownrawdata"
    )
    inputsockets: StringProperty(
        name="list of input sockets",
        default="Unknownrawdata"
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default="Unknownrawdata"
    )
    hasoutputs: BoolProperty(
        name="hasoutputs",
        default=False
    )
    hasinputs: BoolProperty(
        name="hasoutputs",
        default=False
    )
    isnormal: BoolProperty(
        name="hasoutputs",
        default=False
    )


def assumenamefrombsmprops(self, context):
    allpanelrows = 10
    panel_lines = list(k for k in range(allpanelrows) if not eval(f"bpy.context.scene.panel_line{k}.manual"))
    for ks in panel_lines:
        bpy.ops.bsm.assumename(line_num=ks)

    return

def currentshaderinputs(self, context):
    lematerial = MatnameCleaner.clean(self,context)[0]
    if lematerial != None:
        for lesnodes in lematerial.node_tree.nodes:
            validoutput = lesnodes.type == "OUTPUT_MATERIAL" and lesnodes.is_active_output and lesnodes.inputs['Surface'].is_linked
            if validoutput:
                currentshader = lesnodes.inputs['Surface'].links[0].from_node
                inputz = lematerial.node_tree.nodes[currentshader.name].inputs
                if len(inputz) != 0:
                    keyz = inputz.keys()
                    return keyz
                # else
                #     return default

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

def poutputsokets_cb(self, context):
    # callback for the enumlist of the dynamic enums
    scene = context.scene
    shaders_links = scene.shader_links
    nodes_links = scene.node_links
    bsmprops = scene.bsmprops
    selectedshader = scene.bsmprops.shaderlist
    items = []
    rawdata = []

    for i in range(len(shaders_links)):
        if selectedshader in shaders_links[i].shadertype:
            rawdata = shaders_links[i].inputsockets.split("@-¯\(°_o)/¯-@")

    for i in range(len(nodes_links)):
        if selectedshader in nodes_links[i].nodetype:
            rawdata = nodes_links[i].inputsockets.split("@-¯\(°_o)/¯-@")

    if not bsmprops.shader:  # and valid mat
        rawdata = currentshaderinputs(self, context)

    items = arrangeinputlist(self, context, rawdata)
    # if len(items)
    return items


def poutputsokets_up(self, context):
    # update for the enumlist
    scene = context.scene
    state = self.inputsockets
    if state.isalnum == '' :
        self.inputsockets = '0'
    disped = ['Displacement', 'Disp Vector']

    zid = self.ID
    if state != '0':
        same = (i for i in range(10) if state == eval(f"bpy.context.scene.panel_line{i}").inputsockets and i != zid)
        # if same in another slot then clear
        for i in same:
            panel_line = eval(f"scene.panel_line{i}")
            panel_line.inputsockets = '0'
        if state in disped:
            disped = list(j for j in range(10) if (str(eval(f"bpy.context.scene.panel_line{j}").inputsockets) in disped))

            # if already a kind of Disp in list then clear
            for j in disped:

                if j != zid:
                    panel_line = eval(f"scene.panel_line{j}")
                    panel_line.inputsockets = '0'
 
    return


def maptester(self, context):
    if not self.manual:
        bpy.ops.bsm.assumename(line_num=self.ID)
        bpy.ops.bsm.guessfilext(linen=self.ID, keepat=True, called=True)
    return


class MatnameCleaner():
    def clean(self, context):
        bsmprops = context.scene.bsmprops

        leobject = context.view_layer.objects.active

        material = leobject.active_material
        lematname = material.name
        if (".0" in lematname) and bsmprops.fixname:
            lematname = lematname[:-4]
        matline = (material, lematname)
        return matline


def labelbools_up(self, context):
    scene = context.scene
    bsmprops = scene.bsmprops
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()

    bsmprops.manison = manison_cb(bsmprops, context)
    if not self.manual:
        bpy.ops.bsm.assumename(line_num=self.ID)
        bpy.ops.bsm.checkmaps(linen=self.ID, lorigin="labelbools_up", called=False)
    return


class extlist():
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


def applytoall_up(self, context):
    target = "selected objects"

    if self.expert:
        target = "active object"
    if self.applyall:
        target = "all visible objects"
        self.onlyactiveobj = False


    bpy.types.BSM_OT_subimport.bl_description = "Setup nodes and load textures maps on " + target
    bpy.types.BSM_OT_createnodes.bl_description = "Setup Nodes on " + target
    bpy.types.BSM_OT_assignnodes.bl_description = "Load textures maps on " + target
    liste = [
        bpy.types.BSM_OT_subimport,
        bpy.types.BSM_OT_createnodes,
        bpy.types.BSM_OT_assignnodes
    ]
    for cls in liste:
        laclasse = cls
        unregister_class(cls)
        register_class(laclasse)

    return


def otherpositions(self, context, lefile):
    lematname = MatnameCleaner.clean(self, context)[1]

    separator = context.scene.bsmprops.separator
    extractargs = os.path.basename(lefile)[:-4].split(separator)
    position = None
    otherpositions = list(range(2))
    if lematname in extractargs:
        position = extractargs.index(lematname)
        otherpositions = list(p for p in list(range(3)) if p != position)
    result = [otherpositions, position]
    return result


def interpretpattern(self, context, inter_params):
    elements = inter_params[3]
    bsmprops = context.scene.bsmprops
    pat = bsmprops.patterns
    prefix_pos = inter_params[0]
    maplabel_pos = inter_params[1]
    mat_pos = inter_params[2]

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
    folder = os.path.dirname(lefile)

    basename = os.path.basename(lefile)

    bsmprops = context.scene.bsmprops
    separator = bsmprops.separator
    dircontent = os.listdir(folder)
    reference = basename[:-4].split(separator)
    refpositions = otherpositions(self, context, lefile)[0]
    prefixis1 = []
    prefixis2 = []
    leprefix = None
    pos = None
    rate = 0
    if len(reference) > 1:

        prefixes = [reference[(refpositions[0])], reference[(refpositions[1])]]
        for prefix in prefixes:

            leprefix = prefix

            for files in dircontent:
                extractargs = files[:-4].split(separator)
                positions = otherpositions(self, context, files)[0]
                if len(extractargs) > 1:

                    if prefix == extractargs[(positions[0])]:
                        prefixis1.append(1)
                    if prefix == extractargs[(positions[1])]:
                        prefixis2.append(1)

            poolprefixis1 = (len(prefixis1) / len(dircontent)) * 100
            poolprefixis2 = (len(prefixis2) / len(dircontent)) * 100
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
    lefolder = os.path.dirname(lefile) + os.path.sep
    lematname = MatnameCleaner.clean(self, context)[1]
    basename = os.path.basename(lefile)
    extractargs = list(basename[:-4].split(separator))
    ext_tryout = basename[-4:].lower()
    filetypesraw = extlist.givelist(self, context)
    filetypes = []
    containsmatname = lematname in extractargs
    poolpe = list(poolprefix(self, context, lefile))

    for i in range(len(filetypesraw)):
        filetypes.append(filetypesraw[i][0])
    patternof3detected = len(extractargs) == 3
    patternof2detected = len(extractargs) == 2
    patternof1detected = len(extractargs) == 1

    if ext_tryout in filetypes:

        self.mapext = ext_tryout
        if patternof3detected and containsmatname:

            if poolpe[2] > 50:
                positions = otherpositions(self, context, lefile)
                mat_pos = positions[1]
                prefix_pos = poolpe[1]
                bsmprops.prefix = poolpe[0]
                remainingpos = positions[0]
                remainingpos.remove(poolpe[1])
                maplabels_pos = remainingpos[0]
                self.maplabels = extractargs[maplabels_pos]
                inter_params = [prefix_pos, maplabels_pos, mat_pos, 3]
                interpretpattern(self, context, inter_params)

        if patternof2detected:
            remaining = extractargs[:]
            if containsmatname:
                mat_pos = extractargs.index(lematname)
                remaining.remove(lematname)
                self.maplabels = remaining[0]
                maplabels_pos = extractargs.index(self.maplabels)
                inter_params = [None, maplabels_pos, mat_pos, 2]
                interpretpattern(self, context, inter_params)
            else:
                remaining.remove(poolpe[0])
                self.maplabels = remaining[0]
                maplabels_pos = extractargs.index(self.maplabels)
                inter_params = [poolpe[1], maplabels_pos, None, 2]
                interpretpattern(self, context, inter_params)
        if patternof1detected:
            self.maplabel = extractargs[0]
            inter_params = [None, 0, None, 1]
            interpretpattern(self, context, inter_params)
    # TODO check if no deathloop
    if bsmprops.usr_dir == os.path.expanduser('~'):
        # if default set as the first tex folder met
        bsmprops.usr_dir = lefolder
    rate = poolpe[2]
    return rate


def file_update(self, context):
    if self.manual:
        reversepattern(self, context, self.lefilename)
    if os.path.isfile(self.lefilename):
        self.probable = self.lefilename

    isindir_updater(self, context)
    return


def mapext_cb(self, context):
    filetypes = extlist.givelist(self, context)

    return filetypes


def mapext_up(self, context):
    if not self.manual:
        bpy.ops.bsm.assumename(line_num=self.ID)
    return


def shaderlist_cb(self, context):
    lashaderlist = bsm_init_cb(self, context)

    return lashaderlist


def shaderlist_up(self, context):
    scene = context.scene
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    cleaninputsockets(self,context)
    return


def manual_up(self, context):
    bsmprops = context.scene.bsmprops
    if not self.manual:
        bpy.ops.bsm.assumename(line_num=self.ID)
    bsmprops.manison = manison_cb(bsmprops, context)

    return

def expert_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    if not self.expert:
        for i in range(self.panelrows):
            panel_line = eval(f"context.scene.panel_line{i}")
            panel_line.manual = False
            self.skipnormals = False
        self.applyall = self.applyall
        # forced update of applyall_up
    else:
        self.applyall = False
    return


def usr_direfresh(self, context):
    if not os.path.isdir(self.usr_dir):
        self.usr_dir = os.path.expanduser('~') + os.path.sep
    scene = context.scene
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    directory = self.usr_dir
    dircontent = os.listdir(directory)
    self.dircontent = " ".join(str(x) for x in dircontent)
    lematname = MatnameCleaner.clean(self, context)[1]
    separator = self.separator
    relatedfiles = (filez for filez in dircontent if lematname in list(filez[:-4].split(separator)))

    for filez in relatedfiles:
        lefile = directory + filez

        rate = reversepattern(self, context, lefile)

        if rate > 50:
            break
    assumenamefrombsmprops(self, context)


def skipnormal_up(self, context):  #
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    return


class PatternsVariations():
    def liste(self, context, params):
        Prefix = params[0]
        mapname = params[1]
        separator = context.scene.bsmprops.separator
        Extension = params[2]
        matname = MatnameCleaner.clean(self, context)[1]

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


def prefix_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    assumenamefrombsmprops(self, context)
    checknamefrombsmprops(self, context)
    return


def separator_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    if self.separator.isspace() or len(self.separator) == 0:
        self.separator = "_"

    assumenamefrombsmprops(self, context)
    checknamefrombsmprops(self, context)
    return


def patternslist(self, context):
    mapname = "Map Name"
    Extension = ".Ext"
    Prefix = self.prefix
    pt_params = [Prefix, mapname, Extension]
    items = PatternsVariations.liste(self, context, pt_params)
    items.reverse()

    return items


def patterns_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    assumenamefrombsmprops(self, context)
    return


def applyall_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()
    if self.eraseall:
        self.shader = True
    return


def onlyamat_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()

    return


def fixname_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.createdummy()

    return


def manison_cb(self, context):
    manualenabled = (i for i in range(self.panelrows) if
                     eval(f"bpy.context.scene.panel_line{i}.labelbools") and eval(f"bpy.context.scene.panel_line{i}.manual"))

    manison = bool(len(list(manualenabled)))
    if manison:
        self.onlyamat = True
        self.applyall = False
        self.onlyactiveobj = True
    return manison


def isindir_updater(self, context):
    isit = False
    if context != None:
        if "scene" in dir(context)[:]:
            panel_line = self
            self.isindir = os.path.isfile(panel_line.probable)

    return isit
def cleaninputsockets(self,context):
    for i in range(10):
        panel_line = eval(f"context.scene.panel_line{i}")
        inputs = panel_line.inputsockets
        if not inputs.isalnum() :
            panel_line.inputsockets = '0'
    return
def shaderup(self, context):
    scene = bpy.context.scene
    cleaninputsockets(self,context)


        # poutputsokets_up(panel_line, context)

def onlyactiveobj_up(self, context):
    if self.onlyactiveobj:
        self.applyall = False
    return
class BSMprops(PropertyGroup):  # bsmprops

    customshader: BoolProperty(
        name="Enable or Disable",
        description=" Append your own Nodegroups in the 'Replace Shader' list above \
                    \n\
                    \n Allows to use Custom Shader nodes\
                    \n Custom NodeGroups must have a valid Surface Shader output socket \
                    \n and at least one input socket to appear in the list \
                    \n (Experimental !!!)",
        default=False,
        update=appendecustomshaders,
    )
    applyall: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to all visible objects ",
        default=False,
        update=applytoall_up,

    )
    onlyactiveobj: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to active object only ",
        default=False,
        update=onlyactiveobj_up
    )
    separator: StringProperty(
        name="",
        description=" Separator used in the pattern selector below \
                    \n for the Texture Map File name auto-detection.  \
                    \n (In most cases you want to leave it as it is)",
        default="_",
        update=separator_up,
    )
    eraseall: BoolProperty(
        name="Enable or Disable",
        description=" Clear existing nodes \
                     \n Removes all nodes from the material shader \
                     \n before setting up the nodes trees",
        default=False,
        update=applyall_up
    )
    extras: BoolProperty(
        name="Enable or Disable",
        description=" Attach RGB Curves and Color Ramps nodes\
                        \n\
                        \n Inserts a RGB Curve if the Texture map type is RGB \
                        \n or a Color ramp if the Texture Map type is Black & White\
                        \n between the Image texture node and the Shader Input Socket\
                        \n during Nodes Trees setup",
        default=False,
    )

    panelrows: IntProperty(
        name="Set a value",
        description="A integer property",
        default=5,
        min=1,
        max=10,
    )

    dircontent: StringProperty(
        name="Setavalue",
        description="content of selected texture folder",
        default="noneYet",
    )
    prefix: StringProperty(
        name="",
        description=" Prefix of the file names used in the pattern selector below \
                     \n for the Texture Map file name auto-detection.",
        default="PrefixNotSet",
        update=prefix_up,
    )
    emptylist: EnumProperty(
        name="Enable row to select input socket.",
        description="placeholder",
        items=[('0', '', '')]
    )
    patterns: EnumProperty(
        name="Patterns",
        description="Pattern for the Texture file name ",
        items=patternslist,
        # default = '1',
        update=patterns_up,
    )

    usr_dir: StringProperty(
        name="",
        description="Folder containing the Textures Images to be imported",
        subtype='DIR_PATH',
        default=os.path.expanduser('~') + os.path.sep,
        update=usr_direfresh
    )
    bsm_all: StringProperty(
        name="allsettings",
        description="allsettingssaved",
        default="None",

    )
    skipnormals: BoolProperty(
        name="Skip normal map detection",
        description=" Skip Normal maps and Height maps detection\
                            \n\
                            \n Usually the script inserts a Normal map converter node \
                            \n or a Bump map converter node according to the Texture Maps name\
                            \n Tick to bypass detection and link the Texture Maps directly ",
        default=False,
        update=skipnormal_up
    )

    shader: BoolProperty(
        name="",
        description=" Enable to replace the Material Shader with the one in the list \
                       \n\
                       \n (Enabled by default if 'Apply to all' is activated)",
        default=False,
        update=shaderup
    )

    shaderlist: EnumProperty(
        name="lashaderlist:",
        description=" Base Shader node selector \
                        \n Used to select a replacement for the current Shader node\
                        \n if 'Replace Shader' is enabled or if no valid Shader node is detected.\
                        \n Currently ",

        items=shaderlist_cb,
        update=shaderlist_up,
    )

    expert: BoolProperty(
        name="",
        description=" Allows Manual setup of the Maps filenames, \
                    \n  (Tick the checkbox between Map Name and Ext. to enable Manual)\
                    \n Allows Skipping Normal map detection,\
                    \n  (Tick 'Skip Normals' for Direct nodes connection)\
                    \n Disables 'Apply to All' in the Options tab",
        default=False,
        update=expert_up
    )
    onlyamat: BoolProperty(
        name="",
        description=" Apply on active material only, \
                        \n  (By default the script iterates through all materials\
                        \n  presents in the Material Slots.)\
                        \n Enable this to only use the active Material Slot.",
        default=False,
        update=onlyamat_up
    )
    fixname: BoolProperty(
        name="",
        description=" Remove the '.001', '.002', etc. suffixes from a duplicated Material name, \
                         \n without changing the Material name itself. \
                         \n  (Usefull for a copied object or duplicated Material\
                         \n  which got a '.00x' suffix appended. Warning: Experimental !!!) ",
        default=False,
        update=fixname_up
    )
    manison: BoolProperty(
        name="",
        description="Internal ",
        default=False
    )


class PaneLine0(PropertyGroup):
    # panel_line0
    ID: IntProperty(
        name="ID",
        default=0
    )
    name: StringProperty(
        name="name",
        default="PaneLine0"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="BaseColor",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )

    isindir: BoolProperty(
        name="",
        description="Is 'probable' a file ?",
        default=False
        # isindir_updater("context.scene.panel_line0",None)
    )


class PaneLine1(PropertyGroup):
    #panel_line1
    ID: IntProperty(
        name="ID",
        default=1
    )
    name: StringProperty(
        name="name",
        default="PaneLine1"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Roughness",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",

        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )

class PaneLine2(PropertyGroup):
    # panel_line2
    ID: IntProperty(
        name="ID",
        default=2
    )
    name: StringProperty(
        name="name",
        default="PaneLine2"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Metallic",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine3(PropertyGroup):
    # panel_line3
    ID: IntProperty(
        name="ID",
        default=3
    )
    name: StringProperty(
        name="name",
        default="PaneLine3"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Normal",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine4(PropertyGroup):
    # panel_line4
    ID: IntProperty(
        name="ID",
        default=4
    )
    name: StringProperty(
        name="name",
        default="PaneLine4"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Height",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine5(PropertyGroup):
    # panel_line5
    ID: IntProperty(
        name="ID",
        default=5
    )
    name: StringProperty(
        name="name",
        default="PaneLine5"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Specular",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine6(PropertyGroup):
    # panel_line6
    ID: IntProperty(
        name="ID",
        default=6
    )
    name: StringProperty(
        name="name",
        default="PaneLine6"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Glossy",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine7(PropertyGroup):
    # panel_line7
    ID: IntProperty(
        name="ID",
        default=7
    )
    name: StringProperty(
        name="name",
        default="PaneLine7"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Emission",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine8(PropertyGroup):
    # panel_line8
    ID: IntProperty(
        name="ID",
        default=8
    )
    name: StringProperty(
        name="name",
        default="PaneLine8"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Transparency",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )


class PaneLine9(PropertyGroup):
    # panel_line9
    ID: IntProperty(
        name="ID",
        default=9
    )
    name: StringProperty(
        name="name",
        default="PaneLine9"
    )
    maplabels: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Anisotropic",
        update=maptester
    )
    inputsockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=poutputsokets_cb,
        update=poutputsokets_up
    )
    labelbools: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=labelbools_up,
    )
    lefilename: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_update,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    mapext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=mapext_cb,
        update=mapext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
