import bpy
from pathlib import Path

from bpy.types import (
    Panel, Menu, AddonPreferences, PropertyGroup,
    UIList, WindowManager, Scene
)

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
    preset_add_operator = 'bsm.addpreset'


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
        scene = bpy.context.scene
        bsmprops = scene.bsmprops
        row = layout.row()
        row.prop(bsmprops, "usr_dir")


class BSM_PT_linestopanel(TexImporterPanel, Panel):
    bl_idname = "BSM_PT_linestopanel"
    bl_label = "Texture maps"
    bl_parent_id = "BSM_PT_importpanel"
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        bsmprops = scene.bsmprops
        advanced_modemode = bsmprops.advanced_mode
        panel_rows = bsmprops.panel_rows
        #TODO: no globbing in panel, get it propped
        dir_content = [x.name for x in Path(bsmprops.usr_dir).glob('*.*') ]
        row = layout.row()
        col = row.column()
        col.alignment = 'RIGHT'
        row = col.row()
        row.alignment = 'RIGHT'
        row.operator("BSM_OT_addaline", icon="ADD")
        row.separator()
        row = layout.row(align=True)
        row = row.split(factor=.02)
        row.label(text=" " )
        row.use_property_split = True
        row.use_property_decorate = False
        row = row.split(factor=.35)
        col = row.column(align=True)
        col.label(text="Map name")
        row = row.split(factor=.15)
        col = row.column(align=True)
        if not advanced_modemode:
            col.label(text=" " )
        else :

            col.label(text=" " )

        row = row.split(factor=.33)
        col = row.column(align=True)
        col.label(text="Ext.")
        row = row.split(factor=.97)
        col = row.column()
        col.label(text="Sockets")
        row.separator()
        row = layout.row()
        
        for k in range(panel_rows):
            panel_line = eval(f"scene.panel_line{k}")
            file_name = panel_line.file_name
            manual = panel_line.manual
            lefile = Path(panel_line.probable).name
            
            if manual:
                lefile = Path(file_name).name
                dir_content = bsmprops.dir_content

            row = layout.row(align = True)
            row.prop(panel_line, "line_on", text = "")
            row.use_property_split = True
            row.use_property_decorate = False
            row = row.split(factor = .35)
            row.active = panel_line.line_on
            row.enabled = panel_line.line_on
            row.alignment = 'LEFT'
            col = row.column(align=True)
            if manual :
                col.prop(panel_line, "file_name", text = "")
            else:
                col.prop(panel_line, "map_label", text = "")
            row = row.split(factor = .11)
            row.alignment = 'EXPAND'
            col = row.column(align = True)
            col.alignment = 'EXPAND'
            if not advanced_modemode:
                if lefile in dir_content:
                    col.operator('BSM_OT_namechecker', icon='CHECKMARK').linen = k
                else:
                    col.operator('BSM_OT_namechecker', icon='QUESTION').linen = k
            else :

                col.prop(panel_line, "manual", text="", toggle=1, icon='FILE_TICK')
            row = row.split(factor=.33)
            row.alignment = 'LEFT'
            col = row.column(align=True)
            col.alignment = 'LEFT'
            col.enabled = not manual
            col.prop(panel_line, "map_ext", text="")
            row = row.split(factor=.97)
            col = row.column()
            col.enabled = panel_line.line_on
            if not col.active :
                col.prop(bsmprops, "enum_placeholder" , text="")
            else:
                col.prop(panel_line, "input_sockets" , text="")
            row.separator()
        row = layout.row()


class BSM_PT_prefs(TexImporterPanel,Panel):

    bl_idname = "BSM_PT_prefs"
    bl_label = "Preferences"
    bl_parent_id = "BSM_PT_importpanel"
    bl_options = {'DEFAULT_CLOSED',}

    def draw_header_preset(self, _context):
        layout = self.layout
        row = layout.row()
        row = row.split(factor=.95)
        row.operator("BSM_OT_removeline", icon="REMOVE",)


    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        bsmprops = scene.bsmprops
        row = layout.row()
        row.alignment = 'LEFT'
        row.split(factor=1, align = True)
        row.prop(bsmprops, "prefix", text="Prefix")
        row.split(factor=.1)
        row.split(factor=.1)
        row.prop(bsmprops, "separator", text="Separator")
        box = layout.box()
        row = box.row()
        row.label(text="Pattern of the files in the Maps Folder : ")
        row = box.row()
        row.prop(bsmprops, "patterns", text="")
        row = layout.row()
        row.prop(bsmprops, "advanced_mode", text="Advanced Mode ", )


class BSM_PT_buttons(TexImporterPanel, Panel):

    bl_idname = "BSM_PT_buttons"
    bl_label = "Options"
    bl_parent_id = "BSM_PT_importpanel"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column(align = True)
        col.operator("BSM_OT_subimport")
        col.separator()

        row = col.row(align = True)
        col = layout.column(align = True)
        row = col.row(align = True)
        row.operator("BSM_OT_assignnodes")
        row.separator()
        row.operator("BSM_OT_createnodes")


class BSM_PT_options(TexImporterPanel, Panel):

    bl_idname = "BSM_PT_options"
    bl_label = "Options"
    bl_parent_id = "BSM_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        bsmprops = bpy.context.scene.bsmprops
        row = layout.row()
        col = row.column(align = True)
        row = col.row(align = True)
        row.prop(bsmprops, "shader", text="Replace Shader",)
        row = row.split()
        row.prop(bsmprops, "shaders_list", text="")
        row = layout.row()
        row = layout.row()
        row.enabled = not bsmprops.manual_on
        row.prop(bsmprops, "apply_to_all", text="Apply to all visible objects", )
        row = layout.row()
        row.enabled = not bsmprops.manual_on
        row.prop(bsmprops, "only_active_obj", text="Apply to active object only", )
        row = layout.row()
        row.prop(bsmprops, "skip_normals", )
        row = layout.row()
        row.prop(bsmprops, "custom_shader_on", text="Enable Custom Shaders", icon='NONE', icon_only=True)
        row = layout.row()
        row.prop(bsmprops, "eraseall", text="Clear nodes from material", )
        row = layout.row()
        row.prop(bsmprops, "tweak_levels", text="Attach Curves and Ramps ", )
        row = layout.row()
        row.enabled = not bsmprops.manual_on
        row.prop(bsmprops, "only_active_mat", text="Only active Material",)
        row = layout.row()
        row.prop(bsmprops, "fix_name", text="Fix copied Material name",)
