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
from . propertieshandler import PropertiesHandler,props,texture_importer
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
            return len(ndh.get_target_mats(bpy.context))
        except:
            return False


class NODE_OT_stm_add_substance_texture(SubOperatorPoll,Operator):
    bl_idname = "node.stm_add_item"
    bl_label = "Add Texture"

    def execute(self, context):
        propper.add_panel_lines(context)
        return {'FINISHED'}


class NODE_OT_stm_del_substance_texture(SubOperatorPoll,Operator):
    bl_idname = "node.stm_remove_item"
    bl_label = "Remove Texture"

    def execute(self, context):
        propper.del_panel_line(context)
        return {'FINISHED'}


class NODE_OT_stm_make_nodes(OperatorPoll,Operator):
    bl_idname = "node.stm_make_nodes"
    bl_label = "Only Setup Nodes"
    bl_description = "Setup empty Texture Nodes"

    solo: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        self.report({'INFO'}, ndh.print_dict(ndh.handle_nodes(context,True)))
        if self.solo:
            ShowMessageBox("Check Shader nodes panel", "Nodes created", 'FAKE_USER_ON')
        return {'FINISHED'}


class NODE_OT_stm_assign_nodes(OperatorPoll,Operator):
    bl_idname = "node.stm_assign_nodes"
    bl_label = "Only Assign Images"
    bl_description = "import maps for all selected objects"

    solo: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        report = ndh.handle_nodes(context)
        self.report({'INFO'}, ndh.print_dict(report))
        if self.solo:
            ShowMessageBox(f"{report['img_loaded']} matching images loaded", "Images assigned to respective nodes", 'FAKE_USER_ON')
        return {'FINISHED'}


class NODE_OT_stm_import_textures(OperatorPoll,Operator):
    bl_idname = "node.stm_import_textures"
    bl_label = "Import Substance Maps"
    bl_description = "Import texture maps for active object"

    def execute(self,context):
        for i in range (2):
            self.report({'INFO'},ndh.print_dict(ndh.handle_nodes(context,not i)))
        return {'FINISHED'}


class NODE_OT_stm_add_preset(SubOperatorPoll,Operator):
    bl_idname = 'node.stm_add_preset'
    bl_label = 'Add A preset'
    bl_description = 'Add preset'

    def execute(self, context):
        preset_name = props().custom_preset_name.strip()
        if not preset_name:
            self.report({'ERROR'}, "Preset name cannot be empty")
            return {'CANCELLED'}

        preset_file = NODE_OT_stm_presets_dialog.preset_directory / f"{preset_name}.py"
        with open(preset_file, "w", encoding="utf-8") as w:
            w.write(propper.fill_settings(context))

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
        try:
            with open(self.preset_file, "r", encoding="utf-8") as w:
                props().stm_all = w.read()  # Read the file content
                propper.load_props(context)  # Load the properties

                self.report({'INFO'}, f"Applied preset: {self.preset_file}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to apply preset: {e}")
        return {'FINISHED'}

