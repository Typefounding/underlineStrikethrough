Underline Strikethrough
=======================

A simple RoboFont extension for setting underline and strikethrough values in any open UFO(s).

## User Interface:

<img src="./_images/user_interface.png"  width="600">

### List View
This lists all UFOs that were open when you opened Underline Strikethrough.

### Strikethrough
- **Thickness:** The thickness of the strikethrough line. This corresponds to `font.info.openTypeOS2StrikeoutSize`. 
- **Position:** The position of the strikethrough line (the top of the line). This corresponds to `font.info.openTypeOS2StrikeoutPosition`. 

Read [here](https://learn.microsoft.com/en-us/typography/opentype/spec/os2) for more guidance on setting these values.

### Underline
- **Thickness:** The thickness of the underline. This corresponds to `font.info.postscriptUnderlineThickness`. 
- **Position:** The position of the underline (the top of the line). This corresponds to `font.info.postscriptUnderlinePosition`. 

Read [here](https://learn.microsoft.com/en-us/typography/opentype/spec/post) for more guidance on setting these values.

### Testing text
This is the text that you would like displayed in the view above. Default is `Hlaetgys`.

### Buttons
- **Apply to current:** This will take all entered values currently on display and actually write them into the corresponding UFO.
- **Apply to all:** This will take all entered values currently on display and actually write them into all UFOs listed in Underline Strikethrough’s user interface.



