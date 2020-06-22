import bpy
import os

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

from materials_substance.PropertyGroups import (MatnameCleaner,
                                      PatternsVariations,
                                      extlist, Kosinit
                                      )
from bpy.utils import (register_class, unregister_class)


def ShowMessageBox(message="", title="Message", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def selector(self, context):
    viewl = context.view_layer
    kosvars = context.scene.kosvars
    onlyactiveobj = kosvars.onlyactiveobj
    applytoall = kosvars.applyall

    leset = viewl.objects.selected

    lecleanselect = []
    validtypes = ['SURFACE', 'CURVE', 'META', 'MESH', 'GPENCIL']
    if applytoall:
        leset = viewl.objects
    if onlyactiveobj:
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


def checklist(self, context):
    kosvars = context.scene.kosvars
    panelrows = kosvars.panelrows
    lesmaps = []
    enabled = []
    leschans = []
    # TODO see why it doesnt' work without bpy. on context
    on = list(i for i in range(panelrows) if eval(f"bpy.context.scene.kosp{i}.labelbools"))
    for i in on:
        kosp = eval(f"context.scene.kosp{i}")
        if not kosp.manual:
            lesmaps.append(kosp.maplabels)
        else:
            lesmaps.append(os.path.basename(kosp.lefilename))

        leschans.append(kosp.inputsockets)
        enabled.append(kosp.labelbools)
    result = [lesmaps, leschans, on]
    return result


def foreachmat(self, context, mat_params):
    matnamesdone = mat_params[1]
    leselected = mat_params[0]
    lafunction = mat_params[2]
    maslots = leselected.material_slots
    kosvars = context.scene.kosvars
    idx = leselected.active_material_index
    if kosvars.onlyamat:
        maslots = [leselected.material_slots[idx]]

    for i in range(len(maslots)):
        leselected.active_material_index = i
        lematos = leselected.active_material

        if lematos != None:

            if lematos.name not in matnamesdone:
                lematos.use_nodes = True
                params = checklist(self, context)

                enabled = params[2]
                if lafunction == "plug":
                    for indexed in enabled:
                        pg_params = [lematos, indexed]
                        plugthenodes(self, context, pg_params)

                if lafunction == "dothem":
                    do_params = [params[0], params[1], lematos]
                    dothenodes(self, context, do_params)

                matnamesdone.append(lematos.name)

    leselected.active_material_index = idx
    return matnamesdone


class KOS_OT_createnodes(popol, Operator):
    bl_idname = "kos.createnodes"
    bl_label = "Only Setup Nodes"
    bl_description = "Setup empty Texture Nodes"

    fromimportbutton: bpy.props.BoolProperty(default=False)

    def execute(self, context):

        scene = context.scene
        if len(scene.koshi) == 0:
            bpy.ops.kos.createdummy()
        matsdone = []

        og_selection = list(context.view_layer.objects.selected)
        activeobj = context.view_layer.objects.active
        lecleanselect = selector(self, context)
        for leselected in lecleanselect:
            leselected.select_set(True)
            context.view_layer.objects.active = leselected
            mat_params = [leselected, matsdone, "dothem"]
            done = foreachmat(self, context, mat_params)

            matsdone = done

        for obj in og_selection:
            obj.select_set(True)
        context.view_layer.objects.active = activeobj

        if not self.fromimportbutton:
            ShowMessageBox("Check Shader nodes panel", "Nodes created", 'FAKE_USER_ON')

        return {'FINISHED'}


class KOS_OT_assumename(popol, Operator):
    bl_idname = "kos.assumename"
    bl_label = ""
    bl_description = "Assume a probable filename "

    kospnumber: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        # return (context.object is not None)
        return True

    def execute(self, context):
        k = self.kospnumber
        scene = context.scene
        kosp = eval(f"scene.kosp{k}")
        kosvars = scene.kosvars
        lefolder = kosvars.kosdir
        prefix = kosvars.prefix
        fullext = kosp.mapext
        mapname = kosp.maplabels
        separator = kosvars.separator
        patternselected = int(kosvars.patterns)
        allexts = [fullext.capitalize(), fullext.upper(), fullext, ]
        for ext in allexts:
            params = [prefix, mapname, ext]
            patternslist = PatternsVariations.liste(None, context, params)
            supposed = patternslist[patternselected][1]

            kosp.probable = lefolder + supposed
            if os.path.isfile(kosp.probable):
                break

        return {'FINISHED'}


class GuessName():
    def testit(self, context, gs_params):
        scene = context.scene
        kosp = gs_params[0]
        keepat = gs_params[1]
        kosvars = scene.kosvars
        prefix = kosvars.prefix
        isindir = (os.path.basename(kosp.lefilename) in os.path.dirname(kosp.lefilename))
        # almost always True but better safe than sorry
        fullext = kosp.mapext
        allexts = [fullext, fullext.upper(), fullext.capitalize()]
        manual = kosp.manual
        mapname = kosp.maplabels
        isindir = False
        patternselected = int(kosvars.patterns)
        if not manual:

            for ext in allexts:

                if isindir:
                    break
                params = [prefix, mapname, ext]
                patterns = PatternsVariations.liste(None, context, params)
                supposed = patterns[patternselected][1]
                kosp.probable = kosvars.kosdir + supposed
                if os.path.isfile(kosp.probable):
                    kosp.lefilename = kosp.probable

                    kosp.probable = kosp.lefilename
                    isindir = True
                    break

                if not keepat:
                    for liner in patterns:
                        tentative = liner[1]
                        kosp.probable = kosvars.kosdir + tentative

                        if os.path.isfile(kosp.probable):
                            kosp.lefilename = kosp.probable
                            kosvars.patterns = liner[0]  # TODO reversepattern maybe
                            kosp.probable = kosp.lefilename
                            isindir = True

                            break

        return isindir


class KOS_OT_guessfilext(popol, Operator):
    bl_idname = "kos.guessfilext"
    bl_label = ""
    bl_description = "set kosp{linen}.mapext according to dir content"

    keepat: bpy.props.BoolProperty(default=False)
    linen: bpy.props.IntProperty()
    called: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        keepat = self.keepat
        linen = self.linen
        scene = context.scene
        kosp = eval(f"scene.kosp{linen}")
        manual = kosp.manual
        gs_params = [kosp, keepat]
        currentext = kosp.mapext
        isindir = GuessName.testit(self, context, gs_params)

        if not isindir and not manual:

            filetypesraw = extlist.givelist(self, context)
            filetypes = []
            for i in range(len(filetypesraw)):
                filetypes.append(filetypesraw[i][0])
            originalext = kosp.mapext
            for ext in filetypes:
                kosp.mapext = ext

                isindir = GuessName.testit(self, context, gs_params)

                if isindir:
                    break
            if not isindir:
                if not self.called:
                    toreport = "Could not guess file extension, File not found"
                    self.report({'INFO'}, toreport)
                kosp.mapext = originalext
        return {'FINISHED'}


class KOS_OT_checkmaps(popol, Operator):
    bl_idname = "kos.checkmaps"
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
        kosvars = scene.kosvars
        linen = self.linen
        notfromext = self.notfromext

        kosp = eval(f"scene.kosp{linen}")
        manual = kosp.manual
        expert = kosvars.expert
        prefix = kosvars.prefix
        sel = context.object
        mat = sel.active_material
        mat.use_nodes = True
        gs_params = [kosp, keepat]

        if self.lorigin == "plug" and not manual:
            kosp.probable = "reseted"

        isafile = os.path.isfile(kosp.probable)

        if not manual:

            gotafile = GuessName.testit(self, context, gs_params)

            if not gotafile:
                bpy.ops.kos.guessfilext(linen=linen)
            isafile = GuessName.testit(self, context, gs_params)

            if not isafile and self.called :
                toreport = kosp.probable + " not found "
                self.report({'INFO'}, toreport)
                __class__.bl_description = "No Image containing the keyword " + kosp.maplabels + " found , verify the Prefix, the Map name and/or the Maps Folder"

                if not prefix.isalnum():
                    toreport = "Prefix is empty"
                    self.report({'INFO'}, toreport)

                __class__.bl_description = "Set a non-empty Prefix in the Preferences (of this Addon Tab)"
            # necessary in order to update description
            unregister_class(__class__)
            register_class(__class__)

        if isafile:
            if self.called:
                toreport = kosp.probable + " detected in Maps Folder"
                self.report({'INFO'}, toreport)

            return {'FINISHED'}
        return {'CANCELLED'}


def move_existing(self, context, mov_params):
    scene = context.scene
    lematos = mov_params[0]
    lesurfaceshader = mov_params[1]
    nods = mov_params[2]
    kosvars = scene.kosvars
    leoldshader = mov_params[3]
    replace = kosvars.shader
    panelrows = kosvars.panelrows
    imgs = list(nod for nod in nods if nod.type == 'TEX_IMAGE')

    enabled = list(k for k in range(panelrows) if eval(f"bpy.context.scene.kosp{k}.labelbools"))
    adding = len(enabled)
    listofshadernodes = []  # TODO get a lish of all shadernodes
    ylocsall = []
    ylocsimg = []

    for nod in nods:
        replacedshader = replace and (nod != lesurfaceshader)
        if (nod in imgs) or replacedshader:
            ylocsimg.append(nod.location[1])
        ylocsall.append(nod.location[1])

    ylocsimg.sort()
    ylocsall.sort()
    distanceimgs = 0
    clustersize_y = 0
    newclustersize_y = 0
    distancenodes = 0
    if len(ylocsimg) > 1:
        distanceimgs = (ylocsimg[-1] - ylocsimg[0])
    if len(ylocsall) > 1:
        clustersize_y = (ylocsall[-1] - ylocsall[0])

    if bool(adding + int(replace)):
        existing = (nod for nod in nods if nod.type != "OUTPUT_MATERIAL" and not nod == lesurfaceshader)
        newclustersize_y = 888 * (adding / 2)
        if not adding > 0 and replace:
            newclustersize_y = 1024

        # addit = int((distanceimgs / (len(imgs) + adding)) * adding)
        # offsetter_y = 192 * (adding * 2 + len(imgs) * 2 )
        offsetter_y = newclustersize_y

        for nodez in existing:
            nodez.location = (nodez.location[0] - 512, nodez.location[1] + offsetter_y)

    return


def MapinLinks(self, context, mp_params):
    mapin = mp_params[0]
    nods = mp_params[1]
    ylocs = []
    connected = list(linked for linked in mapin.outputs[0].links if linked.is_valid)
    if len(connected) > 0:
        for linked in connected:
            ylocs.append(linked.to_node.location[1])
    else:
        for nod in nods:
            ylocs.append(nod.location[1])
    ylocs.sort()
    center = (ylocs[0] + ylocs[-1]) / 2
    return center


def surfaceshaderlinks(self, context, sl_params):
    lesurfaceshader = sl_params[0]
    nods = sl_params[1]
    ylocs = []
    connected = list(linked for linked in lesurfaceshader.inputs if linked.is_linked)
    if len(connected) > 0:
        for linked in connected:
            ylocs.append(linked.links[0].from_node.location[1])
    else:
        for nod in nods:
            ylocs.append(nod.location[1])
    ylocs.sort()
    center = (ylocs[0] + ylocs[-1]) / 2
    return center


def dothenodes(self, context, do_params):
    lesmaps = do_params[0]
    leschans = do_params[1]
    lematos = do_params[2]
    leoldshader = None
    scene = context.scene
    kosvars = scene.kosvars
    koshi = scene.koshi
    kosni = scene.kosni
    skipnormals = kosvars.skipnormals
    selectedshader = kosvars.shaderlist
    cutstomshd = selectedshader in kosni
    applytoall = kosvars.applyall

    if kosvars.eraseall:
        lematos.node_tree.nodes.clear()

    nods = lematos.node_tree.nodes
    treez = lematos.node_tree
    linkz = treez.links

    lesoutputs = list(lesnodes for lesnodes in nods if lesnodes.type == "OUTPUT_MATERIAL")
    for lesnodes in lesoutputs:
        if lesnodes.is_active_output:
            matos_output = lesnodes
    if not len(lesoutputs) > 0:
        matos_output = nods.new("ShaderNodeOutputMaterial")

    offsetter1_x = -404
    offsetter1_y = 0
    baseloc0_x = matos_output.location[0]
    baseloc0_y = matos_output.location[1]

    surfinput = matos_output.inputs['Surface']
    if surfinput.is_linked:
        lafirstconnection = surfinput.links[0].from_node
        invalidtypes = ["ADD_SHADER", "MIX_SHADER", "HOLDOUT"]
        invalidshader = lafirstconnection.type in invalidtypes

    else:
        lafirstconnection = None
        invalidshader = True
    leoldshader = lafirstconnection
    replaceshader = invalidshader or (kosvars.shader)

    if replaceshader:

        if cutstomshd:
            lenewshader = nods.new('ShaderNodeGroup')
            lenewshader.node_tree = bpy.data.node_groups[selectedshader]

        else:
            lenewshader = nods.new(selectedshader)
        linkz.new(lenewshader.outputs[0], matos_output.inputs[0])
        lesurfaceshader = lenewshader

    else:
        lesurfaceshader = lafirstconnection

    baseloc0_x = matos_output.location[0]
    baseloc0_y = matos_output.location[1]
    lesurfaceshader.location = (baseloc0_x + offsetter1_x * 2, baseloc0_y)
    base_x = lesurfaceshader.location[0]
    base_y = lesurfaceshader.location[1]

    mapin = None
    lescoord = None
    mapnumbr = 0
    mov_params = [lematos, lesurfaceshader, nods, leoldshader]

    move_existing(self, context, mov_params)

    if len(lesmaps) > 0:

        if not mapin:
            mapin = nods.new('ShaderNodeMapping')
            mapin.label = lematos.name + "Mapping"

        if not lescoord:
            lescoord = nods.new('ShaderNodeTexCoord')
            lescoord.label = lematos.name + "Coordinates"

        if not lescoord.outputs[0].is_linked:
            # lematos.node_tree.nodes['Texture Coordinate'].outputs['UV']
            linkz.new(lescoord.outputs['UV'], mapin.inputs['Vector'])

        line = (i for i in range(len(list(lesmaps))) if f"bpy.context.scene.kosp{i}.labelbools")

        for i in line:
            lamap = lesmaps[i]
            lechan = leschans[i]

            kosp = eval(f"scene.kosp{i}")
            manual = kosp.manual
            isdisplacement = ("Displacement" in lechan)
            islinked = (lechan != "0")
            isdispvector = 'Disp Vector' in lechan
            if manual:
                lamap = os.path.basename(kosp.lefilename)[:-4]
            isnormal = ("normal" in lamap or "Normal" in lamap)
            isheight = ("height" in lamap or "Height" in lamap)
            washn = "height" in lesmaps or "Height" in lesmaps or "normal" in lesmaps or "Normal" in lesmaps
            addextras = kosvars.extras and not (isnormal or isheight)
            colbool = ("Color" in lechan)
            emibool = ("Emission" in lechan)
            noramps = ["Subsurface Radius", "Normal", "Tangent"]
            innoramps = (lechan in noramps)
            okcurve = ((colbool or emibool) and not isdisplacement)
            okramp = (not (colbool or emibool) and (not lamap in noramps)) or (isdisplacement and isheight)
            offsetter_x = -312
            offsetter_y = -312

            lanewnode = nods.new(type="ShaderNodeTexImage")
            lanewnode.name = lamap
            lanewnode.label = lamap

            linkz.new(mapin.outputs[0], lanewnode.inputs['Vector'])

            if addextras:
                if okcurve:
                    lacurveramp = nods.new('ShaderNodeRGBCurve')
                    extranode = lacurveramp
                    extranode.label = extranode.name + lamap
                    linkz.new(lanewnode.outputs[0], lacurveramp.inputs[1])

                if okramp:
                    laramp = nods.new('ShaderNodeValToRGB')
                    extranode = laramp
                    linkz.new(lanewnode.outputs[0], laramp.inputs[0])

                    # linkz.new(lacurveramp.outputs[0] , matos_output.inputs[2])
                if okramp or okcurve:
                    extranode.label = extranode.name + lamap

            if isnormal and not skipnormals:
                normalmapnode = nods.new('ShaderNodeNormalMap')
                linkz.new(lanewnode.outputs[0], normalmapnode.inputs[1])

            if isheight and not skipnormals:

                bumpnode = nods.new('ShaderNodeBump')
                linkz.new(lanewnode.outputs[0], bumpnode.inputs[2])
                bumpnode.inputs[0].default_value = .5
                if addextras:
                    linkz.new(extranode.outputs[0], bumpnode.inputs[2])

            if islinked and not isdisplacement and not isdispvector:

                if isnormal and not skipnormals:
                    if isdisplacement:
                        linkz.new(normalmapnode.outputs[0], matos_output.inputs[2])

                    else:
                        linkz.new(normalmapnode.outputs[0], lesurfaceshader.inputs[lechan])

                if isheight and not skipnormals:
                    if isdisplacement:
                        linkz.new(bumpnode.outputs[0], matos_output.inputs[2])

                    else:
                        linkz.new(bumpnode.outputs[0], lesurfaceshader.inputs[lechan])

                if not (isheight or isnormal) or skipnormals:
                    if addextras:

                        linkz.new(extranode.outputs[0], lesurfaceshader.inputs[lechan])
                    else:
                        linkz.new(lanewnode.outputs[0], lesurfaceshader.inputs[lechan])

            if isdisplacement:
                dispmapnode = nods.new('ShaderNodeDisplacement')
                dispmapnode.location = (baseloc0_x - 256, baseloc0_y)
                linkz.new(dispmapnode.outputs[0], matos_output.inputs['Displacement'])
                if addextras:
                    linkz.new(extranode.outputs[0], dispmapnode.inputs['Height'])
                if isheight and not skipnormals:
                    pass
                if isnormal and not skipnormals:
                    linkz.new(normalmapnode.outputs[0], dispmapnode.inputs['Normal'])
                if (not isnormal or skipnormals) and not addextras:
                    linkz.new(lanewnode.outputs[0], dispmapnode.inputs['Height'])
            if isdispvector:  # TODO implement link sanity
                dispvectnode = nods.new('ShaderNodeVectorDisplacement')
                dispvectnode.location = (baseloc0_x - 256, baseloc0_y)
                linkz.new(dispvectnode.outputs[0], matos_output.inputs['Displacement'])
                if addextras:
                    linkz.new(extranode.outputs[0], dispvectnode.inputs['Vector'])
                if isnormal and not skipnormals:
                    linkz.new(normalmapnode.outputs[0], dispvectnode.inputs['Vector'])
                    # not sure it makes any sense
                if (not isnormal or skipnormals) and not addextras:
                    linkz.new(lanewnode.outputs[0], dispvectnode.inputs['Vector'])

            lanewnode.location = ((base_x + offsetter_x * (int(addextras) + int(isnormal or isheight) + 1)),
                                  (base_y + offsetter_y * mapnumbr))

            if addextras:  # again to be sure
                extranode.location = (
                    (base_x + offsetter_x * (int(isnormal or isheight) + 1)), (base_y + offsetter_y * mapnumbr))
            if isheight and not skipnormals:
                bumpnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
            if isnormal and not skipnormals:
                normalmapnode.location = (base_x + offsetter_x, base_y + offsetter_y * mapnumbr)
            mapnumbr += 1
        sl_params = [lesurfaceshader, nods]
        lesurfaceshader.location[1] = surfaceshaderlinks(self, context, sl_params) + 128  # just a bit higher
        lesurfaceshader.location[0] += 128
        matos_output.location[1] = lesurfaceshader.location[1]
        mapin.location = (base_x + offsetter_x * (int(addextras) + int(washn) + 2) + offsetter_x, base_y)
        lescoord.location = (mapin.location[0] + offsetter_x, mapin.location[1])
        mp_params = [mapin, nods]
        mapin.location[1] = MapinLinks(self, context, mp_params)
        lescoord.location[1] = mapin.location[1]
        # for nodez in nods:
        #     nodez.location[1] = nodez.location[1] - 156

    return


def plugthenodes(self, context, pg_params):
    lematerial = pg_params[0]
    index = pg_params[1]

    kosvars = context.scene.kosvars
    kosp = eval(f"context.scene.kosp{index}")
    manual = kosp.manual
    gofile = True
    if not manual:
        # bpy.ops.kos.assumename(kospnumber = index)
        gofile = (bpy.ops.kos.checkmaps(linen=index, lorigin="plug", called=True) == {'FINISHED'})
    lefilepath = kosp.lefilename

    imagename = os.path.basename(lefilepath)
    lamap = kosp.maplabels
    if manual:
        lamap = imagename[:-4]

    if lematerial.node_tree.nodes.find(lamap) > 0:

        if os.path.isfile(lefilepath) == True and gofile:
            bpy.ops.image.open(
                filepath=os.path.basename(lefilepath),
                directory=os.path.dirname(lefilepath),
                files=[{"name": os.path.basename(lefilepath), "name": os.path.basename(lefilepath)}],
                show_multiview=False
            )
            nodestofill = (nod for nod in lematerial.node_tree.nodes if nod.label == lamap)
            for nods in nodestofill:
                nods.image = bpy.data.images[imagename]
            toreport = "Texture file '" + imagename + "' assigned in "+ lematerial.name
            self.report({'INFO'}, toreport)
        else:
            toreport = "Texture '" + imagename + "' not found"
            self.report({'INFO'}, toreport)

    else:
        toreport = "node label " + lamap + " not found"
        self.report({'INFO'}, toreport)

    return


class KOS_OT_assignnodes(popol, Operator):
    bl_idname = "kos.assignnodes"
    bl_label = "Only Assign Images"
    bl_description = "import maps for all selected objects"

    fromimportbutton: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        scene = context.scene
        if len(scene.koshi) == 0:
            bpy.ops.kos.createdummy()
        laselection = list(context.view_layer.objects.selected)
        activeobj = context.view_layer.objects.active
        lecleanselect = selector(self, context)
        matsdone = []
        for leselected in lecleanselect:
            leselected.select_set(True)
            context.view_layer.objects.active = leselected

            mat_params = [leselected, matsdone, "plug"]
            done = foreachmat(self, context, mat_params)
            matsdone = done

        for obj in laselection:
            obj.select_set(True)
        context.view_layer.objects.active = activeobj
        if not self.fromimportbutton:

            pass

            # ShowMessageBox("All images loaded sucessfully", "Image Textures assigned", 'FAKE_USER_ON')
        return {'FINISHED'}


class KOS_OT_subimport(popol, Operator):
    bl_idname = "kos.subimport"
    bl_label = "Import Substance Maps"
    bl_description = "Import Texture Maps for active object"

    def execute(self, context):
        bpy.ops.kos.createnodes(fromimportbutton=True)
        bpy.ops.kos.assignnodes(fromimportbutton=True)
        # ShowMessageBox("Nodes created and Textures loaded", "Success !", 'FAKE_USER_ON')

        return {'FINISHED'}


class KOS_OT_addaline(popol, Operator):
    bl_idname = "kos.addaline"
    bl_label = ""
    bl_description = "Add a new map line below"

    linen: IntProperty(default=0)

    def execute(self, context):
        if len(context.scene.koshi) == 0:
            bpy.ops.kos.createdummy()
        context.scene.kosvars.panelrows += 1

        return {'FINISHED'}


class KOS_OT_removeline(popol, Operator):
    bl_idname = "kos.removeline"
    bl_label = ""
    bl_description = "Remove last Map from the list"

    marked: StringProperty(name="line n", default="KOS_PT_paneline1")

    def execute(self, context):
        if len(context.scene.koshi) == 0:
            bpy.ops.kos.createdummy()
        scene = context.scene
        context.scene.kosvars.panelrows -= 1
        kosp = eval(f"scene.kosp{scene.kosvars.panelrows}")
        kosp.manual = False
        kosp.labelbools = False

        context.view_layer.update()
        return {'FINISHED'}


class KosAddPresetBase:
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
            cls = KosAddPresetBase
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
        bpy.ops.kos.saveall()
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

            target_path = os.path.join("presets", self.preset_subdir)
            target_path = bpy.utils.user_resource('SCRIPTS',
                                                  target_path,
                                                  create=True)

            if not target_path:
                self.report({'WARNING'}, "Failed to create presets path")
                return {'CANCELLED'}

            filepath = os.path.join(target_path, filename) + ext

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
                    os.remove(filepath)
            except Exception as e:
                self.report({'ERROR'}, "Unable to remove preset: %r" % e)
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

            preset_menu_class.bl_label = "Presets"

        if hasattr(self, "post_cb"):
            self.post_cb(context)

        return {'FINISHED'}


class KOS_OT_addpreset(KosAddPresetBase, Operator):
    bl_idname = 'kos.addpreset'
    bl_label = 'Add A preset'
    preset_menu = 'KOS_MT_presetsmenu'

    # Common variable used for all preset values
    preset_defines = ['scene = bpy.context.scene',
                      'kosvars = scene.kosvars',
                      'bpy.ops.kos.saveall()',
                      ]
    # Properties to store in the preset
    preset_values = ['kosvars.shaderlist', 'kosvars.kosall',
                     'kosvars.kosdir', 'kosvars.separator',
                     'kosvars.customshader',
                     'kosvars.applyall', 'kosvars.eraseall',
                     'kosvars.extras', 'kosvars.shader',
                     ]
    # Directory to store the presets
    preset_subdir = 'kospresets'


class KOS_OT_createdummy(popol, Operator):
    bl_idname = "kos.createdummy"
    bl_label = "dummy creator"
    bl_description = "used to initialize some dynamic props"

    def execute(self, context):
        context.scene.koshi.clear()

        fetchedOutputs = []  #
        fetchedInputs = []  #
        fetchedShaders = []  #
        fetchedNodes = []  #
        fetchedObjects = []  #
        scene = context.scene
        scenename = str(scene.name_full)
        kosvars = scene.kosvars
        lashaderlist = Kosinit.exec(None, context)
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
        lenghtlist = 11  # only create nodes for the initial shaderlist aka kosinit

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

            newentry = context.scene.koshi.add()
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


class KOS_OT_saveall(popol, Operator):
    bl_idname = 'kos.saveall'
    bl_label = 'save all values'
    bl_description = 'Save all relevant vars'

    def execute(self, context):
        scene = context.scene
        kosvars = scene.kosvars
        arey = []
        for i in range(10):
            maplabels = eval(f"scene.kosp{i}").maplabels
            lechan = eval(f"scene.kosp{i}").inputsockets
            enabled = str(eval(f"scene.kosp{i}").labelbools)
            lineitems = [str(eval(f"scene.kosp{i}").name), maplabels, lechan, enabled]
            lineraw = "@\_/@".join(str(lx) for lx in lineitems)
            arey.append(lineraw)

        kosvars.kosall = "@-¯\(°_o)/¯-@".join(str(lx) for lx in arey)

        return {'FINISHED'}


class KOS_OT_loadall(popol, Operator):
    bl_idname = 'kos.loadall'
    bl_label = 'save all values'
    bl_description = 'load preset '

    def execute(self, context):

        scene = context.scene
        kosvars = scene.kosvars
        allraw = kosvars.kosall.split("@-¯\(°_o)/¯-@")
        allin = []
        for allitems in allraw:
            zob = allitems.split("@\_/@")
            allin.append(zob)
        for i in range(10):
            paneline = eval(f"scene.kosp{i}")
            paneline.maplabels = allin[i][1]
            paneline.inputsockets = allin[i][2]
            paneline.labelbools = bool(int(eval(allin[i][3])))
        return {'FINISHED'}


class KOS_MT_presetsmenu(Menu):
    # bl_idname = 'my.presetmenu'
    bl_label = 'Presets Menu'
    preset_subdir = 'kospresets'
    preset_operator = 'kos.execute_preset'
    draw = Menu.draw_preset


class KosExecutePreset(Operator):
    # """Execute a preset"""
    bl_idname = "kos.execute_preset"
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

        from os.path import basename, splitext
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = KOS_MT_presetsmenu  # getattr(bpy.types, self.menu_idname)
        preset_class.bl_label = bpy.path.display_name(basename(filepath))

        ext = splitext(filepath)[1].lower()

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
        bpy.ops.kos.loadall()
        return {'FINISHED'}
