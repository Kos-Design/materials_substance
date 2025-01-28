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
from . propertieshandler import PropertiesHandler as ph

from . nodeshandler import NodeHandler as nha

def line_on_up(self, context):
    propper = ph()
    ndh = nha()
    propper.default_sockets(context, self)
    ndh.refresh_shader_links(context)
    return

def apply_to_all_up(self, context):
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

def include_ngroups_up(self, context):
    propper = ph()

    if context.scene.bsmprops.include_ngroups:
        propper.set_nodes_groups(context)
    else:
        context.scene.node_links.clear()
    ndh = nha()
    ndh.refresh_shader_links(context)
    propper.clean_input_sockets(context)
    propper.guess_sockets(context)

def enum_sockets_cb(self, context):
    propper = ph()
    return propper.get_sockets_enum_items(context)

def enum_sockets_up(self, context):
    context.view_layer.update()

def map_label_up(self, context):
    if not self.manual:
        propper = ph()
        propper.detect_a_map(context,self)

def shaders_list_cb(self, context):
    propper = ph()
    return propper.get_shaders_list(context)

def shaders_list_up(self, context):
    propper = ph()
    if self.replace_shader:
        propper.clean_input_sockets(context)
        propper.guess_sockets(context)
    context.view_layer.update()

def manual_up(self, context):
    if self.manual:
        bsmprops = context.scene.bsmprops
        bsmprops.only_active_mat = True
        bsmprops.apply_to_all = False
        bsmprops.only_active_obj = True
    else:
        propper = ph()
        propper.detect_a_map(context,self)

def advanced_mode_up(self, context):
    ndh = nha()
    ndh.refresh_shader_links(context)
    if not self.advanced_mode:
        props = context.scene.bsmprops
        lines = props.texture_importer.textures
        for line in lines:
            line.manual = False
        apply_to_all_up(self,context)
    else:
        self.apply_to_all = False

def usr_dir_up(self, context):
    propper = ph()
    self.dir_content = ""
    #in case a file path is manually entered instead of a folder path
    if not Path(self.usr_dir).is_dir():
        self.usr_dir = str(Path(self.usr_dir).parent)
        if not Path(self.usr_dir).is_dir():
            #reverting to addon folder by default if no valid texture folder is set
            self.usr_dir = f"{(Path(__file__).parent)}"
    dir_content = [x.name for x in Path(self.usr_dir).glob('*.*') ]
    if len(dir_content) :
        self.dir_content = json.dumps((dict(zip(range(len(dir_content)), dir_content))))
    propper.detect_relevant_maps(context)

def dup_mat_compatible_up(self,context):
    propper = ph()
    propper.detect_relevant_maps(context)

def clear_nodes_up(self, context):
    if self.clear_nodes:
        self.replace_shader = True

def only_active_mat_up(self, context):
    ndh = nha()
    ndh.refresh_shader_links(context)

def replace_shader_up(self, context):
    scene = bpy.context.scene
    propper = ph()
    propper.clean_input_sockets(context)
    if self.include_ngroups:
        scene.node_links.clear()
        include_ngroups_up(self,context)
    ndh = nha()
    ndh.refresh_shader_links(context)
    propper.guess_sockets(context)
    context.view_layer.update()

def only_active_obj_up(self, context):
    if self.only_active_obj:
        self.apply_to_all = False

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


class PanelLines(PropertyGroup):

    map_label: StringProperty(
        name="Map name",
        description="Keyword identifier of the texture map to import",
        default="Metallic",
        update=map_label_up
    )
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


class PanelLiner(PropertyGroup):
    textures: CollectionProperty(type=PanelLines)
    texture_index: IntProperty(default=0)


class BSMprops(PropertyGroup):
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
    apply_to_all: BoolProperty(
        name="Enable or Disable",
        description="Apply Operations to all visible objects ",
        default=False,
        update=apply_to_all_up
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
        subtype='DIR_PATH',
        default=str(Path(__file__).parent),
        update=usr_dir_up
    )
    bsm_all: StringProperty(
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
        default=False,
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
