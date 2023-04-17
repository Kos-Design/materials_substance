import bpy
from pathlib import Path
import json

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
    scene = context.scene
    propper = ph()
    ndh = nha()
    propper.default_sockets(context, self)
    bsmprops = scene.bsmprops
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
    #items = propper.get_sockets_enum_items(context)
    #if isitems
    return propper.get_sockets_enum_items(context)
    
def enum_sockets_up(self, context):
    context.view_layer.update()

def map_label_up(self, context):
    if not self.manual:
        propper = ph()
        propper.detect_a_map(context,self.ID)
        propper.default_sockets(context, self)

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
    propper = ph()
    propper.detect_a_map(context,self.ID)
    if self.manual:
        bsmprops = context.scene.bsmprops
        bsmprops.only_active_mat = True
        bsmprops.apply_to_all = False
        bsmprops.only_active_obj = True

def advanced_mode_up(self, context):
    ndh = nha()
    ndh.refresh_shader_links(context)
    if not self.advanced_mode:
        for i in range(self.panel_rows):
            panel_line = eval(f"context.scene.panel_line{i}")
            panel_line.manual = False
        apply_to_all_up(self,context)
    else:
        self.apply_to_all = False

def usr_dir_up(self, context):
    propper = ph()
    if not Path(self.usr_dir).is_dir():
        self.usr_dir = str(Path(self.usr_dir).parent)
        if not Path(self.usr_dir).is_dir():
            self.usr_dir = str(Path.home())
    scene = context.scene
    dir_content = [x.name for x in Path(self.usr_dir).glob('*.*') ]
    self.dir_content = json.dumps((dict(zip(range(len(dir_content)), dir_content))))
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
    ndh = nha()
    ndh.refresh_shader_links(context)
    propper.guess_sockets(context)
    context.view_layer.update()

def only_active_obj_up(self, context):
    if self.only_active_obj:
        self.apply_to_all = False

def name_checker_up(self,context):
    scene = context.scene
    props = scene.bsmprops
    if self.file_is_real :
        propper = ph()
        propper.default_sockets(context, self)
        propper.detect_a_map(context,self.ID)
        bpy.ops.bsm.reporter(reporting=f"{Path(self.file_name).name} detected in [...]/{Path(props.usr_dir).stem}")
    else:
        bpy.ops.bsm.reporter(reporting=f"No image containing {self.map_label} found for this material in [...]/{Path(props.usr_dir).stem}")    
    if self.name_checker:
        self.name_checker = False
        
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
        default='{"0":""}'
    )
    input_sockets: StringProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        default='{"0":""}'
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default='{"0":""}'
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
        default='{"0":""}'
    )
    input_sockets: StringProperty(
        name="list of input sockets",
        default='{"0":""}'
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default='{"0":""}'
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
                        \n or a Color ramp if the Texture Map type is Black & White\
                        \n between the Image texture node and the Shader Input Socket\
                        \n during Nodes Trees setup",
        default=False
    )
    panel_rows: IntProperty(
        name="Set a value",
        description="Number of map rows displayed in the UI",
        default=5,
        min=1,
        max=10
    )
    dir_content: StringProperty(
        name="Setavalue",
        description="content of selected texture folder",
        default='{"0":"Cube_Material_BaseColor.exr","1":"Cube_Material_roughness.exr"}'
    )
    enum_placeholder: EnumProperty(
        name="Enable row to select input socket.",
        description="placeholder",
        items=[('0', '', '')]
    )
    usr_dir: StringProperty(
        description="Folder containing the Textures Images to be imported",
        subtype='DIR_PATH',
        default=str(Path(__file__).parent.joinpath("maps_example")),
        update=usr_dir_up
    )
    bsm_all: StringProperty(
        name="allsettings",
        description="concatenated string of all settings used for preset saving",
        default='{"0":"0"}'
    )
    skip_normals: BoolProperty(
        name="Skip normal map detection",
        description=" Skip Normal maps and Height maps detection\
                            \n\
                            \n Usually the script inserts a Normal map converter node \
                            \n or a Bump map converter node according to the Texture Maps name\
                            \n Tick to bypass detection and link the Texture Maps directly ",
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
                        \n if 'Replace Shader' is enabled or if no valid Shader node is detected.\
                        \n ",

        items=shaders_list_cb,
        update=shaders_list_up
    )
    advanced_mode: BoolProperty(
        description=" Allows Manual setup of the Maps filenames, \
                    \n  (Tick the checkbox between Map Name and Sockets to enable Manual)\
                    \n Allows Skipping Normal map detection,\
                    \n  (Tick 'Skip Normals' for Direct nodes connection)\
                    \n Disables 'Apply to All' in the Options tab",
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=True,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="maps_example/Cube_Material_BaseColor.exr"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="File detected in selected folder",
        default=True
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=True,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="maps_example/Cube_Material_roughness.exr"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=True
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
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
        update=map_label_up
    )
    input_sockets: EnumProperty(
        name="Sockets",
        description="Shader input sockets in which to plug the Texture Nodes",
        items=enum_sockets_cb,
        update=enum_sockets_up
    )
    line_on: BoolProperty(
        description="Enable/Disable line",
        default=False,
        update=line_on_up
    )
    file_name: StringProperty(
        name="File name",
        subtype='FILE_PATH',
        description="Complete filepath of the Texture Map ",
        default="Select a file"
    )
    manual: BoolProperty(
        description="Manual Mode (Enable to select the Map File directly)",
        default=False,
        update=manual_up
    )
    name_checker: BoolProperty(
        description="file_name is in bsmprops.usr_dir",
        default=False,
        update=name_checker_up
    )
    file_is_real: BoolProperty(
        description="Associated file detected in that folder",
        default=False
    )
