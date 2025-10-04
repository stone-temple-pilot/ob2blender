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

## Features
* Batch exporting - edit and export multiple models at a time. One file per highlighted object, filename is object name. **Beware of overwriting files in your directory.**
* Supports double-sided faces. Make sure to tick on Backface Culling to view them properly.
* Priority, face labels, vertex labels, and alpha are all assigned as attributes; see below.
* Smooth- and flat-shading support.
* Automatically convert a material's color to a specified RGB15 value with the naming scheme '15_value'
	* Ex. naming a material 15_4390 will automatically change its color on export to RGB15 value 4390.
	* Range: 0 to 32767.
	* Intended for use with Lost City Model and Anim Editor's color picker tool, as well as recolors in Lost City config files.

## Constraints
* Material colors rely on diffuse_color, i.e. viewport display color. Set all material colors there.
* All vertex values (x, y, z) will round to the nearest integer when exporting. The integer values of an imported .ob2 in Blender are the true values encoded in the file. 
	Press N in Blender to view the values of a selected vertex.
* Face labels, vertex labels, priorities, and alpha are all controlled by the Attribute system.
	Import a model, and click on Data -> Attributes to view what data the model has. Note that all integers have a range of 0 to 255.
	* *VSKIN*: Vertex labels: vertex, integer
	* *TSKIN*: Face labels: face, integer
	* *PRI*: Face priorities: face, integer
	* *ALPHA*: face alpha: face, integer
	Warning: do not change the names or value types of these attributes, or the data will not export.
	You can assign Attributes through Mesh -> Set Attribute to assign what you have highlighted. Click multiple faces or vertices to assign multiple.
* If you do not know which attributes to assign to your model, you can always refer to LostCity Model and Anim Editor or import another model to use as reference.
* Ex. import a model, highlight the attribute you would like to check, click a vertex/face and then Mesh -> Set Attribute. Usually, it will reveal the attribute value already set there.
* You can also use Spreadsheet view, though it goes by face/vertex ID and is not very user-friendly.

## Known Issues
* Textures not yet implemented. Exporting a textured object will yield an error.
* Chathead exporting does not yet work due to 'pop from empty set' error.
* RGB15 conversion converts color but can show up as 'undefined' in Lost City Model and Anim Editor color picker tool. Likely due to rounding error.
* Checking attribute values kind of sucks. Looking for a better solution.
* Useless error saying something about NoneType appears. Models are still exported just fine.

---

*This plugin is developed independently and is not affiliated with Jagex or RuneScape in any way.*

*A big thanks to Pazaz, AmVoidGuy, and the rest of the Lost City community for inspiring this project.*

*Special thanks to Tamateea for providing the basis of this project.*





