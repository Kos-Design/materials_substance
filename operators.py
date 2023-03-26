import bpy
from pathlib import Path

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

from . propertieshandler import PropertiesHandler as ph
                                    
from bpy.utils import (register_class, unregister_class)


def ShowMessageBox(message="", title="Message", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def selector(self, context):
    viewl = context.view_layer
    bsmprops = context.scene.bsmprops
    only_active_obj = bsmprops.only_active_obj
    applytoall = bsmprops.apply_to_all

    leset = viewl.objects.selected

    lecleanselect = []
    validtypes = ['SURFACE', 'CURVE', 'META', 'MESH', 'GPENCIL']
    if applytoall:
        leset = viewl.objects
    if only_active_obj:
        leset = [context.object]

    for obj in leset:
        if obj.type in validtypes:
            lecleanselect.append(obj)
            obj.select_set(False)

    return lecleanselect

class popol():
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):

        if context.object is not None:
            if context.object.active_material is not None:
                return True
        return False


class BSM_OT_createnodes(popol,Operator):
    bl_idname = "bsm.createnodes"
    bl_label = "Only Setup Nodes"
    bl_description = "Setup empty Texture Nodes"

    fromimportbutton: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        ndh = NodeHandler()
        scene = context.scene
        if len(scene.shader_links) == 0:
            bpy.ops.bsm.createdummy()
        matsdone = []

        og_selection = list(context.view_layer.objects.selected)
        activeobj = context.view_layer.objects.active
        lecleanselect = selector(self, context)
        #TODO why matsdone ?
        for obj in og_selection:
            obj.select_set(False)
        for leselected in lecleanselect:
            leselected.select_set(True)
            context.view_layer.objects.active = leselected
            mat_params = {'context':context, 'selection':leselected, 'already_done':matsdone, 'caller':"dothem"}
            matsdone = ndh.foreachmat(**mat_params)
            
            leselected.select_set(False)

        for obj in og_selection:
            obj.select_set(True)
        context.view_layer.objects.active = activeobj

        if not self.fromimportbutton:
            ShowMessageBox("Check Shader nodes panel", "Nodes created", 'FAKE_USER_ON')

        return {'FINISHED'}


class BSM_OT_assumename(popol,Operator):
    bl_idname = "bsm.assumename"
    bl_label = ""
    bl_description = "Assume a probable filename "

    line_num: bpy.props.IntProperty(default=0)
    #TODO: override popol type ?
    @classmethod
    def poll(cls, context):
        # return (context.object is not None)
        return True

    def execute(self, context):
        k = self.line_num
        scene = context.scene
        panel_line = eval(f"scene.panel_line{k}")
        bsmprops = scene.bsmprops
        lefolder = bsmprops.usr_dir
        prefix = bsmprops.prefix
        fullext = panel_line.mapext
        mapname = panel_line.maplabels
        separator = bsmprops.separator
        patternselected = int(bsmprops.patterns)
        allexts = [fullext.capitalize(), fullext.upper(), fullext, ]
        propper = ph()
        matname = propper.mat_cleaner(context)[1]
        for ext in allexts:
            params = [prefix, mapname, ext, matname]
            patterns_list = propper.patterns_list(context, params)
            supposed = patterns_list[patternselected][1]

            panel_line.probable = lefolder + supposed
            if Path(panel_line.probable).is_file():
                break

        return {'FINISHED'}


class GuessName():
    def testit(self, **gs_params):
        context = gs_params['context']
        scene = context.scene
        panel_line = gs_params['props']
        keepat = gs_params['keep_pattern']
        bsmprops = scene.bsmprops
        prefix = bsmprops.prefix
        isindir = Path(panel_line.lefilename).name in str(Path(panel_line.lefilename).parent)
        # almost always True but better safe than sorry
        fullext = panel_line.mapext
        allexts = [fullext, fullext.upper(), fullext.capitalize()]
        manual = panel_line.manual
        mapname = panel_line.maplabels
        propper = ph()
        matname = propper.mat_cleaner(context)[1]
        isindir = False
        patternselected = int(bsmprops.patterns)
        if not manual:

            for ext in allexts:

                if isindir:
                    break
                params = [prefix, mapname, ext, matname]
                patterns = propper.patterns_list(context, params)
                supposed = patterns[patternselected][1]
                panel_line.probable = str(Path(bsmprops.usr_dir).joinpath(supposed))
                if Path(panel_line.probable).is_file():
                    panel_line.lefilename = panel_line.probable

                    panel_line.probable = panel_line.lefilename
                    isindir = True
                    break

                if not keepat:
                    for liner in patterns:
                        tentative = liner[1]
                        panel_line.probable = str(Path(bsmprops.usr_dir).joinpath(tentative))

                        if Path(panel_line.probable).is_file():
                            panel_line.lefilename = panel_line.probable
                            bsmprops.patterns = liner[0]  # TODO reversepattern maybe
                            panel_line.probable = panel_line.lefilename
                            isindir = True

                            break

        return isindir


class BSM_OT_guessfilext(popol,Operator):
    bl_idname = "bsm.guessfilext"
    bl_label = ""
    bl_description = "set panel_line{linen}.mapext according to dir content"

    keepat: bpy.props.BoolProperty(default=False)
    linen: bpy.props.IntProperty()
    called: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        keepat = self.keepat
        linen = self.linen
        scene = context.scene
        panel_line = eval(f"scene.panel_line{linen}")
        manual = panel_line.manual
        gsn = GuessName()
        propper = ph()
        gs_params = {'context': context, 'props':panel_line, 'keep_pattern':keepat}
        currentext = panel_line.mapext
        isindir = gsn.testit(**gs_params)

        if not isindir and not manual:

            filetypesraw = propper.givelist(context)
            filetypes = []
            for i in range(len(filetypesraw)):
                filetypes.append(filetypesraw[i][0])
            originalext = panel_line.mapext
            for ext in filetypes:
                panel_line.mapext = ext

                isindir = gsn.testit(**gs_params)

                if isindir:
                    break
            if not isindir:
                if not self.called:
                    toreport = "Could not guess file extension, File not found"
                    self.report({'INFO'}, toreport)
                panel_line.mapext = originalext
        return {'FINISHED'}


class BSM_OT_checkmaps(popol,Operator):
    bl_idname = "bsm.checkmaps"
    bl_label = ""
    bl_description = "Check if a file containing the Map Name keyword matches the Pattern"

    linen: bpy.props.IntProperty(default=0)
    lorigin: bpy.props.StringProperty(default="Not Set")
    called: bpy.props.BoolProperty(default=True)
    notfromext: bpy.props.BoolProperty(default=True)
    keepat: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        keepat = self.keepat
        scene = context.scene
        bsmprops = scene.bsmprops
        linen = self.linen
        notfromext = self.notfromext

        panel_line = eval(f"scene.panel_line{linen}")
        manual = panel_line.manual
        expert = bsmprops.expert
        prefix = bsmprops.prefix
        sel = context.object
        mat = sel.active_material
        mat.use_nodes = True
        gsn = GuessName()
        gs_params = {'context':context, 'props':panel_line, 'keep_pattern':keepat}
        if self.lorigin == "plug" and not manual:
            panel_line.probable = "reseted"

        isafile = Path(panel_line.probable).is_file()

        if not manual:

            gotafile = gsn.testit(**gs_params)

            if not gotafile:
                bpy.ops.bsm.guessfilext(linen=linen)
            isafile = gsn.testit(**gs_params)

            if not isafile and self.called :
                toreport = panel_line.probable + " not found "
                self.report({'INFO'}, toreport)
                __class__.bl_description = "No Image containing the keyword " + panel_line.maplabels + " found , verify the Prefix, the Map name and/or the Maps Folder"

                if not prefix.isalnum():
                    toreport = "Prefix is empty"
                    self.report({'INFO'}, toreport)

                __class__.bl_description = "Set a non-empty Prefix in the Preferences (of this Addon Tab)"
            # necessary in order to update description
            unregister_class(__class__)
            register_class(__class__)

        if isafile:
            if self.called:
                toreport = panel_line.probable + " detected in Maps Folder"
                self.report({'INFO'}, toreport)

            return {'FINISHED'}
        return {'CANCELLED'}


class BSM_OT_assignnodes(popol,Operator):
    bl_idname = "bsm.assignnodes"
    bl_label = "Only Assign Images"
    bl_description = "import maps for all selected objects"

    fromimportbutton: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        ndh = NodeHandler()
        scene = context.scene
        if len(scene.shader_links) == 0:
            bpy.ops.bsm.createdummy()
        og_selection = list(context.view_layer.objects.selected)
        activeobj = context.view_layer.objects.active
        lecleanselect = selector(self, context)
        matsdone = []
        for obj in og_selection:
            obj.select_set(False)
        for leselected in lecleanselect:
            leselected.select_set(True)
            context.view_layer.objects.active = leselected
            mat_params = {'context':context, 'selection':leselected, 'already_done':matsdone, 'caller':"plug"}
            matsdone = ndh.foreachmat(**mat_params)
            leselected.select_set(False)

        for obj in og_selection:
            obj.select_set(True)
        context.view_layer.objects.active = activeobj
        if not self.fromimportbutton:
            pass
            # ShowMessageBox("All images loaded sucessfully", "Image Textures assigned", 'FAKE_USER_ON')
        return {'FINISHED'}


class BSM_OT_subimport(popol, Operator):
    bl_idname = "bsm.subimport"
    bl_label = "Import Substance Maps"
    bl_description = "Import Texture Maps for active object"

    def execute(self, context):
        bpy.ops.bsm.createnodes(fromimportbutton=True)
        bpy.ops.bsm.assignnodes(fromimportbutton=True)
        # ShowMessageBox("Nodes created and Textures loaded", "Success !", 'FAKE_USER_ON')

        return {'FINISHED'}


class BSM_OT_addaline(popol, Operator):
    bl_idname = "bsm.addaline"
    bl_label = ""
    bl_description = "Add a new map line below"

    linen: IntProperty(default=0)

    def execute(self, context):
        if len(context.scene.shader_links) == 0:
            bpy.ops.bsm.createdummy()
        context.scene.bsmprops.panel_rows += 1

        return {'FINISHED'}


class BSM_OT_removeline(popol, Operator):
    bl_idname = "bsm.removeline"
    bl_label = ""
    bl_description = "Remove last Map from the list"

    marked: StringProperty(name="line n", default="BSM_PT_PaneLine1")

    def execute(self, context):
        if len(context.scene.shader_links) == 0:
            bpy.ops.bsm.createdummy()
        scene = context.scene
        context.scene.bsmprops.panel_rows -= 1
        panel_line = eval(f"scene.panel_line{scene.bsmprops.panel_rows}")
        panel_line.manual = False
        panel_line.labelbools = False

        context.view_layer.update()
        return {'FINISHED'}


class BsmAddPresetbase:
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
            cls = BsmAddPresetbase
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
        import os
        from bpy.utils import is_path_builtin
        bpy.ops.bsm.saveall()
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


class BSM_OT_addpreset(BsmAddPresetbase, Operator):
    bl_idname = 'bsm.addpreset'
    bl_label = 'Add A preset'
    preset_menu = 'BSM_MT_presetsmenu'

    # Common variable used for all preset values
    preset_defines = ['scene = bpy.context.scene',
                      'bsmprops = scene.bsmprops',
                      ]
    # Properties to store in the preset
    preset_values = [
                     'bsmprops.expert',
                     'bsmprops.bsm_all',
                     'bsmprops.usr_dir', 'bsmprops.separator',
                     'bsmprops.panel_rows',
                     'bsmprops.apply_to_all', 'bsmprops.eraseall',
                     'bsmprops.tweak_levels',
                     'bsmprops.only_active_obj', 'bsmprops.skipnormals',
                     'bsmprops.onlyamat',
                     'bsmprops.fixname',
                     'bsmprops.prefix',
                     'bsmprops.patterns'

                     ]
    # Directory to store the presets
    preset_subdir = 'bsm_presets'


class BSM_OT_createdummy(popol, Operator):
    bl_idname = "bsm.createdummy"
    bl_label = "dummy creator"
    bl_description = "used to initialize some dynamic props"

    def execute(self, context):
        context.scene.shader_links.clear()

        fetchedOutputs = []  #
        fetchedInputs = []  #
        fetchedShaders = []  #
        fetchedNodes = []  #
        fetchedObjects = []  #
        scene = context.scene
        scenename = str(scene.name_full)
        bsmprops = scene.bsmprops
        propper = ph()
        lashaderlist = propper.populate(context)
        for obj in context.view_layer.objects.selected:
            fetchedObjects.append(obj)
        bpy.ops.object.select_all(action='DESELECT')
        activeobj = context.view_layer.objects.active

        view_layer = context.view_layer
        mesh = bpy.data.meshes.new("mesh")
        lecubetmp = bpy.data.objects.new(mesh.name, mesh)
        collecto = bpy.data.collections.new("latmpcollect")
        collecto.objects.link(lecubetmp)
        vieww = view_layer.active_layer_collection
        vieww.collection.children.link(collecto)
        lecubetmp.select_set(True)
        view_layer.objects.active = lecubetmp
        lematcree = bpy.data.materials.new(name="MaterialName")
        lecubetmp.data.materials.append(lematcree)
        mattemp = lecubetmp.material_slots[-1].material
        mattemp.use_nodes = True
        lashaderlistraw = []

        leshaderoutputnodes = []
        allshaderstnodes = []
        # only create nodes for the initial shaderlist populated by ph.populate
        lenghtlist = 11  
        for lesnods in range(lenghtlist):
            laligne = lashaderlist[lesnods]
            lID = int(lesnods)
            letyp = str(laligne[0])
            lename = str(laligne[1])
            fetchedShaders.append((lename, letyp), )
            lashaderlistraw.append(laligne)
            lanewnode = mattemp.node_tree.nodes.new(type=letyp)
            lanewnode.name = lename
            lanewnode.label = lanewnode.name
            leszinputs = mattemp.node_tree.nodes[lanewnode.name].inputs
            leszoutputs = mattemp.node_tree.nodes[lanewnode.name].outputs
            lalistsizeI = len(leszinputs)
            lalistsizeO = len(leszoutputs)
            fetchedInputs = []
            fetchedOutputs = []
            for inp in range(0, lalistsizeI):
                leyley = leszinputs[inp].name
                leinpname = (leyley, leyley, "",)
                leshaderoutputnodes.append(leinpname)
                fetchedInputs.append(leyley)
            for inp in range(0, lalistsizeO):
                loyloy = leszoutputs[inp].name
                leoutname = (loyloy, loyloy, "",)
                fetchedOutputs.append(loyloy)

            newentry = context.scene.shader_links.add()
            newentry.name = lename
            newentry.shadertype = letyp
            newentry.inputsockets = "@-¯\(°_o)/¯-@".join(str(x) for x in fetchedInputs)
            newentry.outputsockets = "@-¯\(°_o)/¯-@".join(str(x) for x in fetchedOutputs)

            allshaderstnodes.append(leshaderoutputnodes)

        bpy.data.materials.remove(lematcree)
        bpy.data.objects.remove(lecubetmp)
        bpy.data.collections.remove(collecto)

        for obj in fetchedObjects:
            bpy.data.scenes[scenename].objects[obj.name].select_set(True)
        context.view_layer.objects.active = activeobj
        return {'FINISHED'}


class BSM_OT_saveall(popol, Operator):
    bl_idname = 'bsm.saveall'
    bl_label = 'save all values'
    bl_description = 'Save all relevant vars'

    def execute(self, context):
        scene = context.scene
        bsmprops = scene.bsmprops
        arey = []
        for i in range(10):
            maplabels = eval(f"scene.panel_line{i}").maplabels
            lechan = eval(f"scene.panel_line{i}").inputsockets
            enabled = str(eval(f"scene.panel_line{i}").labelbools)
            exts = eval(f"scene.panel_line{i}").mapext
            lesfilenames = eval(f"scene.panel_line{i}").lefilename
            probables = eval(f"scene.panel_line{i}").probable
            manuals = str(eval(f"scene.panel_line{i}").manual)

            lineitems = [str(eval(f"scene.panel_line{i}").name), maplabels, lechan, enabled, exts, lesfilenames, probables, manuals ]
            lineraw = "@\_/@".join(str(lx) for lx in lineitems)
            arey.append(lineraw)

        bsmprops.bsm_all = "@-¯\(°_o)/¯-@".join(str(lx) for lx in arey)

        return {'FINISHED'}


class BSM_OT_loadall(popol, Operator):
    bl_idname = 'bsm.loadall'
    bl_label = 'save all values'
    bl_description = 'load preset '

    def execute(self, context):

        scene = context.scene
        bsmprops = scene.bsmprops
        allraw = bsmprops.bsm_all.split("@-¯\(°_o)/¯-@")
        allin = []
        for allitems in allraw:
            zob = allitems.split("@\_/@")
            allin.append(zob)
        for i in range(10):
            PaneLine = eval(f"scene.panel_line{i}")
            PaneLine.maplabels = allin[i][1]
            try :
                PaneLine.inputsockets = allin[i][2]
            except TypeError :
                PaneLine.inputsockets = '0'
            PaneLine.labelbools = bool(int(eval(allin[i][3])))
            PaneLine.mapext = allin[i][4]
            PaneLine.lefilename = allin[i][5]
            PaneLine.probable = allin[i][6]
            PaneLine.manual = bool(int(eval(allin[i][7])))

        return {'FINISHED'}


class BSM_MT_presetsmenu(Menu):
    # bl_idname = 'my.presetmenu'
    bl_label = 'Presets Menu'
    preset_subdir = 'bsm_presets'
    preset_operator = 'bsm.execute_preset'
    draw = Menu.draw_preset


class BsmExecutePreset(Operator):
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
        bpy.ops.bsm.loadall()
        return {'FINISHED'}
