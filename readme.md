<img width="969" height="524" alt="image" src="https://github.com/user-attachments/assets/f26a9666-e021-4a4f-b4f3-19db8c7dc47f" />

## Description
This add-on allows you to import, edit and export old format RuneScape models (.ob2 and .dat) all within Blender!
Built on Blender 4.5.

This project is in alpha. Not all features are fully implemented yet, see 'Known Issues' below.

Optimized for use with Lost City: https://github.com/LostCityRS/Server
 
This add-on is based off of RuneBlend by Tamatea: https://github.com/tamateea/RuneBlend
 
It is also tailored for use alongside AmVoidGuy's Lost City Model and Anim Editor: https://github.com/AmVoidGuy/LostCityModelAndAnimEditor

Companion thread on Lost City forums: https://lostcity.rs/t/ob2blender-lost-city-model-addon-for-blender/10972

## Installation Instructions
1. **Installation:** Download the plugin and install it in Blender following the standard plugin installation process.
   * **You may need to rename the folder manually, i.e. ob2blender-main to ob2blender.**
3. **Importing Models:** Select file->import/export->Runescape Model (.ob2)

## Basic Instructions
1. Import an .ob2 format model using Import -> RuneScape Model (.ob2).
2. Edit to your heart's desire.
3. Select the object you want to export. When you export, the file name will use the name of the object.
	* Example: if your object is named model_399_obj, it will be exported as model_399_obj.ob2
	* *Important*: this add-on supports batch exporting. Meaning, all objects will be exported as individual .ob2 files, named as before. **Beware of overwriting files in your directory.**

Assuming no errors, your model should work in-game when implemented!

<img width="799" height="611" alt="image" src="https://github.com/user-attachments/assets/d57b20d0-4f92-418d-88b8-8f019ae7be9f" />

## Features
* Batch exporting - edit and export multiple models at a time. One file per highlighted object, filename is object name. **Beware of overwriting files in your directory.**
* Supports exporting double-sided faces. Make sure to tick on Backface Culling to view them properly.
* New toolbar to facilitate vertex and face labeling, as well as HSL16/RGB15 color tools useful for RuneScape.
* Priority, face labels, vertex labels, and alpha are all assigned as attributes; see below.
* Smooth- and flat-shading support.
* Automatically convert a material's color to a specified RGB15 value with the naming scheme '15_value'
	* Ex. naming a material 15_4390 will automatically change its color on export to RGB15 value 4390.
	* Range: 0 to 32767.
	* Intended for use with Lost City Model and Anim Editor's color picker tool, as well as recolors in Lost City config files.
    * You can also create an RGB15 material using the toolbar!

## Instructions
* Material colors rely on diffuse_color, i.e. viewport display color. Set all material colors there.
* All vertex values (x, y, z) will round to the nearest integer when exporting. The integer values of an imported .ob2 in Blender are the true values encoded in the file. 
	Press N in Blender to view the values of a selected vertex.
* Face labels, vertex labels, priorities, and alpha are all controlled by the Attribute system.
	Import a model, and click on Data -> Attributes to view what data the model has. Note that all integers have a range of 0 to 255.
	* *VSKIN*: Vertex labels: vertex, integer
	* *TSKIN*: Face labels: face, integer
	* *PRI*: Face priorities: face, integer
	* *ALPHA*: face alpha: face, integer

*Warning: do not change the names or value types of these attributes, or the data will not export.
	You can add attributes to the mesh and also assign them through Mesh -> Set Attribute to assign what you have highlighted. Click multiple faces or vertices to assign multiple.
	The added Toolbar (N -> click OB2 tab) streamlines this process for you. Try it out!
	<img width="339" height="652" alt="image" src="https://github.com/user-attachments/assets/076c4c73-6ba7-4091-bb7e-ce17a51aa3c1" />

* If you do not know which attributes to assign to your model, you can always refer to LostCity Model and Anim Editor or import another model to use as reference.
* Ex. import a model, highlight the attribute you would like to check, click a vertex/face and then Mesh -> Set Attribute. Usually, it will reveal the attribute value already set there.
* You can also use Spreadsheet view, though it goes by face/vertex ID and is not necessarily user-friendly.

# Textures
* Create a new material for your texture. On the material, go to Surface -> yellow button on Base Color -> Image Texture <img width="840" height="670" alt="image" src="https://github.com/user-attachments/assets/f75c4eb3-6c26-4b46-b5c6-6368eec86092" />
* Select a texture. In your ob2blender installation folder, there are already 60 textures in there from vanilla RuneScape, and they are all named 1.png - 60.png. Select the one you wish to use. **The name of your texture MUST be an integer from 0-255 or your model will not export. This is because RuneScape IDs texture images as 0-255 from the cache.**
* Apply the textures to desired faces, and UV unwrap in the left window. For more information on UV editing in Blender, there are many tutorials online.
Assuming everything was done properly, your textured model should render correctly in-game. If you are lost on where to start, I would recommend opening up a vanilla textured model e.g. model_301_obj_wear.ob2 from the cache and going off from there. 


## Known Issues
* Sometimes, when importing an .ob2 file, vertex 0 is degenerate and unselectable. **Beware**: Certain operations on geometry including this vertex, like using Knife on an edge connected to it, will cause Blender to crash. <img width="484" height="490" alt="image" src="https://github.com/user-attachments/assets/171ffc32-22ea-479f-8840-467327312465" />

*Solution: put a new vertex at the same position and merge. It will not affect the rest of your model, but make sure the VSKIN attribute is the same if it matters.
* Models are mirrored horizontally compared to how they are imported in Lost City Model and Anim Editor. Please bear this in mind when making things like arm and leg models.
* RGB15 conversion can be janky - likely due to off-by-one rounding errors.
* Texture implementation is not yet perfect - RuneScape uses a so-called PMN or vector texturing system as opposed to conventional UV, which Blender uses, which can cause complications with conversion. Some faces with texture assigned may lose them. Working on solutions to these problems.

---

*This plugin is developed independently and is not affiliated with Jagex or RuneScape in any way.*

*A big thanks to Pazaz, AmVoidGuy, and the rest of the Lost City community for inspiring this project.*

*Special thanks to Tamateea for providing the basis of this project.*











