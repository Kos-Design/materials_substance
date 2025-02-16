import bpy

from bpy.props import (StringProperty, IntProperty, BoolProperty,PointerProperty, CollectionProperty,EnumProperty)

from bpy.types import (PropertyGroup, UIList,AddonPreferences)

from . propertieshandler import PropertiesHandler, set_wish

from . propertygroups import StmProps, enum_sockets_cb, auto_mode_up, ch_sockets_up, enum_sockets_up, manual_up, split_rgb_up, line_on_up, NodesLinks, ShaderLinks

propper = PropertiesHandler()

def get_name_up(self):
    return self.get("name","")

def set_name_up(self, value):
    self["name"] = value
    try:
        if (self.auto_mode and not self.manual) or self.split_rgb:
            propper.default_sockets(self)
            if self.split_rgb :
                ch_sockets_up(self,bpy.context)
            elif self.auto_mode:
                enum_sockets_up(self,bpy.context)
        propper.wish = set_wish()
    except AttributeError:
        print(f"error during sockets update {self.wish}" )

def init_prefs():
    prefs = bpy.context.preferences.addons[__package__].preferences
    if len(prefs.shader_links) == 0:
        prefs.shader_links.add()
    if len(prefs.maps.textures) == 0:
        maps = ["Color","Roughness","Metallic","Normal"]
        for i in range(4):
            item = prefs.maps.textures.add()
            item.name = f"{maps[i]}"
            item.input_sockets = f"{'' if i else 'Base '}{maps[i]}"
            propper.make_clean_channels(item)

class StmChannelSocket(PropertyGroup):
    input_sockets: EnumProperty(
        name="Input socket",
        description="Target shader input sockets for this texture node.\
                    \n Selected automaticaly if -Detect target socket- is enabled",
        items=enum_sockets_cb,
        update=ch_sockets_up
    )
    line_name: StringProperty(
        name="Color",
        description="name of the line owning this instance",
        default="Select a name"
    )


class StmChannelSockets(PropertyGroup):
    socket: CollectionProperty(type=StmChannelSocket)
    sockets_index: IntProperty(default=0)
    line_name: StringProperty(
        name="Color",
        description="name of the line owning this instance",
        default="Select a name"
    )


class StmPanelLines(PropertyGroup):
    name: StringProperty(
        name="name",
        description="Keyword identifier of the texture map to import",
        get=get_name_up,
        set=set_name_up
    )

    channels: PointerProperty(type=StmChannelSockets)

    file_name: StringProperty(
        name="File",
        subtype='FILE_PATH',
        description="Complete filepath of the texture map",
        default="Select a file"
    )
    auto_mode: BoolProperty(
        name="Detect target socket",
        description="Auto detect target shader socket",
        default=True,
        update=auto_mode_up
    )
    input_sockets: EnumProperty(
        name="",
        description="Target shader input sockets for this texture node.\
                    \n Selected automaticaly if Autodetect sockets is enabled",
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


class StmPanelLiner(PropertyGroup):
    textures: CollectionProperty(type=StmPanelLines)
    texture_index: IntProperty(default=0)


class StmNodes(PropertyGroup):
    node_links: CollectionProperty(type=NodesLinks)
    node_index: IntProperty(default=0)


class StmShaders(PropertyGroup):
    shader_links: CollectionProperty(type=ShaderLinks)
    shader_index: IntProperty(default=0)


class NODE_UL_stm_list(UIList):
    """
    Same behaviour as normal UI list but this workaround allows the triggering
    of an update function when changing item names in UI Panel by double-clicking on it,
    whereas normal UI lists do not!
    --could be a candidate for a bugreport--
    """
    bl_idname = "NODE_UL_stm_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item:
            layout.prop(item, "name", text="", emboss=False, icon=f"SEQUENCE_COLOR_0{((index+3)%9+1)}")


class StmAddonPreferences(AddonPreferences):
    bl_idname = __package__ if __package__ else __name__

    maps: bpy.props.PointerProperty(type=StmPanelLiner)
    node_links: CollectionProperty(type=NodesLinks)
    shader_links: CollectionProperty(type=ShaderLinks)
    display_in_shadernodes_editor: BoolProperty(default=True,description="uncheck this option to not display the Extension panel in the Shader Nodes Editor Sidebar. It will remain accessible via the File > Import > Substance Textures menu ")
    props: bpy.props.PointerProperty(type=StmProps)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Default maps:")
        row = layout.row()
        row.template_list(
            "NODE_UL_stm_list", "Textures",
            self.maps, "textures",
            self.maps, "texture_index",
            type="GRID",
            columns=4,
        )
        button_col = row.column(align=True)
        button_col.operator("node.stm_add_item", icon="ADD", text="")
        button_col.operator("node.stm_remove_item", icon="REMOVE", text="")
        button_col.separator(factor=3)

        button_col.operator("node.stm_reset_substance_textures", icon="FILE_REFRESH", text="")
        layout.prop(self,'display_in_shadernodes_editor',text="Display Panel in Shader Nodes Editor")
