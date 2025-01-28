bl_info = {
    "name": "Substance Texture Importer",
    "author": "Cosmin Planchon",
    "version": (0, 5, 0),
    "blender": (4, 0, 0),
    "location": "Properties > Material",
    "description": "Import & autoassign images from Substance Painter or similar 3D painting tools",
    "warning": "",
    "wiki_url": "https://github.com/Kos-Design/materials_substance/blob/main/readme.rst",
    "tracker_url": "https://github.com/Kos-Design/materials_substance/issues",
    "category": "Material"}

import bpy
from bpy.app.handlers import persistent
from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty,FloatVectorProperty,
    EnumProperty,
)

from . propertygroups import ( ShaderLinks, NodesLinks, BSMprops,
                             PanelLines, PanelLiner, ph
                            )

from . operators import ( BSM_MT_presetsmenu, BSM_OT_execute_preset,
                          BSM_OT_make_nodes, BSM_OT_assign_nodes,
                          BSM_OT_reporter,BSM_OT_add_substance_texture,
                          BSM_OT_save_all, BSM_OT_load_all,
                          BSM_OT_import_textures,
                          BSM_OT_add_preset,BSM_OT_del_substance_texture,
                          )

from . panels import (  BSM_PT_presets, BSM_PT_importpanel, BSM_PT_panel_liner,
                        BSM_PT_prefs, BSM_PT_options, BSM_PT_params, BSM_PT_buttons,
                        )

classes = (
    PanelLines,
    PanelLiner,
    BSMprops,
    NodesLinks,
    ShaderLinks,
    BSM_OT_reporter,
    BSM_OT_execute_preset,
    BSM_OT_make_nodes,
    BSM_MT_presetsmenu,
    BSM_OT_add_preset,
    BSM_PT_presets,
    BSM_OT_import_textures,
    BSM_OT_add_substance_texture,
    BSM_OT_del_substance_texture,
    BSM_PT_importpanel,
    BSM_PT_params,
    BSM_PT_panel_liner,
    BSM_PT_prefs,
    BSM_PT_buttons,
    BSM_PT_options,
    BSM_OT_save_all,
    BSM_OT_load_all,
    BSM_OT_assign_nodes,
    )


@persistent
def initialize_defaults(arg_1,arg_2):
    props = bpy.context.scene.bsmprops
    if hasattr(props, "texture_importer"):
        maps = ["Color","Roughness","Metallic","Normal"]
        texture_importer = props.texture_importer
        if len(texture_importer.textures) == 0:
            propper = ph()
            for i in range(4):
                item = texture_importer.textures.add()
                item.name = f"{maps[i]} map"
                item.map_label = f"{maps[i]}"
                propper.default_sockets(bpy.context,item)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.bsmprops = PointerProperty(type=BSMprops)
    bpy.types.Scene.node_links = CollectionProperty(type=NodesLinks)
    bpy.types.Scene.shader_links = CollectionProperty(type=ShaderLinks)
    bpy.app.handlers.load_post.append(initialize_defaults)

def unregister():
    from bpy.utils import unregister_class
    bpy.app.handlers.load_post.remove(initialize_defaults)
    del bpy.types.Scene.shader_links
    del bpy.types.Scene.node_links
    del bpy.types.Scene.bsmprops
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
