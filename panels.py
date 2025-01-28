import bpy

from bpy.types import Panel

from bl_ui.utils import PresetPanel

class TexImporterPanel():
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    @classmethod
    def poll(cls, context):
        if context.object is not None :
            if context.object.active_material is not None:
                return True
        return False


class BSM_PT_presets(PresetPanel, Panel):
    bl_label = 'Presets'
    preset_subdir = 'bsm_presets'
    preset_operator = 'bsm.execute_preset'
    preset_add_operator = 'bsm.add_preset'


class BSM_PT_importpanel(TexImporterPanel, Panel):
    bl_idname = "BSM_PT_importpanel"
    bl_label = "Substance Texture Importer"

    def draw_header_preset(self, _context):
        layout = self.layout
        BSM_PT_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout


class BSM_PT_params(TexImporterPanel, Panel):

    bl_idname = "BSM_PT_params"
    bl_label = "Maps Folder:"
    bl_parent_id = "BSM_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene.bsmprops, "usr_dir")

class BSM_PT_panel_liner(TexImporterPanel,Panel):
    bl_label = "Textures:"
    bl_idname = "BSM_PT_substance_texture_importer"
    bl_parent_id = "BSM_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.bsmprops
        texture_importer = props.texture_importer
        row = layout.row()
        row.template_list(
            "UI_UL_list", "Textures",
            texture_importer, "textures",
            texture_importer, "texture_index",
        )

        col = row.column(align=True)
        col.operator("bsm.add_item", icon="ADD", text="")
        col.operator("bsm.remove_item", icon="REMOVE", text="")

        if texture_importer.textures and texture_importer.texture_index < len(texture_importer.textures):
            item = texture_importer.textures[texture_importer.texture_index]
            layout.prop(item, "line_on")
            sub_layout = layout.column()  # Or layout.box() for a bordered box
            sub_layout.enabled = item.line_on  # Disable all UI elements within this group if line_on is False
            sub_layout.prop(item, "map_label")
            if props.advanced_mode :
                sub_sub_layout = sub_layout.column()
                sub_sub_layout.prop(item, "manual")
                if item.manual :
                    sub_sub_sub_layout = sub_sub_layout.column()
                    sub_sub_sub_layout.prop(item, "file_name")
            sub_layout.prop(item, "input_sockets")

class BSM_PT_prefs(TexImporterPanel,Panel):

    bl_idname = "BSM_PT_prefs"
    bl_label = ""
    bl_parent_id = "BSM_PT_importpanel"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(context.scene.bsmprops, "advanced_mode", text="Manual Mode ", )


class BSM_PT_buttons(TexImporterPanel, Panel):

    bl_idname = "BSM_PT_buttons"
    bl_label = "Options"
    bl_parent_id = "BSM_PT_importpanel"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column(align = True)
        col.operator("bsm.import_textures")
        col.separator()
        row = col.row(align = True)
        col = layout.column(align = True)
        row = col.row(align = True)
        row.operator("bsm.assign_nodes")
        row.separator()
        ops = row.operator("bsm.make_nodes")


class BSM_PT_options(TexImporterPanel, Panel):

    bl_idname = "BSM_PT_options"
    bl_label = "Options"
    bl_parent_id = "BSM_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        bsmprops = context.scene.bsmprops
        row = layout.row()
        col = row.column(align = True)
        row = col.row(align = True)
        row.prop(bsmprops, "replace_shader", text="Replace Shader",)
        row = row.split()
        row.prop(bsmprops, "shaders_list", text="")
        row = layout.row()
        row = layout.row()
        row.prop(bsmprops, "apply_to_all", text="Apply to all visible objects", )
        row = layout.row()
        row.prop(bsmprops, "only_active_obj", text="Apply to active object only", )
        row = layout.row()
        row.prop(bsmprops, "skip_normals", )
        row = layout.row()
        row.prop(bsmprops, "include_ngroups", text="Enable Custom Shaders", icon='NONE', icon_only=True)
        row = layout.row()
        row.prop(bsmprops, "clear_nodes", text="Clear nodes from material", )
        row = layout.row()
        row.prop(bsmprops, "tweak_levels", text="Attach Curves and Ramps ", )
        row = layout.row()
        row.prop(bsmprops, "only_active_mat", text="Only active Material",)
        row = layout.row()
        row.prop(bsmprops, "dup_mat_compatible", text="Duplicated material compatibility",)
        row = layout.row()
        row.separator()
