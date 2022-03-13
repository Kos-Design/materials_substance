[doc](../doc) / [Home](Home.md) Options [Preferences](Preferences.md)

**Options**

***

![Blender-Substance-Texture-Importer_Options-Panel_picture](http://kos-design.com/images/wikipics/Options.png  "Options_Panel")

Set of Options displayed at the bottom of the Add-on panel allowing some flexibility in the workflow by modifying the behaviour of the add-on.
All options are Off by default, tick the checkbox next to it to enable an option before executing the script.

***
**Replace Shader**\
![Blender-Substance-Texture-Importer_Replace-Shader_option_picture](http://kos-design.com/images/wikipics/replace-shader.png  "Replace Shader option")\
Enable to replace the current shader node by the one selected in the dropdown menu next to it. When enabled the Input Socket lists will be updated according to the Shader selected (by default: Principled BSDF)

 ![Blender-Substance-Texture-Importer_shader-substitute-list_picture](http://kos-design.com/images/wikipics/shader-substitute-list.png  "shader-substitute-list")\
 Content of the dropdown menu right next to the "Replace Shader" option.
Select a shader node in this list to use as a replacement when the option "Replace Shader" is enabled. 
(or if no valid shader node is connected to a material output node in the target Material)
**Note**: to have your Custom Shader Node to appear in this list you must enable the option "Enable Custom Shader"

***

**Apply to all visible objects**\
![Blender-Substance-Texture-Importer_Replace-Shader_apply-to-all visible-objects_option_picture](http://kos-design.com/images/wikipics/apply-to-all-visible-objects.png  "option_apply-to-all visible-objects")\
Enable this option to import the texture images on all visible object regardless of the selection. (Usefull to preserve your current selection)


***

**Apply to active object only**\
![Blender-Substance-Texture-Importer_Replace-Shader_apply-to-active-object-only_option_picture](http://kos-design.com/images/wikipics/apply-to-active-object-only.png  "option_apply-to-active-object-only")\
Enable this option to import the texture images only for the active object regardless of the selection. (Usefull to preserve your current selection) 


***

**Skip normal map detection**\
![Blender-Substance-Texture-Importer_Replace-Shader_skip-normal-map-detection_option_picture](http://kos-design.com/images/wikipics/skip-normal-map-detection.png  "option_skip-normal-map-detection")\
By Default the script will detect a Normal map as such if it finds the keyword "normal" in the fields enabled for each map type. It will then add a Normal map convertor node in-between the image and the selected input socket during the nodes creation.
Enable this option to disable this detection and allow the script to plug the normal map texture directly into the selected shader input socket. (Usefull when using a custom shader node with a normal map convertor already included in the Nodegroup) 

***

**Enable Custom Shaders**\
![Blender-Substance-Texture-Importer_Replace-Shader_enable-custom-shader_option_picture](http://kos-design.com/images/wikipics/enable-custom-shader.png "option_enable-custom-shader")\
Enable this option to append your custom node groups to the list of replacement shader nodes (next to the "Replace Shader" option)
To be valid your custom shader nodegroup must contain at least one BSDF output and one input socket. 
(**Note:** Re-toggle this option if you update your nodegroup afterward to refresh the script.)

***

**Clear nodes from material**\
![Blender-Substance-Texture-Importer_Replace-Shader_clear-nodes-from-material_option_picture](http://kos-design.com/images/wikipics/clear-nodes-from-material.png "option_clear-nodes-from-material")\
Enable this option to remove all existing nodes in the target materials before importing the image textures. 
(**Note**: this will also enable the "Replace Shader" option)

***

**Attach Curves and Ramps**\
![Blender-Substance-Texture-Importer_Replace-Shader_attach-curves-and-ramps_option_picture](http://kos-design.com/images/wikipics/attach-curves-and-ramps.png  "option_attach-curves-and-ramps")\
Enable this option to add a RGB-Curve or a ColorRamp in-between the image map and the input socket. If the texture map name contains the keyword "Color", a RGB-curve will be added, otherwise a ColorRamp will be added. Unless the map type is detected as a normal map, then no RGB-curve or ColorRamp will be added.
(**Note: **This option potentially breaks the "pure P.B.R. workflow" but could be usefull to tweak the texture map values.) 

***

**Only active Material**\
![Blender-Substance-Texture-Importer_Replace-Shader_only-active-material_option_picture](http://kos-design.com/images/wikipics/only-active-material.png  "option_only-active-material")\
Enable this option to only import the texture images for the active material of each selected object.
***

**Fix copied Material name**\
![Blender-Substance-Texture-Importer_Replace-Shader_fix-material-name_option_picture](http://kos-design.com/images/wikipics/fix-material-name.png  "option_fix-material-name")\
Enable this option to allow the script to ignore the .001, .002 etc. suffixes in duplicated material names.
Typically, if you are making some tests with a duplicated material of the one you used to create the texture maps, you may want to activate this feature. For example if an image is called "prefix_Material_MapName.exr" but then your target material is "Material.001", you should enable this option.
