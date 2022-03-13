Blender Substance Texture Importer
------------------------------------

.. figure:: http://kos-design.com/images/plugthum.cropped.png
   :scale: 100 %
   :align: center

-----------
Description:
-----------

Blender addon designed to import Substance Painter Textures and other similar P.B.R maps into Blender 3D easily. The script imports the texture maps from the choosen folder and assigns them to the selected objects according to their material name.
The texture maps exported from Substance Painter or similar tools usually have a name pattern containing the material name a prefix(object name) and the texture map name (BaseColor, Metallic, Roughness, Normal etc.). 
The script attempts to guess the name pattern from the texture folder content and assigns the relevant texture maps to the Shaders of the selected objects. (Manual assignment is also possible for special cases)

Lets say the selected texture folder contains a set of P.B.R. texture maps named “prefix_FirstMaterialName_BaseColor.png”, “prefix_FirstMaterialName_Roughness.png”, “prefix_FirstMaterialName_Metallic.exr”, “prefix_SecondMaterialName_BaseColor.png” etc.
(or another kind of name pattern containing a Material name and a Texture map name) 
You only need to activate the relevant line in the addon panel (and edit the texture map name if needed) to batch import the image textures into their associated shaders on all selected objects at once.

Installation:
---------------

`TLDR Add-on Installation Video Tutorial <https://youtu.be/lumrnhikSOg>`__

https://youtu.be/lumrnhikSOg

Download the git archive zip from https://github.com/Kos-Design/materials_substance/raw/master/Blender_Substance_Texture_Importer.zip
and install it in Blender via Edit > Preferences > Add-ons > Install an Addon
Note : if you download the files manually from git, place them ( __init__.py, Operators.py, Panels.py and PropertyGroups.py ) in a folder called "materials_substance" inside your Blender Add-Ons directory.
It will appear in the Add-Ons list, enable it by ticking the checkbox in front of “Material: Blender Substance Texture Importer”
That’s it the plugin is ready to use.


How-to:
-------

`Basic Features & How-to Video tutorial <https://youtu.be/45rky8J_0us>`__

https://youtu.be/45rky8J_0us

`Documentation <doc/Home.md>`__
(still in progress) 

A Panel labeled Substance Texture Importer is displayed under the Shader Settings in the Material Tab. 

First choose the Directory containing the Texture Maps to be imported.
(It is best to keep the texture images in a separate folder to help the script images name detection.) 

License
-------

This add-on is released under the `GNU/GPL v3.0 license <https://github.com/Kos-Design/materials_substance/blob/master/LICENSE>`__

