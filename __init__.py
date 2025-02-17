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

from . propertygroups import ( ShaderLinks, NodesLinks, StmProps,register_msgbus,unregister_msgbus)

from . operators import ( NODE_OT_stm_execute_preset,NODE_OT_stm_reset_substance_textures,
                          NODE_OT_stm_make_nodes, NODE_OT_stm_assign_nodes,menu_func,NODE_OT_stm_move_line,
                          NODE_OT_stm_add_substance_texture,NODE_OT_stm_delete_preset,NODE_OT_stm_presets_dialog,
                          NODE_OT_stm_import_textures,IMPORT_OT_stm_window,NODE_OT_add_preset_popup,
                          NODE_OT_stm_add_preset,NODE_OT_stm_del_substance_texture,
                          )

from . panels import (  NODE_PT_stm_presets, NODE_PT_stm_importpanel, NODE_PT_stm_panel_liner,
                        NODE_PT_stm_prefs, NODE_PT_stm_options, NODE_PT_stm_params, NODE_PT_stm_buttons,
                        )

from . preferences import (StmAddonPreferences, StmPanelLiner, NODE_UL_stm_list, StmPanelLines,init_prefs,
                             StmChannelSocket, StmChannelSockets,StmShaders, StmNodes,)

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
    NODE_OT_add_preset_popup,
    StmAddonPreferences,
    NODE_UL_stm_list,
    IMPORT_OT_stm_window,
    NODE_OT_stm_reset_substance_textures,
    NODE_OT_stm_move_line
    )


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    init_prefs()
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    register_msgbus()

def unregister():
    from bpy.utils import unregister_class
    unregister_msgbus()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
