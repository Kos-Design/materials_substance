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

from . propertygroups import ( ShaderLinks, NodesLinks, StmProps )

from . operators import ( NODE_OT_stm_execute_preset,NODE_OT_stm_reset_substance_textures,
                          NODE_OT_stm_make_nodes, NODE_OT_stm_assign_nodes,
                          NODE_OT_stm_add_substance_texture,NODE_OT_stm_delete_preset,NODE_OT_stm_presets_dialog,
                          NODE_OT_stm_import_textures,
                          NODE_OT_stm_add_preset,NODE_OT_stm_del_substance_texture,
                          )

from . panels import (  NODE_PT_stm_presets, NODE_PT_stm_importpanel, NODE_PT_stm_panel_liner,
                        NODE_PT_stm_prefs, NODE_PT_stm_options, NODE_PT_stm_params, NODE_PT_stm_buttons,
                        )
from . propertieshandler import shader_links, node_links
from . preferences import (StmAddonPreferences, StmPanelLiner, NODE_UL_stm_list, StmPanelLines,
                             StmChannelSocket, StmChannelSockets,StmShaders, StmNodes)

classes = (
    StmProps,
    NodesLinks,
    ShaderLinks,
    StmShaders,
    StmNodes,
    NODE_OT_stm_execute_preset,
    NODE_OT_stm_make_nodes,
    NODE_OT_stm_presets_dialog,
    NODE_OT_stm_add_preset,
    NODE_PT_stm_presets,
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
    StmChannelSocket,
    StmChannelSockets,
    StmPanelLines,
    StmPanelLiner,
    StmAddonPreferences,
    NODE_UL_stm_list,
    NODE_OT_stm_reset_substance_textures,
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.stm_props = PointerProperty(type=StmProps)
    prefs = bpy.context.preferences.addons[__package__].preferences
    if not len(prefs.shader_links):
        prefs.shader_links.add()
    if not len(prefs.maps.textures):
        maps = ["Color","Roughness","Metallic","Normal"]
        for i in range(4):
            item = prefs.maps.textures.add()
            item.name = f"{maps[i]}"
            item.input_sockets = f"{'' if i else 'Base '}{maps[i]}"

def unregister():
    from bpy.utils import unregister_class
    del bpy.types.Scene.stm_props
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
