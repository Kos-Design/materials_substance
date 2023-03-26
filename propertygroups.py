import bpy
from pathlib import Path

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
from . propertieshandler import PropertiesHandler as ph

def line_on_cb(self, context):
    scene = context.scene
    bsmprops = scene.bsmprops
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()

    bsmprops.manual_on = manual_on_cb(bsmprops, context)
    if not self.manual:
        bpy.ops.bsm.name_maker(line_num=self.ID)
        bpy.ops.bsm.name_checker(linen=self.ID, lorigin="line_on_cb", called=False)
    return

def apply_to_all_cb(self, context):
    target = "selected objects"

    if self.advanced_mode:
        target = "active object"
    if self.apply_to_all:
        target = "all visible objects"
        self.only_active_obj = False

    bpy.types.BSM_OT_import_textures.bl_description = "Setup nodes and load textures maps on " + target
    bpy.types.BSM_OT_make_nodes.bl_description = "Setup Nodes on " + target
    bpy.types.BSM_OT_assign_nodes.bl_description = "Load textures maps on " + target
    liste = [
        bpy.types.BSM_OT_import_textures,
        bpy.types.BSM_OT_make_nodes,
        bpy.types.BSM_OT_assign_nodes
    ]
    for cls in liste:
        laclasse = cls
        unregister_class(cls)
        register_class(laclasse)

    return

def file_name_update_cb(self, context):
    propper = ph()
    if self.manual:
        propper.pattern_weight(context, self.file_name)
    if Path(self.file_name).is_file():
        self.probable = self.file_name

    is_in_dir_updater(self,context=context)
    return

def custom_shader_on_cb(self, context):
    propper = ph()
    if context.scene.bsmprops.custom_shader_on:
        propper.set_nodes_groups(context)
    else:
        context.scene.node_links.clear()
    propper.clean_input_sockets(context)
    return
  
def enum_sockets_cb(self, context):
    # callback for the enumlist of the dynamic enums
    scene = context.scene
    shaders_links = scene.shader_links
    nodes_links = scene.node_links
    bsmprops = scene.bsmprops
    selectedshader = scene.bsmprops.shaders_list
    items = []
    rawdata = []
    propper = ph()
    for i in range(len(shaders_links)):
        if selectedshader in shaders_links[i].shadertype:
            rawdata = shaders_links[i].input_sockets.split("@-¯\(°_o)/¯-@")

    for i in range(len(nodes_links)):
        if selectedshader in nodes_links[i].nodetype:
            rawdata = nodes_links[i].input_sockets.split("@-¯\(°_o)/¯-@")

    if not bsmprops.shader:  # and valid mat
        mat_used = propper.mat_name_cleaner(context)[0]
        rawdata = propper.get_shader_inputs(context,mat_used)

    items = propper.format_enum(context, rawdata)
    # if len(items)
    return items

def enum_sockets_up(self, context):
    # update for the enumlist
    scene = context.scene
    state = self.input_sockets
    if state.isalnum == '' :
        self.input_sockets = '0'
    disped = ['Displacement', 'Disp Vector']

    zid = self.ID
    if state != '0':
        same = (i for i in range(10) if state == eval(f"bpy.context.scene.panel_line{i}").input_sockets and i != zid)
        # if same in another slot then clear
        for i in same:
            panel_line = eval(f"scene.panel_line{i}")
            panel_line.input_sockets = '0'
        if state in disped:
            disped = list(j for j in range(10) if (str(eval(f"bpy.context.scene.panel_line{j}").input_sockets) in disped))

            # if already a kind of Disp in list then clear
            for j in disped:

                if j != zid:
                    panel_line = eval(f"scene.panel_line{j}")
                    panel_line.input_sockets = '0'
 
    return

def map_label_cb(self, context):
    if not self.manual:
        bpy.ops.bsm.name_maker(line_num=self.ID)
        bpy.ops.bsm.find_ext(linen=self.ID, keepat=True, called=True)
    return

def map_ext_cb(self, context):
    propper = ph()
    filetypes = propper.get_extensions(context)

    return filetypes

def map_ext_up(self, context):
    if not self.manual:
        bpy.ops.bsm.name_maker(line_num=self.ID)
    return

def shaders_list_cb(self, context):
    propper = ph()
    shaders_list = propper.get_shaders_list(context)
    return shaders_list

def shaders_list_up(self, context):
    propper = ph()
    scene = context.scene
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    propper.clean_input_sockets(context)
    return

def manual_up(self, context):
    bsmprops = context.scene.bsmprops
    if not self.manual:
        bpy.ops.bsm.name_maker(line_num=self.ID)
    #TODO: why ? this could loop ?    
    bsmprops.manual_on = manual_on_cb(bsmprops, context)

    return

def advanced_mode_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    if not self.advanced_mode:
        for i in range(self.panel_rows):
            panel_line = eval(f"context.scene.panel_line{i}")
            panel_line.manual = False
            self.skip_normals = False
        self.apply_to_all = self.apply_to_all
        # forced update of apply_to_all_cb
        #call cb instead
    else:
        self.apply_to_all = False
    return

def usr_dir_cb(self, context):
    propper = ph()
    if not Path(self.usr_dir).is_dir():
        self.usr_dir = str(Path.home())
    scene = context.scene
    if len(scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    directory = self.usr_dir
    dir_content = [x.name for x in Path(directory).glob('*.*') ]
    self.dir_content = " ".join(str(x) for x in dir_content)
    lematname = propper.mat_name_cleaner(context)[1]
    separator = self.separator
    relatedfiles = (filez for filez in dir_content if lematname in list((Path(filez).stem).split(separator)))

    for filez in relatedfiles:
        try:
            lefile = directory + filez

            rate = propper.pattern_weight(context, lefile)

            if rate > 50:
                break
        except IOError:
            continue
    propper.make_names(context)

def skip_normals_up(self, context):  #
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    return

def prefix_cb(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    propper = ph()
    propper.make_names(context)
    propper.check_names(context)
    return

def separator_cb(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    if self.separator.isspace() or len(self.separator) == 0:
        self.separator = "_"
    propper = ph()
    propper.make_names(context)
    propper.check_names(context)
    return

def patterns_cb(self, context):
    mapname = "Map Name"
    Extension = ".Ext"
    Prefix = self.prefix
    propper = ph()
    matname = propper.mat_name_cleaner(context)[1]
    pt_params = {'prefix':Prefix, 'map_name':mapname, 'ext':Extension, 'mat_name':matname}
    items = propper.get_patterns(context, **pt_params)
    items.reverse()

    return items

def patterns_up(self, context):
    propper = ph()
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    propper = ph()    
    propper.make_names(context)
    return

def apply_to_all_cb(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()
    if self.eraseall:
        self.shader = True
    return

def only_active_mat_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()

    return

def fix_name_up(self, context):
    if len(context.scene.shader_links) == 0:
        bpy.ops.bsm.make_nodetree()

    return

def manual_on_cb(self, context):
    manual_enabled = (i for i in range(self.panel_rows) if
                     eval(f"bpy.context.scene.panel_line{i}.line_on") and eval(f"bpy.context.scene.panel_line{i}.manual"))

    manual_on = bool(len(list(manual_enabled)))
    if manual_on:
        self.only_active_mat = True
        self.apply_to_all = False
        self.only_active_obj = True
    return manual_on

def is_in_dir_updater(self, context):
    isit = False
    if context != None:
        if "scene" in dir(context)[:]:
            panel_line = self
            self.is_in_dir = Path(panel_line.probable).is_file()

    return isit

def shader_up(self, context):
    scene = bpy.context.scene
    propper = ph()
    propper.clean_input_sockets(context)

def only_active_obj_cb(self, context):
    if self.only_active_obj:
        self.apply_to_all = False
    return

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
    input_sockets: StringProperty(
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
    input_sockets: StringProperty(
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


class BSMprops(PropertyGroup):

    custom_shader_on: BoolProperty(
        name="Enable or Disable",
        description=" Append your own Nodegroups in the 'Replace Shader' list above \
                    \n\
                    \n Allows to use Custom Shader nodes\
                    \n Custom NodeGroups must have a valid Surface Shader output socket \
                    \n and at least one input socket to appear in the list \
                    \n (Experimental !!!)",
        default=False,
        update=custom_shader_on_cb,
    )
    apply_to_all: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to all visible objects ",
        default=False,
        update=apply_to_all_cb,
    )
    only_active_obj: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to active object only ",
        default=False,
        update=only_active_obj_cb
    )
    separator: StringProperty(
        name="",
        description=" Separator used in the pattern selector \
                    \n for the Texture Map File name auto-detection.  \
                    \n (In most cases you want to leave it as it is)",
        default="_",
        update=separator_cb,
    )
    eraseall: BoolProperty(
        name="Enable or Disable",
        description=" Clear existing nodes \
                     \n Removes all nodes from the material shader \
                     \n before setting up the nodes trees",
        default=False,
        #TODO:why ? Check behaviour 
        update=apply_to_all_cb
    )
    tweak_levels: BoolProperty(
        name="Enable or Disable",
        description=" Attach RGB Curves and Color Ramps nodes\
                        \n\
                        \n Inserts a RGB Curve if the Texture map type is RGB \
                        \n or a Color ramp if the Texture Map type is Black & White\
                        \n between the Image texture node and the Shader Input Socket\
                        \n during Nodes Trees setup",
        default=False,
    )
    panel_rows: IntProperty(
        name="Set a value",
        description="A integer property",
        default=5,
        min=1,
        max=10,
    )
    dir_content: StringProperty(
        name="Setavalue",
        description="content of selected texture folder",
        default="noneYet",
    )
    prefix: StringProperty(
        name="",
        description=" Prefix of the file names used in the pattern selector below \
                     \n for the Texture Map file name auto-detection.",
        default="PrefixNotSet",
        update=prefix_cb,
    )
    enum_placeholder: EnumProperty(
        name="Enable row to select input socket.",
        description="placeholder",
        items=[('0', '', '')]
    )
    patterns: EnumProperty(
        name="Patterns",
        description="Pattern for the Texture file name ",
        items=patterns_cb,
        # default = '1',
        update=patterns_up,
    )
    usr_dir: StringProperty(
        name="",
        description="Folder containing the Textures Images to be imported",
        subtype='DIR_PATH',
        default=str(Path.home()),
        update=usr_dir_cb
    )
    bsm_all: StringProperty(
        name="allsettings",
        description="concatenated string of all settings used for preset saving",
        default="None",
    )
    skip_normals: BoolProperty(
        name="Skip normal map detection",
        description=" Skip Normal maps and Height maps detection\
                            \n\
                            \n Usually the script inserts a Normal map converter node \
                            \n or a Bump map converter node according to the Texture Maps name\
                            \n Tick to bypass detection and link the Texture Maps directly ",
        default=False,
        update=skip_normals_up
    )
    shader: BoolProperty(
        name="",
        description=" Enable to replace the Material Shader with the one in the list \
                       \n\
                       \n (Enabled by default if 'Apply to all' is activated)",
        default=False,
        update=shader_up
    )
    shaders_list: EnumProperty(
        name="shaders_list:",
        description=" Base Shader node selector \
                        \n Used to select a replacement for the current Shader node\
                        \n if 'Replace Shader' is enabled or if no valid Shader node is detected.\
                        \n ",

        items=shaders_list_cb,
        update=shaders_list_up,
    )
    advanced_mode: BoolProperty(
        name="",
        description=" Allows Manual setup of the Maps filenames, \
                    \n  (Tick the checkbox between Map Name and Ext. to enable Manual)\
                    \n Allows Skipping Normal map detection,\
                    \n  (Tick 'Skip Normals' for Direct nodes connection)\
                    \n Disables 'Apply to All' in the Options tab",
        default=False,
        update=advanced_mode_up
    )
    only_active_mat: BoolProperty(
        name="",
        description=" Apply on active material only, \
                        \n  (By default the script iterates through all materials\
                        \n  presents in the Material Slots.)\
                        \n Enable this to only use the active Material Slot.",
        default=False,
        update=only_active_mat_up
    )
    fix_name: BoolProperty(
        name="",
        description=" Remove the '.001', '.002', etc. suffixes from a duplicated Material name, \
                         \n without changing the Material name itself. \
                         \n  (Usefull for a copied object or duplicated Material\
                         \n  which got a '.00x' suffix appended. Warning: Experimental !!!) ",
        default=False,
        update=fix_name_up
    )
    manual_on: BoolProperty(
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="BaseColor",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )

    is_in_dir: BoolProperty(
        name="",
        description="Is 'probable' a file ?",
        default=False
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Roughness",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",

        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Metallic",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Normal",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Height",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Specular",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Glossy",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Emission",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Transparency",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,

    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )
    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
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
    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the Texture map to be imported",
        default="Anisotropic",
        update=map_label_cb
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        name="",
        description="Enable/Disable line",
        default=False,
        update=line_on_cb,
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file",
        update=file_name_update_cb,
    )
    probable: StringProperty(
        subtype='FILE_PATH',
        description="probable filename",
        default="nope",
    )

    map_ext: EnumProperty(
        name="Texture file type",
        description="Extension of the texture map file",
        items=map_ext_cb,
        update=map_ext_up
    )
    manual: BoolProperty(
        name="",
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
