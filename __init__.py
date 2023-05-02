bl_info = {
    "name": "Blender Substance Texture Importer",
    "author": "Cosmin Planchon",
    "version": (0, 3, 1),
    "blender": (3, 1, 2),
    "location": "Properties > Material",
    "description": "Import & autoassign images from Substance Painter or similar 3D painting tools",
    "warning": "",
    "wiki_url": "https://github.com/Kos-Design/materials_substance/blob/main/readme.rst",
    "tracker_url": "https://github.com/Kos-Design/materials_substance/issues",
    "category": "Material"}

import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty,FloatVectorProperty,
    EnumProperty, 
)

from . propertygroups import ( PaneLine0, PaneLine1, PaneLine2, PaneLine3,
                            PaneLine4, PaneLine5, PaneLine6, PaneLine7,
                            PaneLine8, PaneLine9, ShaderLinks,
                            NodesLinks, BSMprops,
                            )

from . operators import ( BSM_MT_presetsmenu, BSM_OT_execute_preset,
                          BSM_OT_make_nodes, BSM_OT_assign_nodes,
                          BSM_OT_reporter,
                          BSM_OT_save_all, BSM_OT_load_all,
                          BSM_OT_import_textures, BSM_OT_del_map_line,
                          BSM_OT_add_preset,
                          BSM_OT_add_map_line,
                          )

from . panels import (  BSM_PT_presets, BSM_PT_importpanel, BSM_PT_panel_line,
                        BSM_PT_prefs, BSM_PT_options, BSM_PT_params, BSM_PT_buttons,
                        )

classes = (
    BSMprops,
    NodesLinks,
    ShaderLinks,
    PaneLine0,
    PaneLine1,
    PaneLine2,
    PaneLine3,
    PaneLine4,
    PaneLine5,
    PaneLine6,
    PaneLine7,
    PaneLine8,
    PaneLine9,
    BSM_OT_reporter,
    BSM_OT_add_map_line,
    BSM_OT_execute_preset,
    BSM_OT_make_nodes,
    BSM_MT_presetsmenu,
    BSM_OT_add_preset,
    BSM_PT_presets,
    BSM_OT_import_textures,
    BSM_PT_importpanel,
    BSM_PT_params,
    BSM_PT_panel_line,
    BSM_PT_prefs,
    BSM_PT_buttons,
    BSM_PT_options,
    BSM_OT_del_map_line,
    BSM_OT_save_all,
    BSM_OT_load_all,
    BSM_OT_assign_nodes,
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.bsmprops = PointerProperty(type=BSMprops)
    for i in range(10) :
        exec(f"bpy.types.Scene.panel_line{i} = PointerProperty(type=PaneLine{i})")
    bpy.types.Scene.node_links = CollectionProperty(type=NodesLinks)
    bpy.types.Scene.shader_links = CollectionProperty(type=ShaderLinks)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    del bpy.types.Scene.shader_links
    del bpy.types.Scene.node_links
    for i in range(10) :
        exec(f"del bpy.types.Scene.panel_line{9-i}")
    del bpy.types.Scene.bsmprops

if __name__ == '__main__':
    register()
