import bpy
from pathlib import Path
import json
import functools

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
from . propertieshandler import PropertiesHandler, props, node_links, lines, texture_importer

propper = PropertiesHandler()

def line_on_up(self, context):
    propper.default_sockets(context, self)
    propper.refresh_shader_links(context)
    return

def initialize_defaults(self, context):
    if len(self.textures) != 0:
        return
    maps = ["Color","Roughness","Metallic","Normal"]
    for i in range(4):
        item = self.textures.add()
        item.name = f"{maps[i]} map"
        item.name = f"{maps[i]}"
        propper.default_sockets(bpy.context,item)
    return

def apply_to_all_objs_up(self, context):
    target = "selected objects"
    if self.advanced_mode:
        target = "active object"
    if self.apply_to_all_objs:
        target = "all visible objects"
        self.only_active_obj = False
    bpy.types.NODE_OT_stm_import_textures.bl_description = "Setup nodes and load textures maps on " + target
    bpy.types.NODE_OT_stm_make_nodes.bl_description = "Setup Nodes on " + target
    bpy.types.NODE_OT_stm_assign_nodes.bl_description = "Load textures maps on " + target
    liste = [
        bpy.types.NODE_OT_stm_import_textures,
        bpy.types.NODE_OT_stm_make_nodes,
        bpy.types.NODE_OT_stm_assign_nodes
    ]
    for cls in liste:
        laclasse = cls
        unregister_class(cls)
        register_class(laclasse)
    return

def target_list_cb(self,context):
    targets = [('selected_objects', 'Selected Objects materials', '',0),
                ('all_visible', 'All visible Objects materials', '',1),
                ('all_objects', 'All Objects materials', '',2),
                ('all_materials', 'All scene materials', '',3),
                ('active_obj', 'Only Active Object in selection', '',4),
            ]
    return targets

def match_sockets_up(self,context):
    if self.match_sockets:
        replace_shader_up(self,context)

def target_list_up(self,context):
    match self.target:
        case "selected_objects":
            pass
        case "all_visible":
            pass
        case "all_objects":
            pass
        case "all_materials":
            self.apply_to_all_mats = True
            self.only_active_mat = False
        case "active_obj":
            pass
    #if self.advanced_mode:
    return

def apply_to_all_mats_up(self, context):
    target = "selected objects"
    bpy.types.NODE_OT_stm_import_textures.bl_description = "Setup nodes and load textures maps on " + target
    bpy.types.NODE_OT_stm_make_nodes.bl_description = "Setup Nodes on " + target
    bpy.types.NODE_OT_stm_assign_nodes.bl_description = "Load textures maps on " + target
    liste = [
        bpy.types.NODE_OT_stm_import_textures,
        bpy.types.NODE_OT_stm_make_nodes,
        bpy.types.NODE_OT_stm_assign_nodes
    ]
    for cls in liste:
        laclasse = cls
        unregister_class(cls)
        register_class(laclasse)
    return

def make_clean_channels(self,context):
    self.channels.socket.clear()
    for i in range(3):
        item = self.channels.socket.add()
        item.name = ['R','G','B'][i]

def split_rgb_up(self,context):
    if not (len(self.channels.socket) and len(self.channels.socket) == 3):
        make_clean_channels(self,context)

def include_ngroups_up(self, context):
    if props().include_ngroups:
        propper.set_nodes_groups(context)
    else:
        node_links().clear()
    propper.refresh_shader_links(context)
    propper.guess_sockets(context)

def enum_sockets_cb(self, context):
    return propper.get_sockets_enum_items(context)

def enum_sockets_up(self, context):
    context.view_layer.update()

def line_name_up(self, context):
    if not self.manual:
        propper.detect_a_map(context,self)

def shaders_list_cb(self, context):
    return propper.get_shaders_list(context)

def shaders_list_up(self, context):
    if self.replace_shader:
        propper.guess_sockets(context)
    context.view_layer.update()

def manual_up(self, context):
    if self.manual:
        props().target = 'active_obj'
        props().only_active_mat = True
        props().apply_to_all_objs = False
        props().only_active_obj = True
        props().apply_to_all_mats = False
    else:
        propper.detect_a_map(context,self)

def advanced_mode_up(self, context):
    propper.refresh_shader_links(context)
    if not self.advanced_mode:
        for line in lines():
            line.manual = False
            line.split_rgb = False

def usr_dir_up(self, context):
    self.dir_content = ""
    if not Path(self.usr_dir).is_dir():
        self.usr_dir = str(Path(self.usr_dir).parent)
        if not Path(self.usr_dir).is_dir():
            self.usr_dir = f"{(Path(__file__).parent)}"
    dir_content = [x.name for x in Path(self.usr_dir).glob('*.*') ]
    if len(dir_content) :
        self.dir_content = json.dumps((dict(zip(range(len(dir_content)), dir_content))))
    if self.match_sockets:
        replace_shader_up(props(),bpy.context)

def dup_mat_compatible_up(self,context):
    propper.detect_relevant_maps(context)

def clear_nodes_up(self, context):
    if self.clear_nodes:
        self.replace_shader = True

def only_active_mat_up(self, context):
    if "all_materials" in self.target and self.only_active_mat:
        self.target = "selected_objects"
    propper.refresh_shader_links(context)

def replace_shader_up(self, context):
    propper.clean_input_sockets(context)
    if self.include_ngroups:
        node_links().clear()
        include_ngroups_up(self,context)
    propper.refresh_shader_links(context)
    propper.guess_sockets(context)
    context.view_layer.update()

def only_active_obj_up(self, context):
    if self.only_active_obj:
        self.apply_to_all_objs = False

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
        default="{'0':''}"
    )
    input_sockets: StringProperty(
        name="",
        description="Shader input sockets for this texture node",
        default="{'0':''}"
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default="{'0':''}"
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
        default="{'0':''}"
    )
    input_sockets: StringProperty(
        name="list of input sockets",
        default="{'0':''}"
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default="{'0':''}"
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


class ChannelSocket(PropertyGroup):
    input_sockets: EnumProperty(
        name="Input socket",
        description="Target shader input sockets for this texture node",
        items=enum_sockets_cb,
        #update=enum_sockets_up
    )


class ChannelSockets(PropertyGroup):
    socket: CollectionProperty(type=ChannelSocket)
    sockets_index: IntProperty(default=0)

def get_name_up(self):
    return self.get("name","")

def set_name_up(self, value):
    self["name"] = value
    if not self.manual and props().match_sockets:
        replace_shader_up(props(),bpy.context)

class PanelLines(PropertyGroup):
    name: StringProperty(
        name="name",
        description="Keyword identifier of the texture map to import",
        get=get_name_up,
        set=set_name_up
    )

    channels: PointerProperty(type=ChannelSockets)

    file_name: StringProperty(
        name="File",
        subtype='FILE_PATH',
        description="Complete filepath of the texture map",
        default="Select a file"
    )
    input_sockets: EnumProperty(
        name="",
        description="Target shader input sockets for this texture node",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    file_is_real: BoolProperty(
        description="Associated file exists",
        default=False
    )
    manual: BoolProperty(
        name='Overwrite file name',
        description="Manual mode switch",
        default=False,
        update=manual_up
    )
    line_on: BoolProperty(
        name="Active",
        description="Enable/Disable line",
        default=True,
        update=line_on_up
    )
    split_rgb: BoolProperty(
        name="Split rgb channels",
        description="Split the RGB channels of the target image to plug them into individual sockets",
        default=False,
        update=split_rgb_up
    )


class PanelLiner(PropertyGroup):
    textures: CollectionProperty(type=PanelLines)
    texture_index: IntProperty(default=0,update=initialize_defaults)


class StmProps(PropertyGroup):
    texture_importer: PointerProperty(type=PanelLiner)
    include_ngroups: BoolProperty(
        name="Enable or Disable",
        description=" Append your own Nodegroups in the 'Replace Shader' list above \
                    \n\
                    \n Allows to use Custom Shader nodes\
                    \n Custom NodeGroups must have a valid Surface Shader output socket \
                    \n and at least one input socket to appear in the list \
                    \n (Experimental !!!)",
        default=False,
        update=include_ngroups_up
    )
    apply_to_all_objs: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to all visible objects ",
        default=False,
        update=apply_to_all_objs_up
    )

    custom_preset_name: StringProperty(
        name="Preset name",
        description="New preset name",
        default="preset name"
    )
    apply_to_all_mats: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to all materials ",
        default=False,
        update=apply_to_all_mats_up
    )
    only_active_obj: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to active object only ",
        default=False,
        update=only_active_obj_up
    )
    clear_nodes: BoolProperty(
        name="Enable or Disable",
        description=" Clear existing nodes \
                     \n Removes all nodes from the material shader \
                     \n before setting up the nodes trees",
        default=False,
        update=clear_nodes_up
    )
    target: EnumProperty(
        name="Target ",
        description=" Objects or materials affected by the operations ",
        items=target_list_cb,
        update=target_list_up
    )
    match_sockets: BoolProperty(
        name="Enable or Disable",
        description=" Auto-detect sockets\
                        \n\
                        \n The addon attempts to match each texture map to its corresponding\
                        \n shader socket according to its keyword defined in the panel lines.\
                        \n Disable this if you want to skip this detection in order to plug \
                        \n the textures in non-matching sockets(ex:Metallic into Roughness etc.)",
        default=True,
        update=match_sockets_up
    )
    tweak_levels: BoolProperty(
        name="Enable or Disable",
        description=" Attach RGB Curves and Color Ramps nodes\
                        \n\
                        \n Inserts a RGB Curve if the Texture map type is RGB \
                        \n or a Color ramp if the texture map type is Black & White\
                        \n between the Image texture node and the Shader Input Socket\
                        \n during Nodes Trees setup",
        default=False
    )
    dir_content: StringProperty(
        name="Setavalue",
        description="content of selected texture folder",
        default=""
    )
    usr_dir: StringProperty(
        name="",
        description="Folder containing the Textures Images to be imported",
        subtype="DIR_PATH",
        default=bpy.utils.extension_path_user(f'{__package__}', create=True),
        update=usr_dir_up
    )
    stm_all: StringProperty(
        name="allsettings",
        description="Json string of all settings, used internally for preset saving",
        default="{'0':'0'}"
    )
    skip_normals: BoolProperty(
        name="Skip normal map detection",
        description=" Skip Normal maps and Height maps detection.\
                            \n\
                            \n Usually the script inserts a Normal map converter node \
                            \n or a Bump map converter node according to the texture maps name.\
                            \n Tick to link the texture map directly",
        default=False
    )
    replace_shader: BoolProperty(
        description=" Enable to replace the Material Shader with the one in the list \
                       \n\
                       \n (Enabled by default if 'Apply to all' is activated)",
        default=True,
        update=replace_shader_up
    )
    shaders_list: EnumProperty(
        name="shaders_list:",
        description=" Base Shader node selector \
                        \n Used to select a replacement for the current Shader node\
                        \n if 'Replace Shader' is enabled or if no valid Shader node is detected.",

        items=shaders_list_cb,
        update=shaders_list_up
    )
    advanced_mode: BoolProperty(
        description=" Allows Manual setup of the Maps filenames, \
                    \n  (Tick the checkbox between Map Name and Sockets to enable manual file selection)",
        default=False,
        update=advanced_mode_up
    )
    only_active_mat: BoolProperty(
        description=" Apply on active material only, \
                        \n  (By default the script iterates through all materials\
                        \n  presents in the Material Slots.)\
                        \n Enable this to only use the active Material Slot.",
        default=False,
        update=only_active_mat_up
    )
    dup_mat_compatible: BoolProperty(
        description=" Process duplicated materials names like the originals, \
                        \n  Use this to treat materials with suffix .001\
                        \n  as the original ones (ignores the .00x suffix)",
        default=True
    )
