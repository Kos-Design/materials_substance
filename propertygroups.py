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
from . propertieshandler import PropertiesHandler, props, node_links, lines,p_lines, texture_importer
from . nodeshandler import NodeHandler

propper = PropertiesHandler()
ndh = NodeHandler()
_msgbus_owner = None

def line_on_up(self, context):
    propper.default_sockets(self)
    propper.refresh_shader_links()
    return

def material_update_callback():
    try:
        propper.mat = ndh.mat = bpy.context.object.active_material
        replace_shader_up(props(),bpy.context)
    except :
        print("pouet")

def unregister_msgbus():
    global _msgbus_owner
    if _msgbus_owner:
        bpy.msgbus.clear_by_owner(_msgbus_owner)
        _msgbus_owner = None

def register_msgbus():
    global _msgbus_owner
    _msgbus_owner = object()
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "active_material"),
        owner=_msgbus_owner,
        args=(),
        notify=material_update_callback
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "active_material_index"),
        owner=_msgbus_owner,
        args=(),
        notify=material_update_callback
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, "active"),
        owner=_msgbus_owner,
        args=(),
        notify=material_update_callback
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.MaterialSlot, "link"),
        owner=_msgbus_owner,
        args=(),
        notify=material_update_callback
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "material_slots"),
        owner=_msgbus_owner,
        args=(),
        notify=material_update_callback
    )


def target_list_cb(self,context):
    targets = [('selected_objects', 'Selected Objects materials', '',0),
                ('all_visible', 'All visible Objects materials', '',1),
                ('all_objects', 'All Objects materials', '',2),
                ('all_materials', 'All scene materials', '',3),
                ('active_obj', 'Only Active Object in selection', '',4),
            ]
    return targets

def get_presets(self, context):
    presets = [('0','-Select Preset-', ''),]
    preset_directory = Path(bpy.utils.extension_path_user(f'{__package__}',path="stm_presets", create=True))
    for file in sorted(preset_directory.glob("*.py")):
        presets.append((f"{file}", f"{file.stem}", ""))
    return presets

def apply_preset(self,context):
    propper.read_preset()

def custom_preset_enum_up(self, context):
    apply_preset(self,context)

def target_list_up(self,context):
    match self.target:
        case "selected_objects":
            pass
        case "all_visible":
            pass
        case "all_objects":
            pass
        case "all_materials":
            self.only_active_mat = False
        case "active_obj":
            pass
    #if self.advanced_mode:
    return

def set_operator_description(self, context):
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

def split_rgb_up(self,context):
    if not (len(self.channels.socket) and len(self.channels.socket) == 3):
        propper.make_clean_channels(self)
    if self.auto_mode:
        propper.default_sockets(self)

def include_ngroups_up(self, context):
    if props().include_ngroups:
        propper.set_nodes_groups()
    else:
        node_links().clear()
    propper.refresh_shader_links()
    propper.guess_sockets()

def enum_sockets_cb(self, context):
    inp_list = propper.get_sockets_enum_items()
    if not inp_list or len(inp_list) < 5:
        print('reverting to default list')
        return [('no_socket', '-- Unmatched Socket --', ''), ('Base Color', 'Base Color', ''), ('Metallic', 'Metallic', ''), ('Roughness', 'Roughness', ''), ('IOR', 'IOR', ''), ('Alpha', 'Alpha', ''), ('Normal', 'Normal', ''), ('Diffuse Roughness', 'Diffuse Roughness', ''), ('Subsurface Weight', 'Subsurface Weight', ''), ('Subsurface Radius', 'Subsurface Radius', ''), ('Subsurface Scale', 'Subsurface Scale', ''), ('Subsurface IOR', 'Subsurface IOR', ''), ('Subsurface Anisotropy', 'Subsurface Anisotropy', ''), ('Specular IOR Level', 'Specular IOR Level', ''), ('Specular Tint', 'Specular Tint', ''), ('Anisotropic', 'Anisotropic', ''), ('Anisotropic Rotation', 'Anisotropic Rotation', ''), ('Tangent', 'Tangent', ''), ('Transmission Weight', 'Transmission Weight', ''), ('Coat Weight', 'Coat Weight', ''), ('Coat Roughness', 'Coat Roughness', ''), ('Coat IOR', 'Coat IOR', ''), ('Coat Tint', 'Coat Tint', ''), ('Coat Normal', 'Coat Normal', ''), ('Sheen Weight', 'Sheen Weight', ''), ('Sheen Roughness', 'Sheen Roughness', ''), ('Sheen Tint', 'Sheen Tint', ''), ('Emission Color', 'Emission Color', ''), ('Emission Strength', 'Emission Strength', ''), ('Thin Film Thickness', 'Thin Film Thickness', ''), ('Thin Film IOR', 'Thin Film IOR', ''), ('Disp Vector', 'Disp Vector', ''), ('Displacement', 'Displacement', ''),('Ambient Occlusion','Ambient Occlusion',''),]
    return inp_list

def enum_sockets_up(self, context):
    if self.input_sockets not in [sock[0] for sock in propper.get_sockets_enum_items()]:
        self['input_sockets'] = 0
        return
    for line in p_lines():
        if line.split_rgb:
            for sock in line.channels.socket:
                if sock.input_sockets in self.input_sockets and not 'no_socket' in self.input_sockets and line.auto_mode:
                    try:
                        sock['input_sockets'] = 0
                        line.auto_mode = False
                    except:
                        print(f'cannot assign {[sock[0].replace(" ", "").lower() for sock in propper.get_sockets_enum_items()][0]} to {sock.name}, keeping as {sock.input_sockets}')
        else:
            if line.input_sockets in self.input_sockets and not 'no_socket' in self.input_sockets and not line == self and line.auto_mode:
                try:
                    line['input_sockets'] = 0
                    line.auto_mode = False
                except:
                    print(f'cannot assign {[sock[0].replace(" ", "").lower() for sock in propper.get_sockets_enum_items()][0]} to {line.name}, keeping as {line.input_sockets}')
    #context.view_layer.update()

def ch_sockets_up(self, context):
    for line in p_lines():
        if line.split_rgb:
            for sock in line.channels.socket:
                if sock.input_sockets in self.input_sockets and not 'no_socket' in self.input_sockets and not self == sock and line.auto_mode:
                    try:
                        setattr(sock,'input_sockets', 'no_socket')
                        line.auto_mode = False
                    except:
                        print(f'cannot assign {[sock[0].replace(" ", "").lower() for sock in propper.get_sockets_enum_items()][0]} to {sock.name}, keeping as {sock.input_sockets}')
        else:
            if line.input_sockets in self.input_sockets and not 'no_socket' in self.input_sockets and line.auto_mode:
                try:
                    setattr(line,'input_sockets', 'no_socket')
                    line.auto_mode = False
                except:
                    print(f'cannot assign {[sock[0].replace(" ", "").lower() for sock in propper.get_sockets_enum_items()][0]} to {line.name}, keeping as {line.input_sockets}')
    context.view_layer.update()

def line_name_up(self, context):
    if not self.manual:
        ndh.detect_a_map(self)

def shaders_list_cb(self, context):
    return propper.get_shaders_list()

def shaders_list_up(self, context):
    if self.replace_shader:
        propper.guess_sockets()
    context.view_layer.update()

def manual_up(self, context):
    if self.manual:
        props().target = 'active_obj'
        props().only_active_mat = True
    else:
        ndh.detect_a_map(self)

def advanced_mode_up(self, context):
    propper.refresh_shader_links()
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
    if self.include_ngroups:
        node_links().clear()
        include_ngroups_up(self,context)
    propper.guess_sockets()
    context.view_layer.update()

def dup_mat_compatible_up(self,context):
    ndh.detect_relevant_maps()

def clear_nodes_up(self, context):
    if self.clear_nodes:
        self.replace_shader = True

def auto_mode_up(self,context):
    if self.auto_mode:
        propper.default_sockets(self)

def only_active_mat_up(self, context):
    if "all_materials" in self.target and self.only_active_mat:
        self.target = "selected_objects"
    propper.refresh_shader_links()

def replace_shader_up(self, context):
    propper.set_enum_sockets_items()
    if self.include_ngroups:
        node_links().clear()
        include_ngroups_up(self,context)
    propper.safe_refresh()
    propper.guess_sockets()
    context.view_layer.update()

class ShaderLinks(PropertyGroup):

    ID: IntProperty(
        name="ID",
        default=0
    )
    name: StringProperty(
        name="named",
        default="Principled BSDF"
    )
    shadertype: StringProperty(
        name="internal name",
        default='ShaderNodeBsdfPrincipled'
    )
    input_sockets: StringProperty(
        name="",
        description="Shader input sockets for this texture node",
        default='{"0": "Base Color", "1": "Metallic", "2": "Roughness", "3": "IOR", "4": "Alpha", "5": "Normal", "6": "Diffuse Roughness", "7": "Subsurface Weight", "8": "Subsurface Radius", "9": "Subsurface Scale", "10": "Subsurface IOR", "11": "Subsurface Anisotropy", "12": "Specular IOR Level", "13": "Specular Tint", "14": "Anisotropic", "15": "Anisotropic Rotation", "16": "Tangent", "17": "Transmission Weight", "18": "Coat Weight", "19": "Coat Roughness", "20": "Coat IOR", "21": "Coat Tint", "22": "Coat Normal", "23": "Sheen Weight", "24": "Sheen Roughness", "25": "Sheen Tint", "26": "Emission Color", "27": "Emission Strength", "28": "Thin Film Thickness", "29": "Thin Film IOR"}'
    )
    outputsockets: StringProperty(
        name="lint of output sockets",
        default='{"0": "BSDF"}'
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


class StmProps(PropertyGroup):

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
    mode_opengl: BoolProperty(
        name="OpenGL Normals",
        description=" Disable to use DirectX™ normal map format instead of OpenGL.\
                        \n\
                        \n When this option is disabled, the script inverts the Y channel\
                        \n of the normal map to match blender format by adding a RGBCurve\
                        \n node with the green channel curve inverted before a normal map\
                        \n is plugged during Nodes Trees setup",
        default=True
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
        name="all_settings",
        description="Json string of all settings, used internally for preset saving",
        default="{'0':'0'}"
    )
    sockets: StringProperty(
        name="all_inputs",
        description="Json string of all inputs sockets, used internally for preset saving",
        default='{"0": "Base Color", "1": "Metallic", "2": "Roughness", "3": "IOR", "4": "Alpha", "5": "Normal", "6": "Diffuse Roughness", "7": "Subsurface Weight", "8": "Subsurface Radius", "9": "Subsurface Scale", "10": "Subsurface IOR", "11": "Subsurface Anisotropy", "12": "Specular IOR Level", "13": "Specular Tint", "14": "Anisotropic", "15": "Anisotropic Rotation", "16": "Tangent", "17": "Transmission Weight", "18": "Coat Weight", "19": "Coat Roughness", "20": "Coat IOR", "21": "Coat Tint", "22": "Coat Normal", "23": "Sheen Weight", "24": "Sheen Roughness", "25": "Sheen Tint", "26": "Emission Color", "27": "Emission Strength", "28": "Thin Film Thickness", "29": "Thin Film IOR"}'
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
    custom_preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset.",
        default="New Preset"
    )
    custom_preset_enum: EnumProperty(name="Presets",items=get_presets,update=custom_preset_enum_up)
