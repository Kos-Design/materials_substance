import bpy
from bpy import context
from pathlib import Path
import json
from . nodeshandler import NodeHandler as nha
from . nodeshandler import SelectionSet
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

from . propertieshandler import PropertiesHandler as ph
                                    
from bpy.utils import (register_class, unregister_class)


def ShowMessageBox(message="", title="Message", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class sub_poll():
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):

        if context.object is not None:
            if context.object.active_material is not None:
                return True
        return False

class BSM_OT_reporter(Operator):
    bl_idname = "bsm.reporter"
    bl_label = "Displays reports"
    bl_description = "Prints message in Info Window"
    bl_options = {'INTERNAL'}
    
    reporting: bpy.props.StringProperty(default="")

    def execute(self, context):
        ShowMessageBox(message=self.reporting, title="Message", icon='INFO')
        #self.report({'INFO'}, self.reporting)
        return {'FINISHED'}


class BSM_OT_make_nodes(sub_poll,Operator):
    bl_idname = "bsm.make_nodes"
    bl_label = "Only Setup Nodes"
    bl_description = "Setup empty Texture Nodes"

    solo: bpy.props.BoolProperty(default=True)
   
    def execute(self, context):
        ndh = nha()
        report = ndh.handle_nodes(context,**{'method':'create_nodes'})
        reporting = ndh.print_dict(report)
           
        #)" \n ".join(list(report))
        self.report({'INFO'}, reporting)
        if self.solo:
            ShowMessageBox("Check Shader nodes panel", "Nodes created", 'FAKE_USER_ON')
        return {'FINISHED'}


class BSM_OT_assign_nodes(sub_poll,Operator):
    bl_idname = "bsm.assign_nodes"
    bl_label = "Only Assign Images"
    bl_description = "import maps for all selected objects"

    solo: bpy.props.BoolProperty(default=True)
    
    def execute(self, context):
        ndh = nha()
        report = ndh.handle_nodes(context,**{'method':'setup_nodes'})
        report['img_loaded'] 
        reporting = ndh.print_dict(report)
        self.report({'INFO'}, reporting)
        #self.report({'INFO'}, " \n ".join(list(report)))
        if self.solo:
            ShowMessageBox(f"{report['img_loaded']} matching images loaded", "Images assigned to respective nodes", 'FAKE_USER_ON')
        return {'FINISHED'}


class BSM_OT_import_textures(sub_poll, Operator):
    bl_idname = "bsm.import_textures"
    bl_label = "Import Substance Maps"
    bl_description = "Import Texture Maps for active object"
    
    def execute(self,context):
        bpy.ops.bsm.make_nodes(solo=False)
        bpy.ops.bsm.assign_nodes(solo=False)
        return {'FINISHED'}


class BSM_OT_add_map_line(sub_poll, Operator):
    bl_idname = "bsm.add_map_line"
    bl_label = ""
    bl_description = "Add a new map line below"

    line_number: IntProperty(default=0)

    def execute(self, context):
        ndh = nha()
        ndh.refresh_shader_links(context)
        context.scene.bsmprops.panel_rows += 1

        return {'FINISHED'}


class BSM_OT_del_map_line(sub_poll, Operator):
    bl_idname = "bsm.del_map_line"
    bl_label = ""
    bl_description = "Remove last Map from the list"

    marked: StringProperty(name="line n", default="BSM_PT_PaneLine1")

    def execute(self, context):
        ndh = nha()
        ndh.refresh_shader_links(context)
        scene = context.scene
        context.scene.bsmprops.panel_rows -= 1
        panel_line = eval(f"scene.panel_line{scene.bsmprops.panel_rows}")
        panel_line.manual = False
        panel_line.line_on = False
        context.view_layer.update()
        return {'FINISHED'}


class BSM_presetbase:
    #    """Base preset class, only for subclassing
    #    subclasses must define
    #     - preset_values
    #     - preset_subdir """
    # bl_idname = "script.preset_base_add"
    # bl_label = "Add a Python Preset"

    # only because invoke_props_popup requires. Also do not add to search menu.
    bl_options = {'REGISTER', 'INTERNAL'}

    name: StringProperty(
        name="Name",
        description="Name of the preset, used to make the path name",
        maxlen=64,
        options={'SKIP_SAVE'},
    )
    remove_name: BoolProperty(
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    remove_active: BoolProperty(
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    @staticmethod
    def as_filename(name):  # could reuse for other presets

        # lazy init maketrans
        def maketrans_init():
            cls = BSM_presetbase
            attr = "_as_filename_trans"

            trans = getattr(cls, attr, None)
            if trans is None:
                trans = str.maketrans({char: "_" for char in " !@#$%^&*(){}:\";'[]<>,.\\/?"})
                setattr(cls, attr, trans)
            return trans

        name = name.lower().strip()
        name = bpy.path.display_name_to_filepath(name)
        trans = maketrans_init()
        return name.translate(trans)

    def execute(self, context):
        from bpy.utils import is_path_builtin
        bpy.ops.bsm.save_all()
        if hasattr(self, "pre_cb"):
            self.pre_cb(context)

        preset_menu_class = getattr(bpy.types, self.preset_menu)

        is_xml = getattr(preset_menu_class, "preset_type", None) == 'XML'

        if is_xml:
            ext = ".xml"
        else:
            ext = ".py"

        name = self.name.strip()
        if not (self.remove_name or self.remove_active):

            if not name:
                return {'FINISHED'}

            # Reset preset name
            wm = bpy.data.window_managers[0]
            if name == wm.preset_name:
                wm.preset_name = 'New Preset'
            filename = self.as_filename(name)
            pathlibbed = str(Path("presets").joinpath(self.preset_subdir))
            target_path = bpy.utils.user_resource('SCRIPTS',
                                                  path=pathlibbed,
                                                  create=True)
            if not target_path:
                self.report({'WARNING'}, "Failed to create presets path")
                return {'CANCELLED'}
            filepath = str(Path(target_path).joinpath(filename)) + ext

            if hasattr(self, "add"):
                self.add(context, filepath)
            else:
                if is_xml:
                    import rna_xml
                    rna_xml.xml_file_write(context,
                                           filepath,
                                           preset_menu_class.preset_xml_map)
                else:

                    def rna_recursive_attr_expand(value, rna_path_step, level):
                        if isinstance(value, bpy.types.PropertyGroup):
                            for sub_value_attr in value.bl_rna.properties.keys():
                                if sub_value_attr == "rna_type":
                                    continue
                                sub_value = getattr(value, sub_value_attr)
                                rna_recursive_attr_expand(sub_value, "%s.%s" % (rna_path_step, sub_value_attr), level)
                        elif type(value).__name__ == "bpy_prop_collection_idprop":  # could use nicer method
                            file_preset.write("%s.clear()\n" % rna_path_step)
                            for sub_value in value:
                                file_preset.write("item_sub_%d = %s.add()\n" % (level, rna_path_step))
                                rna_recursive_attr_expand(sub_value, "item_sub_%d" % level, level + 1)
                        else:
                            # convert thin wrapped sequences
                            # to simple lists to repr()
                            try:
                                value = value[:]
                            except:
                                pass

                            file_preset.write("%s = %r\n" % (rna_path_step, value))

                    file_preset = open(filepath, 'w', encoding="utf-8")
                    file_preset.write("import bpy\n")

                    if hasattr(self, "preset_defines"):
                        for rna_path in self.preset_defines:
                            exec(rna_path)
                            file_preset.write("%s\n" % rna_path)
                        file_preset.write("\n")

                    for rna_path in self.preset_values:
                        value = eval(rna_path)
                        rna_recursive_attr_expand(value, rna_path, 1)

                    file_preset.close()

            preset_menu_class.bl_label = bpy.path.display_name(filename)

        else:
            if self.remove_active:
                name = preset_menu_class.bl_label

            # fairly sloppy but convenient.
            filepath = bpy.utils.preset_find(name,
                                             self.preset_subdir,
                                             ext=ext)

            if not filepath:
                filepath = bpy.utils.preset_find(name,
                                                 self.preset_subdir,
                                                 display_name=True,
                                                 ext=ext)

            if not filepath:
                return {'CANCELLED'}

            if is_path_builtin(filepath):
                self.report({'WARNING'}, "You can't remove the default presets")
                return {'CANCELLED'}

            try:
                if hasattr(self, "remove"):
                    self.remove(context, filepath)
                else:
                    Path(filepath).unlink()
            except Exception as e:
                self.report({'ERROR'}, "Unable to remove preset: %r" % e)
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

            preset_menu_class.bl_label = "Presets"

        if hasattr(self, "post_cb"):
            self.post_cb(context)

        return {'FINISHED'}


class BSM_OT_add_preset(BSM_presetbase, Operator):
    bl_idname = 'bsm.add_preset'
    bl_label = 'Add A preset'
    preset_menu = 'BSM_MT_presetsmenu'

    # Common variable used for all preset values
    preset_defines = ['scene = bpy.context.scene',
                      'bsmprops = scene.bsmprops',
                      ]
    # Properties to store in the preset
    preset_values = [
                     'bsmprops.advanced_mode',
                     'bsmprops.bsm_all',
                     'bsmprops.usr_dir',
                     'bsmprops.panel_rows',
                     'bsmprops.apply_to_all', 'bsmprops.clear_nodes',
                     'bsmprops.tweak_levels',
                     'bsmprops.only_active_obj', 'bsmprops.skip_normals',
                     'bsmprops.only_active_mat'

                     ]
    # Directory to store the presets
    preset_subdir = 'bsm_presets'


class BSM_OT_save_all(sub_poll, Operator):
    bl_idname = 'bsm.save_all'
    bl_label = 'save all values'
    bl_description = 'Save all relevant vars'

    def execute(self, context):
        propper = ph()
        args = {}
        props = context.scene.bsmprops
        args['internals'] = ["type","rna_type","content","bl_rna","name","bsm_all"]
        args['attributes'] = [attr for attr in dir(props) if attr not in args['internals'] and attr[:2] != "__"]
        for attr in args['attributes']:
            args[attr] = eval(f"props.{attr}")
        for i in range(10):
            line = eval(f"context.scene.panel_line{i}")
            args[line.name] = {}
            args[line.name]['map_label'] = line.map_label
            args[line.name]['input_sockets'] = line.input_sockets
            args[line.name]['line_on'] = str(line.line_on)
            args[line.name]['file_name'] = line.file_name
            args[line.name]['manual'] = str(line.manual)
        props.bsm_all = json.dumps(args)
        return {'FINISHED'}


class BSM_OT_load_all(sub_poll, Operator):
    bl_idname = 'bsm.load_all'
    bl_label = 'save all values'
    bl_description = 'load preset '

    def execute(self, context):
        props = context.scene.bsmprops
        args = json.loads(props.bsm_all)

        for attr in args['attributes']:
            props[attr] = args[attr]
        for i in range(10):
            panel_line = eval(f"context.scene.panel_line{i}")
            panel_line['map_label'] = args[f"PaneLine{i}"]['map_label'] 
            try :
                panel_line.input_sockets = args[f"PaneLine{i}"]['input_sockets']
            except TypeError :
                #print(args[f"PaneLine{i}"]['input_sockets'])
                panel_line['input_sockets'] = '0'
            panel_line['line_on'] = bool(int(eval(args[f"PaneLine{i}"]['line_on'])))
            panel_line['file_name'] = args[f"PaneLine{i}"]['file_name']
            panel_line['manual'] = bool(int(eval(args[f"PaneLine{i}"]['manual'])))
        context.view_layer.update()    
        return {'FINISHED'}


class BSM_MT_presetsmenu(Menu):
    # bl_idname = 'my.presetmenu'
    bl_label = 'Presets Menu'
    preset_subdir = 'bsm_presets'
    preset_operator = 'bsm.execute_preset'
    draw = Menu.draw_preset


class BSM_OT_execute_preset(Operator):
    # """Execute a preset"""
    bl_idname = "bsm.execute_preset"
    bl_label = "Execute a Python Preset"

    filepath: StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    menu_idname: StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = BSM_MT_presetsmenu  # getattr(bpy.types, self.menu_idname)
        preset_class.bl_label = bpy.path.display_name(Path(filepath).stem)
        ext = str(Path(filepath).suffix).lower()
        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "unknown filetype: %r" % ext)
            return {'CANCELLED'}

        if hasattr(preset_class, "reset_cb"):
            preset_class.reset_cb(context)

        if ext == ".py":
            try:
                bpy.utils.execfile(filepath)
            except Exception as ex:
                self.report({'ERROR'}, "Failed to execute the preset: " + repr(ex))

        elif ext == ".xml":
            import rna_xml
            rna_xml.xml_file_run(context,
                                 filepath,
                                 preset_class.preset_xml_map)

        if hasattr(preset_class, "post_cb"):
            preset_class.post_cb(context)
        bpy.ops.bsm.load_all()
        return {'FINISHED'}
