import bpy
import os

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


class KOS_PT_presets(PresetPanel, Panel):
    bl_label = 'Presets'
    preset_subdir = 'kospresets'
    preset_operator = 'kos.execute_preset'
    preset_add_operator = 'kos.addpreset'

class KOS_PT_importpanel(TexImporterPanel, Panel):
    bl_idname = "KOS_PT_importpanel"
    bl_label = "Substance Texture Importer"

    def draw_header_preset(self, _context):
        layout = self.layout
        KOS_PT_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout

class KOS_PT_params(TexImporterPanel, Panel):

    bl_idname = "KOS_PT_params"
    bl_label = "Maps Folder:"
    bl_parent_id = "KOS_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        kosvars = scene.kosvars
        row = layout.row()
        row.prop(kosvars, "kosdir")

class KOS_PT_linestopanel(TexImporterPanel, Panel):
    bl_idname = "KOS_PT_linestopanel"
    bl_label = "Texture maps"
    bl_parent_id = "KOS_PT_importpanel"
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        kosvars = scene.kosvars
        expertmode = kosvars.expert
        panelrows = kosvars.panelrows
        row = layout.row()
        col = row.column()
        col.alignment = 'RIGHT'
        row = col.row()
        row.alignment = 'RIGHT'
        row.operator("KOS_OT_addaline", icon="ADD")
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
        if not expertmode:
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

        for k in range(panelrows):
            kosp = eval(f"scene.kosp{k}")
            lefilename = kosp.lefilename
            manual = kosp.manual
            lefile = os.path.basename(kosp.probable)
            dircontent = os.listdir(kosvars.kosdir)
            if manual:
                lefile = os.path.basename(lefilename)
                dircontent = kosvars.dircontent

            row = layout.row(align = True)
            row.prop(kosp, "labelbools", text = "")
            row.use_property_split = True
            row.use_property_decorate = False
            row = row.split(factor = .35)
            row.active = kosp.labelbools
            row.enabled = kosp.labelbools
            row.alignment = 'LEFT'
            col = row.column(align=True)
            if manual :
                col.prop(kosp, "lefilename", text = "")
            else:
                col.prop(kosp, "maplabels", text = "")
            row = row.split(factor = .11)
            row.alignment = 'EXPAND'
            col = row.column(align = True)
            col.alignment = 'EXPAND'
            if not expertmode:
                if lefile in dircontent:
                    col.operator('KOS_OT_checkmaps', icon='CHECKMARK').linen = k
                else:
                    col.operator('KOS_OT_checkmaps', icon='QUESTION').linen = k
            else :

                col.prop(kosp, "manual", text="", toggle=1, icon='FILE_TICK')
            row = row.split(factor=.33)
            row.alignment = 'LEFT'
            col = row.column(align=True)
            col.alignment = 'LEFT'
            col.enabled = not manual
            col.prop(kosp, "mapext", text="")
            row = row.split(factor=.97)
            col = row.column()
            col.enabled = kosp.labelbools
            if not col.active :
                col.prop(kosvars, "emptylist" , text="")
            else:
                col.prop(kosp, "inputsockets" , text="")
            row.separator()
        row = layout.row()

class KOS_PT_prefs(TexImporterPanel,Panel):

    bl_idname = "KOS_PT_prefs"
    bl_label = "Preferences"
    bl_parent_id = "KOS_PT_importpanel"
    bl_options = {'DEFAULT_CLOSED',}

    def draw_header_preset(self, _context):
        layout = self.layout
        row = layout.row()
        row = row.split(factor=.95)
        row.operator("KOS_OT_removeline", icon="REMOVE",)


    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        kosvars = scene.kosvars
        row = layout.row()
        row.alignment = 'LEFT'
        row.split(factor=1, align = True)
        row.prop(kosvars, "prefix", text="Prefix")
        row.split(factor=.1)
        row.split(factor=.1)
        row.prop(kosvars, "separator", text="Separator")
        box = layout.box()
        row = box.row()
        row.label(text="Pattern of the files in the Maps Folder : ")
        row = box.row()
        row.prop(kosvars, "patterns", text="")
        row = layout.row()
        row.prop(kosvars, "expert", text="Advanced Mode ", )

class KOS_PT_buttons(TexImporterPanel, Panel):

    bl_idname = "KOS_PT_buttons"
    bl_label = "Options"
    bl_parent_id = "KOS_PT_importpanel"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column(align = True)
        col.operator("KOS_OT_subimport")
        col.separator()

        row = col.row(align = True)
        col = layout.column(align = True)
        row = col.row(align = True)
        row.operator("KOS_OT_assignnodes")
        row.separator()
        row.operator("KOS_OT_createnodes")


class KOS_PT_options(TexImporterPanel, Panel):

    bl_idname = "KOS_PT_options"
    bl_label = "Options"
    bl_parent_id = "KOS_PT_importpanel"

    def draw(self, context):
        layout = self.layout
        kosvars = bpy.context.scene.kosvars
        row = layout.row()
        col = row.column(align = True)
        row = col.row(align = True)
        row.prop(kosvars, "shader", text="Replace Shader",)
        row = row.split()
        row.prop(kosvars, "shaderlist", text="")
        row = layout.row()
        row = layout.row()
        row.enabled = not kosvars.manison
        row.prop(kosvars, "applyall", text="Apply to all visible objects", )
        row = layout.row()
        row.enabled = not kosvars.manison
        row.prop(kosvars, "onlyactiveobj", text="Apply to active object only", )
        row = layout.row()
        row.prop(kosvars, "skipnormals", )
        row = layout.row()
        row.prop(kosvars, "customshader", text="Enable Custom Shaders", icon='NONE', icon_only=True)
        row = layout.row()
        row.prop(kosvars, "eraseall", text="Clear nodes from material", )
        row = layout.row()
        row.prop(kosvars, "extras", text="Attach Curves and Ramps ", )
        row = layout.row()
        row.enabled = not kosvars.manison
        row.prop(kosvars, "onlyamat", text="Only active Material",)
        row = layout.row()
        row.prop(kosvars, "fixname", text="Fix copied Material name",)
