bl_info = {
    "name": "Substance Textures Importer",
    "author": "Cosmin Planchon",
    "version": (0, 6, 0),
    "blender": (4, 0, 0),
    "location": "Shader editor > Sidebar > STM",
    "description": "Import & autoassign images from Substance Painter or similar 3D painting tools",
    "warning": "",
    "wiki_url": "https://github.com/Kos-Design/substance_textures_importer/blob/main/readme.rst",
    "tracker_url": "https://github.com/Kos-Design/substance_textures_importer/issues",
    "category": "Node"}

import bpy
from bpy.app.handlers import persistent
from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty,FloatVectorProperty,
    EnumProperty,
)

from . propertygroups import ( ShaderLinks, NodesLinks,ChannelSocket,
                                ChannelSockets, PanelLines,
                                PanelLiner,  StmProps
                            )

from . operators import ( NODE_OT_stm_execute_preset,
                          NODE_OT_stm_make_nodes, NODE_OT_stm_assign_nodes,
                          NODE_OT_stm_add_substance_texture,NODE_OT_stm_delete_preset,NODE_OT_stm_presets_dialog,
                          NODE_OT_stm_import_textures,
                          NODE_OT_stm_add_preset,NODE_OT_stm_del_substance_texture,
                          )

from . panels import (  NODE_PT_stm_presets, NODE_PT_stm_importpanel, NODE_PT_stm_panel_liner,WORKAROUND_UL_List,
                        NODE_PT_stm_prefs, NODE_PT_stm_options, NODE_PT_stm_params, NODE_PT_stm_buttons
                        )

classes = (
    ChannelSocket,
    ChannelSockets,
    PanelLines,
    PanelLiner,
    StmProps,
    NodesLinks,
    ShaderLinks,
    NODE_OT_stm_execute_preset,
    NODE_OT_stm_make_nodes,
    NODE_OT_stm_presets_dialog,
    NODE_OT_stm_add_preset,
    NODE_PT_stm_presets,
    WORKAROUND_UL_List,
    NODE_OT_stm_import_textures,
    NODE_OT_stm_delete_preset,
    NODE_OT_stm_add_substance_texture,
    NODE_OT_stm_del_substance_texture,
    NODE_PT_stm_importpanel,
    NODE_PT_stm_params,
    NODE_PT_stm_panel_liner,
    NODE_PT_stm_prefs,
    NODE_PT_stm_buttons,
    NODE_PT_stm_options,
    NODE_OT_stm_assign_nodes,
    )


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.stm_props = PointerProperty(type=StmProps)
    bpy.types.Scene.node_links = CollectionProperty(type=NodesLinks)
    bpy.types.Scene.shader_links = CollectionProperty(type=ShaderLinks)

def unregister():
    from bpy.utils import unregister_class
    del bpy.types.Scene.shader_links
    del bpy.types.Scene.node_links
    del bpy.types.Scene.stm_props
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
