bl_info = {
    "name": "Blender Substance Texture Importer",
    "author": "Cosmin Planchon",
    "version": (0, 2, 2),
    "blender": (2, 82, 0),
    "location": "Properties > Material",
    "description": "Import & autoassign images from Substance Painter or similar 3D painting tools",
    "warning": "",
    "wiki_url": "https://github.com/Kos-Design/materials_substance/wiki/Blender-Substance-Texture-Importer-Wiki",
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

from . operators import ( BSM_MT_presetsmenu, BsmExecutePreset,
                          BSM_OT_createnodes, BSM_OT_assignnodes,
                          BSM_OT_checkmaps, BSM_OT_assumename,
                          BSM_OT_createdummy,
                          BSM_OT_saveall, BSM_OT_loadall,
                          BSM_OT_subimport, BSM_OT_removeline,
                          BSM_OT_addpreset,
                          BSM_OT_addaline, BSM_OT_guessfilext,
                          )

from . panels import (  BSM_PT_presets, BSM_PT_importpanel, BSM_PT_linestopanel,
                        BSM_PT_prefs, BSM_PT_options, BSM_PT_params, BSM_PT_buttons,
                        )

classesp = (
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
    BSM_OT_addaline,
    BsmExecutePreset,
    BSM_OT_createdummy,
    BSM_OT_guessfilext,
    BSM_OT_assumename,
    BSM_OT_checkmaps,
    BSM_OT_createnodes,
    BSM_MT_presetsmenu,
    BSM_OT_addpreset,
    BSM_PT_presets,
    BSM_OT_subimport,
    BSM_PT_importpanel,
    BSM_PT_params,
    BSM_PT_linestopanel,
    BSM_PT_prefs,
    BSM_PT_buttons,
    BSM_PT_options,
    BSM_OT_removeline,
    BSM_OT_saveall,
    BSM_OT_loadall,
    BSM_OT_assignnodes,
    )

def register():
    from bpy.utils import register_class
    for cls in classesp:
        register_class(cls)
   
    bpy.types.Scene.bsmprops = PointerProperty(type=BSMprops)
    bpy.types.Scene.panel_line0 = PointerProperty(type=PaneLine0)
    bpy.types.Scene.panel_line1 = PointerProperty(type=PaneLine1)
    bpy.types.Scene.panel_line2 = PointerProperty(type=PaneLine2)
    bpy.types.Scene.panel_line3 = PointerProperty(type=PaneLine3)
    bpy.types.Scene.panel_line4 = PointerProperty(type=PaneLine4)
    bpy.types.Scene.panel_line5 = PointerProperty(type=PaneLine5)
    bpy.types.Scene.panel_line6 = PointerProperty(type=PaneLine6)
    bpy.types.Scene.panel_line7 = PointerProperty(type=PaneLine7)
    bpy.types.Scene.panel_line8 = PointerProperty(type=PaneLine8)
    bpy.types.Scene.panel_line9 = PointerProperty(type=PaneLine9)
    bpy.types.Scene.node_links = CollectionProperty(type=NodesLinks)
    bpy.types.Scene.shader_links = CollectionProperty(type=ShaderLinks)

def unregister():
    from bpy.utils import unregister_class
    for cls in classesp:
        unregister_class(cls)
    del bpy.types.Scene.shader_links
    del bpy.types.Scene.node_links
    del bpy.types.Scene.panel_line9
    del bpy.types.Scene.panel_line8
    del bpy.types.Scene.panel_line7
    del bpy.types.Scene.panel_line6
    del bpy.types.Scene.panel_line5
    del bpy.types.Scene.panel_line4
    del bpy.types.Scene.panel_line3
    del bpy.types.Scene.panel_line2
    del bpy.types.Scene.panel_line1
    del bpy.types.Scene.panel_line0
    del bpy.types.Scene.bsmprops

if __name__ == '__main__':
    register()
