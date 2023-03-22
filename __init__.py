bl_info = {
    "name": "Blender Substance Texture Importer",
    "author": "Cosmin Planchon",
    "version": (0, 2, 0),
    "blender": (2, 82, 0),
    "location": "Properties > Material",
    "description": "Import & autoassign images from Substance Painter or similar 3D painting tools",
    "warning": "",
    "wiki_url": "https://github.com/Kos-Design/materials_substance/wiki/Blender-Substance-Texture-Importer-Wiki",
    "tracker_url": "https://github.com/Kos-Design/materials_substance/issues",
    "category": "Material"}

import bpy
import importlib

from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty,FloatVectorProperty,
    EnumProperty,
)

from . import PropertyGroups

from . import Operators

from . import Panels

importlib.reload(PropertyGroups)

importlib.reload(Operators)

importlib.reload(Panels)

from . PropertyGroups import ( Paneline0, Paneline1, Paneline2, Paneline3,
                            Paneline4, Paneline5, Paneline6, Paneline7,
                            Paneline8, Paneline9,  ShaderLinks,
                            NodesLinks, KosVars,
                            )

from . Operators import ( KOS_MT_presetsmenu, KosExecutePreset,
                          KOS_OT_createnodes, KOS_OT_assignnodes,
                          KOS_OT_checkmaps, KOS_OT_assumename,
                          KOS_OT_createdummy,
                          KOS_OT_saveall, KOS_OT_loadall,
                          KOS_OT_subimport, KOS_OT_removeline,
                          KOS_OT_addpreset,
                          KOS_OT_addaline, KOS_OT_guessfilext,
                          )

from . Panels import (  KOS_PT_presets, KOS_PT_importpanel, KOS_PT_linestopanel,
                        KOS_PT_prefs, KOS_PT_options, KOS_PT_params, KOS_PT_buttons,
                        )

classesp = (
    KosVars,
    ShaderLinks,
    NodesLinks,
    Paneline0,
    Paneline1,
    Paneline2,
    Paneline3,
    Paneline4,
    Paneline5,
    Paneline6,
    Paneline7,
    Paneline8,
    Paneline9,
    KOS_OT_addaline,
    KosExecutePreset,
    KOS_OT_createdummy,
    KOS_OT_guessfilext,
    #KOS_OT_realinit,
    KOS_OT_assumename,
    KOS_OT_checkmaps,
    KOS_OT_createnodes,
    KOS_MT_presetsmenu,
    KOS_OT_addpreset,
    KOS_PT_presets,
    KOS_OT_subimport,
    KOS_PT_importpanel,
    KOS_PT_params,
    KOS_PT_linestopanel,
    KOS_PT_prefs,
    KOS_PT_buttons,
    KOS_PT_options,
    KOS_OT_removeline,
    KOS_OT_saveall,
    KOS_OT_loadall,
    KOS_OT_assignnodes,
    )

def register():
    from bpy.utils import register_class
    for cls in classesp:
        register_class(cls)

    bpy.types.Scene.kosvars = PointerProperty(type=KosVars)
    bpy.types.Scene.kosp0 = PointerProperty(type=Paneline0)
    bpy.types.Scene.kosp1 = PointerProperty(type=Paneline1)
    bpy.types.Scene.kosp2 = PointerProperty(type=Paneline2)
    bpy.types.Scene.kosp3 = PointerProperty(type=Paneline3)
    bpy.types.Scene.kosp4 = PointerProperty(type=Paneline4)
    bpy.types.Scene.kosp5 = PointerProperty(type=Paneline5)
    bpy.types.Scene.kosp6 = PointerProperty(type=Paneline6)
    bpy.types.Scene.kosp7 = PointerProperty(type=Paneline7)
    bpy.types.Scene.kosp8 = PointerProperty(type=Paneline8)
    bpy.types.Scene.kosp9 = PointerProperty(type=Paneline9)
    bpy.types.Scene.kosni = CollectionProperty(type=NodesLinks)
    bpy.types.Scene.koshi = CollectionProperty(type=ShaderLinks)

def unregister():
    from bpy.utils import unregister_class
    for cls in classesp:
        unregister_class(cls)
    del bpy.types.Scene.kosni
    del bpy.types.Scene.koshi
    del bpy.types.Scene.kosp0
    del bpy.types.Scene.kosp1
    del bpy.types.Scene.kosp2
    del bpy.types.Scene.kosp3
    del bpy.types.Scene.kosp4
    del bpy.types.Scene.kosp5
    del bpy.types.Scene.kosp6
    del bpy.types.Scene.kosp7
    del bpy.types.Scene.kosp8
    del bpy.types.Scene.kosp9
    del bpy.types.Scene.kosvars

if __name__ == '__main__':
    register()
