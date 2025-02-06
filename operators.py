import bpy
from bpy import context
from pathlib import Path
import json
from . nodeshandler import NodeHandler
from bpy.types import (
    Operator, PropertyGroup, UIList, WindowManager,
    Scene, Menu,
)
from bpy.props import (
    StringProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty,
    FloatProperty, FloatVectorProperty,
    EnumProperty,
)
from . propertieshandler import PropertiesHandler,props,texture_importer,texture_index,lines
from bpy.utils import (register_class, unregister_class)
from . import __package__ as package
import os

propper = PropertiesHandler()
ndh = NodeHandler()

def ShowMessageBox(message="", title="Message", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

class SubOperatorPoll():
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return hasattr(texture_importer(), "textures")


class OperatorPoll():
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            return len(ndh.get_target_mats(context))
        except:
            return False


class NODE_OT_stm_add_substance_texture(SubOperatorPoll,Operator):
    bl_idname = "node.stm_add_item"
    bl_label = "Add Texture"

    def execute(self, context):
        propper.add_panel_lines()
        return {'FINISHED'}


class NODE_OT_stm_del_substance_texture(SubOperatorPoll,Operator):
    bl_idname = "node.stm_remove_item"
    bl_label = "Remove Texture"

    def execute(self, context):
        propper.del_panel_line()
        return {'FINISHED'}

class NODE_OT_stm_reset_substance_textures(SubOperatorPoll,Operator):
    bl_idname = "node.stm_reset_substance_textures"
    bl_label = "Reset textures names"
    bl_description = "Resets the textures lines to a default set of values.\
                    \n (Color, Roughness, Metallic, Normal)"
    
    def execute(self, context):
        propper.initialize_defaults()
        return {'FINISHED'}


class NODE_OT_stm_make_nodes(OperatorPoll,Operator):
    bl_idname = "node.stm_make_nodes"
    bl_label = "Only Setup Nodes"
    bl_description = "Setup empty Texture Nodes"

    def execute(self, context):
        self.report({'INFO'}, ("\n").join(ndh.report_content))
        ndh.handle_nodes(True)
        ShowMessageBox("Check Shader nodes panel", "Nodes created", 'FAKE_USER_ON')
        return {'FINISHED'}


class NODE_OT_stm_assign_nodes(OperatorPoll,Operator):
    bl_idname = "node.stm_assign_nodes"
    bl_label = "Only Assign Images"
    bl_description = "import maps for all selected objects"

    def execute(self, context):
        ndh.handle_nodes()
        self.report({'INFO'}, ("\n").join(ndh.report_content))
        img_count = len([line for line in ndh.report_content if "assigned" in line])
        ShowMessageBox(f"{img_count} matching images loaded", "Images assigned to respective nodes", 'FAKE_USER_ON')
        return {'FINISHED'}


class NODE_OT_stm_import_textures(OperatorPoll,Operator):
    bl_idname = "node.stm_import_textures"
    bl_label = "Import Substance Maps"
    bl_description = "Import texture maps for active object"

    def execute(self,context):
        for i in range (2):
            ndh.handle_nodes(not i)
            self.report({'INFO'},("\n").join(ndh.report_content) )
        return {'FINISHED'}


class NODE_OT_stm_add_preset(SubOperatorPoll,Operator):
    bl_idname = 'node.stm_add_preset'
    bl_label = 'Add A preset'
    bl_description = 'Add preset'

    def execute(self, context):
        preset_name = props().custom_preset_name
        if not preset_name:
            self.report({'ERROR'}, "Preset name cannot be empty")
            return {'CANCELLED'}
        p_file = Path(NODE_OT_stm_presets_dialog.preset_directory).joinpath(preset_name)
        filer = f"{p_file}{'.py' if not 'py' in p_file.suffix else ''}"
        with open(filer, "w", encoding="utf-8") as w:
            w.write(propper.fill_settings())
            self.report({'INFO'}, f"Added preset: {preset_name}")
            return {'FINISHED'}
        return {'CANCELLED'}


class NODE_OT_stm_presets_dialog(SubOperatorPoll,Operator):
    bl_idname = "node.stm_presets_dialog"
    bl_label = "STM Presets"
    bl_description = 'Open preset panel'

    preset_directory = Path(bpy.utils.extension_path_user(f'{package}',path="stm_presets", create=True))

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=200)

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.label(text="Presets:")
        layout.separator()
        if self.preset_directory.exists():
            files = sorted(self.preset_directory.glob("*.py"))
            for file in files:
                row = layout.split(factor=0.85, align=True)
                op = row.operator("node.stm_execute_preset", text=file.stem,emboss=False)
                op.preset_file = str(file)
                del_op = row.operator("node.stm_delete_preset", text="", icon="REMOVE",emboss=False)
                del_op.preset_file = str(file)
        else:
            layout.label(text="No presets found")
        layout.separator()
        row = layout.split(factor=0.85, align=True)
        row.prop(props(), "custom_preset_name", text="")
        row.operator("node.stm_add_preset", text="", icon="ADD")


class NODE_OT_stm_delete_preset(SubOperatorPoll,Operator):
    bl_idname = "node.stm_delete_preset"
    bl_label = "Delete Custom Preset"
    bl_description = 'Delete preset'

    preset_file: bpy.props.StringProperty()

    def execute(self, context):
        preset_path = Path(self.preset_file)
        if preset_path.exists():
            preset_path.unlink()
            self.report({'INFO'}, f"Deleted preset: {preset_path.name}")
        else:
            self.report({'ERROR'}, "Preset not found")
        return {'FINISHED'}


class NODE_OT_stm_execute_preset(SubOperatorPoll,Operator):
    bl_idname = "node.stm_execute_preset"
    bl_label = "Execute a Python Preset"
    bl_description = 'Select preset'

    preset_file: bpy.props.StringProperty()

    def execute(self, context):
        if not self.preset_file:
            self.report({'ERROR'}, "Preset name cannot be empty")
            return {'CANCELLED'}
        filer = f"{Path(NODE_OT_stm_presets_dialog.preset_directory).joinpath(self.preset_file)}"
        print(filer)
        try:
            props().custom_preset_enum = filer
            return {'FINISHED'}
        except Exception:
            return {'CANCELLED'}

class NODE_OT_add_preset_popup(bpy.types.Operator):
    bl_idname = "node.add_preset_popup"
    bl_label = "Add Preset"
    bl_description = "Add a new preset"

    preset_name: bpy.props.StringProperty(name="Preset Name")

    def execute(self, context):
        if not self.preset_name:
            self.report({'ERROR'}, "Preset name cannot be empty")
            return {'CANCELLED'}
        p_file = Path(NODE_OT_stm_presets_dialog.preset_directory).joinpath(self.preset_name)
        filer = f"{p_file}{'.py' if not 'py' in p_file.suffix else ''}"
        with open(filer, "w", encoding="utf-8") as w:
            w.write(propper.fill_settings())
        props().custom_preset_enum = filer
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")

def sync_filepath(self,context):
    props().usr_dir = self.directory

def get_directory(self,context):
    return self.directory

def set_directory(self,value):
    self["directory"] = value
    props().usr_dir = self["directory"]

class IMPORT_OT_stm_window(Operator):
    bl_idname = "import.stm_window"
    bl_label = "Import Substance Textures"
    bl_description = "Open a substance textures importer panel"

    directory: bpy.props.StringProperty(subtype="DIR_PATH",set=set_directory)
    show_options: bpy.props.BoolProperty(name="Options", default=True)
    preset_directory = NODE_OT_stm_presets_dialog.preset_directory
    
    def execute(self, context):
        for i in range (2):
            ndh.handle_nodes(not i)
            self.report({'INFO'},("\n").join(ndh.report_content))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        space = context.space_data
        params = space.params
        current_directory = params.directory
        #if props().usr_dir != self.directory:
        #    props().usr_dir = self.directory
        
        layout.label(text=f"Textures Directory: {Path(current_directory.decode('utf-8')).name}")
        
        layout.label(text="<<--- Select the textures folder to import _Î")
        if self.preset_directory.exists():
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            split = row.split(factor=0.85, align=True)
            split.prop(props(), "custom_preset_enum", text="")
            buttons_row = split.row(align=True)
            buttons_row.operator("node.add_preset_popup", text="", icon="ADD")
            del_op = buttons_row.operator("node.stm_delete_preset", text="", icon="REMOVE")
            del_op.preset_file = props().custom_preset_enum

        row = layout.row()
        row.prop(props(), "target")
        row = layout.row()
        row.template_list(
            "NODE_UL_stm_list", "Textures",
            texture_importer(), "textures",
            texture_importer(), "texture_index",
            type="GRID",
            columns=1,
        )
        button_col = row.column(align=True)
        button_col.operator("node.stm_add_item", icon="ADD", text="")
        button_col.operator("node.stm_remove_item", icon="REMOVE", text="")
        button_col.separator(factor=3)
        button_col.separator(factor=3)
        button_col.separator(factor=3)
        button_col.operator("node.stm_reset_substance_textures", icon="FILE_REFRESH", text="")
        if lines() and texture_index() < len(lines()):
            item = lines()[texture_index()]
            layout.prop(item, "line_on")
            sub_layout = layout.column()
            sub_layout.enabled = item.line_on
            if props().advanced_mode :
                sub_sub_layout = sub_layout.column()
                sub_sub_layout.prop(item, "manual")
                if item.manual :
                    sub_sub_sub_layout = sub_sub_layout.column()
                    sub_sub_sub_layout.prop(item, "file_name")
                sub_sub_layout.prop(item, "split_rgb")
                if item.split_rgb:
                    if item.channels.socket and item.channels.sockets_index < len(item.channels.socket):
                        for i,sock in enumerate(item.channels.socket):
                            sub_sub_layout.prop(sock, "input_sockets",text=sock.name,icon=f"SEQUENCE_COLOR_0{((i*3)%9+1)}")
            if not item.split_rgb:
                sub_layout.prop(item, "input_sockets")
        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(props(), "advanced_mode", text="Manual Mode ", )

        row = layout.row()
        row.operator("node.stm_assign_nodes")
        row.separator()
        row.operator("node.stm_make_nodes")
        row = layout.row(align = True)
        row.alignment = 'LEFT'
        row.prop(self, "show_options", icon="TRIA_DOWN" if self.show_options else "TRIA_RIGHT", emboss=False)
        if self.show_options:
            box = layout.box()
            row = box.row(align = True)
            row.prop(props(), "replace_shader", text="Replace Shader",)
            row = row.split()
            if props().replace_shader :
                row.prop(props(), "shaders_list", text="")
            row = box.row()
            row.prop(props(), "skip_normals", )
            row = layout.row()
            row.prop(props(), "mode_opengl", )
            row = box.row()
            row.prop(props(), "include_ngroups", text="Enable Custom Shaders", )
            row = box.row()
            row.prop(props(), "match_sockets", text="Auto-detect sockets", )
            row = box.row()
            row.prop(props(), "clear_nodes", text="Clear nodes from material", )
            row = box.row()
            row.prop(props(), "tweak_levels", text="Attach Curves and Ramps ", )
            row = box.row()
            row.prop(props(), "only_active_mat", text="Only active Material",)
            row = box.row()
            row.prop(props(), "dup_mat_compatible", text="Duplicated material compatibility",)
            row = box.row()
            row.separator()


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_stm_window.bl_idname, text="Substance Textures")

