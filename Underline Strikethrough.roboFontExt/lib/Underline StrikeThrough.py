from AppKit import NSApp, NSAppearance, NSAppearanceNameDarkAqua
import ezui
import merz
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
from mojo.UI import getDefault, CurrentFontWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault
from lib.tools.unicodeTools import GN2UV
from fontTools.misc.roundTools import otRound


def getKey(val, di):
    for key, value in di.items():
        if val == value:
            return key


extensionKey = "com.typefounding.underlineStrikethrough"


class UnderlineStrikethrough(Subscriber, ezui.WindowController):

    def build(self):
        content = """
        * HorizontalStack
        > |-----|                  @table
        > |     |
        > |-----|

        > ---

        > * VerticalStack

        >> * MerzView              @merzView

        >> * HorizontalStack       @textArea
        >>> [_ _]                  @testText
        >>> * ColorWell            @colorWell

        >> ---

        >> * HorizontalStack

        >>> !!!!! Underline        @ulLabel

        >>> * VerticalStack

        >>>> * TwoColumnForm       @underlineForm

        >>>>> : Thickness:
        >>>>> * HorizontalStack
        >>>>>> [_ _]               @ulThicknessText
        >>>>>> (Sync)              @syncThickULButton

        >>>>> ---

        >>>>> : Position:
        >>>>> [_ _]                @ulPosText
        >>>>> (Descender)          @ulDescButton
        >>>>> (Below Descender)    @ulBelowDescButton

        >>> ---

        >>> !!!!! Strikethrough    @stLabel

        >>> * VerticalStack

        >>>> * TwoColumnForm       @strikeForm

        >>>>> : Thickness:
        >>>>> * HorizontalStack
        >>>>>> [_ _]               @stThicknessText
        >>>>>> (Sync)              @syncThickSTButton

        >>>>> ---

        >>>>> : Position:
        >>>>> [_ _]                @stPosText
        >>>>> (Mid Cap-Height)     @stMidCapButton
        >>>>> (Mid X-Height)       @stMidXButton

        ---
        """
        footer = """
        !- All values have been written into their respective UFOs.  @setAllLabel 
        (Set Values)               @setAllButton
        """

        tableWidth  = 225
        fieldWidth  = 55
        headerWidth = 120
        buttonWidth = 118
        titleWidth  = 70
        itemWidth   = buttonWidth
        syncWidth   = fieldWidth

        descriptionData = dict(
            table=dict(
                items=[],
                width=tableWidth
            ),
            merzView=dict(
                backgroundColor=(1, 1, 1, 1),
                delegate=self,
                height=300
            ),
            testText=dict(
                width="fill",
                height=24,
            ),
            colorWell=dict(
                width=fieldWidth,
                height=24,
            ),
            ulThicknessText=dict(
                valueType="integer",
                valueWidth=fieldWidth,
                # valueIncrement=1
            ),
            ulPosText=dict(
                valueType="integer",
                valueWidth=fieldWidth,
                # valueIncrement=1
            ),
            syncThickSTButton=dict(
                width = syncWidth,
            ),
            syncThickULButton=dict(
                width = syncWidth,
            ),
            underlineForm=dict(
                titleColumnWidth=titleWidth,
                itemColumnWidth=itemWidth,
            ),
            strikeForm=dict(
                titleColumnWidth=titleWidth,
                itemColumnWidth=itemWidth,
            ),
            stThicknessText=dict(
                valueType="integer",
                valueWidth=fieldWidth,
                # valueIncrement=1
            ),
            stPosText=dict(
                valueType="integer",
                valueWidth=fieldWidth,
                # valueIncrement=1
            ),
            ulLabel=dict(
                width=headerWidth
            ),
            stLabel=dict(
                width=headerWidth
            ),
            ulDescButton=dict(
                width=buttonWidth,
            ),
            ulBelowDescButton=dict(
                width=buttonWidth,
            ),
            stMidCapButton=dict(
                width=buttonWidth,
            ),
            stMidXButton=dict(
                width=buttonWidth,
            ),
            setAllButton=dict(
                width=tableWidth,
                gravity="leading"
            ),
        )
        self.w = ezui.EZWindow(
            content=content,
            title="Underline Strikethrough",
            descriptionData=descriptionData,
            controller=self,
            size="auto",
            footer=footer,
            # tabLoops=["ulThicknessText", "stThicknessText", "ulPosText", "stPosText"],  # Doesn't seem to work.
        )

        # Set the position of the window to relate to the front-most font overview window.
        if CurrentFontWindow():
            fw_x, fw_y, _, _ = CurrentFontWindow().w.getPosSize()
        else:
            fw_x, fw_y = 300, 300
        _, _, w_w, w_h = self.w.getPosSize()
        self.w.setPosSize((fw_x + 50, fw_y + 50, w_w, w_h))

        self.merzView = self.w.getItem("merzView")

        self.w.getItem("setAllLabel").show(False)

        self.testString = getExtensionDefault(extensionKey + ".testString", fallback="Hloxtps")
        self.w.getItem("testText").set(self.testString)

        self.underlineThickness = {}
        self.underlinePosition  = {} # The top of the underline
        self.strikeThickness    = {}
        self.strikePosition     = {}

        self.strokeColor = getExtensionDefault(extensionKey + ".strokeColor", fallback=(0,0,0,1))
        self.w.getItem("colorWell").set(self.strokeColor)

        self.setPreviewColors()

    def acceptsFirstResponder(self, sender):
        return True

    # def magnifyWithEvent(self, sender, event):
    #     print("magnifying...")
    #     print(event)
    #     # self.container.setContainerScale(scale)

    def started(self):
        self.w.open()

        # Select the first font on open
        self.selectedFonts = []
        if AllFonts():
            self.fonts = AllFonts()
            self.selectedFonts = [self.fonts[0]]

        self.updateFontList()
        self.updateTextFields()
        self.updatePreview()

    # Change the preview colors if the app switches to dark mode.
    def roboFontAppearanceChanged(self, info):
        self.setPreviewColors()
        self.updatePreview()

    def roboFontDidChangePreferences(self, info):
        self.setPreviewColors()
        self.updatePreview()

    def setPreviewColors(self):
        self.bgColor = getDefault("spaceCenterBackgroundColor")
        if NSApp().appearance() == NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua):
            self.bgColor = getDefault("spaceCenterBackgroundColor.dark")

        self.fgColor = getDefault("spaceCenterGlyphColor")
        if NSApp().appearance() == NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua):
            self.fgColor = getDefault("spaceCenterGlyphColor.dark")

    def destroy(self):
        self.selectedFonts = []

    def clearInternalDictionary(self):
        self.underlineThickness = {}
        self.underlinePosition  = {}
        self.strikeThickness    = {}
        self.strikePosition     = {}

    def fontDocumentDidOpen(self, info):
        self.updateFontList()

    def fontDocumentDidOpenNew(self, info):
        self.updateFontList()

    # Doesn't seem to work as intended without a delay.
    fontDocumentDidSaveDelay = 1

    def fontDocumentDidSave(self, info):
        self.updateFontList()

    def fontDocumentDidClose(self, info):
        self.updateFontList()

    def getFontIdentifier(self, font):
        # Try to keep track of the font using its path, but if it doesn't have a path (not saved yet)...
        if font.path:
            identifier = font.path
        # Use the title on its window.
        else:
            identifier = font.fontWindow().w.getNSWindow().title()
        return identifier

    def getFontDisplayName(self, font):
        if font.info.familyName and font.info.styleName:
            displayName = font.info.familyName + " - " + font.info.styleName
        else:
            displayName = font.fontWindow().w.getNSWindow().title()
        return displayName

    def updateFontList(self):
        """
        Updates the font list upon open and when new UFOs 
        are opened/closed while the extension is open.
        """
        self.w.getItem("setAllLabel").show(False)
        self.fonts = AllFonts()
        self.fontsList = []
        self.clearInternalDictionary()  # Leave behind any old "identifiers"

        if self.fonts:
            for font in self.fonts:
                # Update the font list panel itself
                displayName = self.getFontDisplayName(font)
                self.fontsList.append(displayName)

                # Update internal account of data when new font is opened/closed
                dictionaryToValue = [
                    (self.underlineThickness , font.info.postscriptUnderlineThickness),
                    (self.strikeThickness    , font.info.openTypeOS2StrikeoutSize),
                    (self.strikePosition     , font.info.openTypeOS2StrikeoutPosition)
                    ]
                fontIdentifier = self.getFontIdentifier(font)
                for dictionary, value in dictionaryToValue:
                    if fontIdentifier not in dictionary.keys():
                        if value:
                            dictionary.update({fontIdentifier: value})
                        else:
                            dictionary.update({fontIdentifier: None})
                # Deal with underline position
                if "public.openTypePostUnderlinePosition" in font.lib:
                    self.underlinePosition.update({fontIdentifier: font.lib["public.openTypePostUnderlinePosition"]})
                # If font doesn't have that lib key set, but is using fontmake, use fontmake behavior
                elif getDefault("fontCompilerTool") == "fontmake":
                    self.underlinePosition.update({fontIdentifier: font.info.postscriptUnderlinePosition})
                # If not that, do the math to get position
                elif font.info.postscriptUnderlinePosition and font.info.postscriptUnderlineThickness:
                    ul = font.info.postscriptUnderlinePosition + font.info.postscriptUnderlineThickness / 2
                    self.underlinePosition.update({fontIdentifier: ul})
                # If a position but no thickness, top is the position
                elif font.info.postscriptUnderlinePosition:
                    self.underlinePosition.update({fontIdentifier: font.info.postscriptUnderlinePosition})
                # If no position or thickness, value is None
                else:
                    self.underlinePosition.update({fontIdentifier: None})

        # Set the font list in the UI
        self.w.getItem("table").set(self.fontsList)

        # Select what was selected before
        fontIndexesToSelect = []
        if len(self.fonts) == 1:  # If there"s only one font, select that one.
            fontIndexesToSelect = [0]
        else:
            for font in self.selectedFonts:
                for i, afFont in enumerate(self.fonts):
                    if font == afFont:
                        fontIndexesToSelect.append(i)
        self.selectedFonts = [self.fonts[index] for index in fontIndexesToSelect]
        self.w.getItem("table").setSelectedIndexes(fontIndexesToSelect)

        self.updateTextFields()
        self.updatePreview()

    def getValueIfConsistent(self, fonts, dictionary):
        """
        Check whether the fonts selected in list have the same value for any given attribute. 
        If so, returns that value. If not, return an empty string.
        """
        if fonts and dictionary:
            value = dictionary[self.getFontIdentifier(fonts[0])]
            for font in fonts:
                fontIdentifier = self.getFontIdentifier(font)
                checkValue = dictionary[fontIdentifier]
                if checkValue != value:
                    return ""
            return value
        else:
            return ""

    def updateTextFields(self):
        self.w.getItem("setAllLabel").show(False)
        self.w.getItem("ulThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.underlineThickness))
        self.w.getItem("ulPosText").set(self.getValueIfConsistent(self.selectedFonts, self.underlinePosition))
        self.w.getItem("stThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.strikeThickness))
        self.w.getItem("stPosText").set(self.getValueIfConsistent(self.selectedFonts, self.strikePosition))

    def testTextCallback(self, sender):
        self.testString = sender.get()
        setExtensionDefault(extensionKey + ".testString", self.testString)
        self.updatePreview()

    def tableSelectionCallback(self, sender):
        selectedIndexes = sender.getSelectedIndexes()
        self.selectedFonts = [self.fonts[index] for index in selectedIndexes]
        self.updateTextFields()
        self.updatePreview()

    def ulThicknessTextCallback(self, sender):
        value = sender.get()
        if value != "-":
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.underlineThickness[fontIdentifier] = value
            self.updatePreview()

    def syncThickULButtonCallback(self, sender):
        """Matches strikethrough thickness value"""
        value = self.w.getItem("stThicknessText").get()
        if value:
            value = int(value)
            self.w.getItem("ulThicknessText").set(value)
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.underlineThickness[fontIdentifier] = value
            self.updatePreview()

    def ulPosTextCallback(self, sender):
        value = sender.get()
        if value != "-":
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.underlinePosition[fontIdentifier] = value
            self.updatePreview()

    def ulDescButtonCallback(self, sender):
        """Snaps the underline value to bottom-align with the descender."""
        for font in self.selectedFonts:
            fontIdentifier = self.getFontIdentifier(font)
            value = None
            if self.underlineThickness[fontIdentifier]:
                value = int(font.info.descender + self.underlineThickness[fontIdentifier])
            self.underlinePosition[fontIdentifier] = value
        self.updatePreview()
        self.updateTextFields()

    def ulBelowDescButtonCallback(self, sender):
        """Snaps the underline value to an underline thickness distance below the descender."""
        for font in self.selectedFonts:
            fontIdentifier = self.getFontIdentifier(font)
            value = None
            if self.underlineThickness[fontIdentifier]:
                value = int(font.info.descender - self.underlineThickness[fontIdentifier])
            self.underlinePosition[fontIdentifier] = value
        self.updatePreview()
        self.updateTextFields()

    def stThicknessTextCallback(self, sender):
        value = sender.get()
        if value != "-":
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.strikeThickness[fontIdentifier] = value
            self.updatePreview()

    def syncThickSTButtonCallback(self, sender):
        """Matches underline thickness value"""
        value = self.w.getItem("ulThicknessText").get()
        if value:
            value = int(value)
            self.w.getItem("stThicknessText").set(value)
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.strikeThickness[fontIdentifier] = value
            self.updatePreview()

    def stPosTextCallback(self, sender):
        value = sender.get()
        if value != "-":
            for font in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(font)
                self.strikePosition[fontIdentifier] = value
            self.updatePreview()

    def stMidCapButtonCallback(self, sender):
        """Snaps the strikethrough value to the middle of the cap-height"""
        for font in self.selectedFonts:
            fontIdentifier = self.getFontIdentifier(font)
            value = None
            if self.strikeThickness[fontIdentifier]:
                value = int(font.info.capHeight / 2 + self.strikeThickness[fontIdentifier] / 2)
            self.strikePosition[fontIdentifier] = value
        self.updatePreview()
        self.updateTextFields()

    def stMidXButtonCallback(self, sender):
        """Snaps the strikethrough value to the middle of the x-height"""
        for font in self.selectedFonts:
            fontIdentifier = self.getFontIdentifier(font)
            value = None
            if self.strikeThickness[fontIdentifier]:
                value = int(font.info.xHeight / 2 + self.strikeThickness[fontIdentifier] / 2)
            self.strikePosition[fontIdentifier] = value
        self.updatePreview()
        self.updateTextFields()

    def colorWellCallback(self, sender):
        self.strokeColor = sender.get()
        setExtensionDefault(extensionKey + ".strokeColor", self.strokeColor)
        self.updatePreview()

    def updatePreview(self):
        """Updates the Merz View which shows the test string with underline and strikethrough applied."""
        self.w.getItem("setAllLabel").show(False)

        self.container = self.merzView.getMerzContainer()
        self.container.setBackgroundColor(self.bgColor)
        self.container.clearSublayers()
        merzW, merzH = self.container.getSize()
        margin = 300

        if self.selectedFonts:
            for viewFont in self.selectedFonts:
                fontIdentifier = self.getFontIdentifier(viewFont)
                baseline = merzH / 2 - 200
                viewScale = merzH / (viewFont.info.unitsPerEm + margin*2) * 0.75

                self.localFGColor   = self.fgColor
                self.localStrokeColor = self.strokeColor
                if viewFont != self.selectedFonts[0]:
                    r, g, b, a = self.localFGColor
                    self.localFGColor   = r, g, b, 0.25
                    r, g, b, a = self.strokeColor
                    self.localStrokeColor = r, g, b, 0.25

                cursor = margin
                for char in self.testString:
                    glyphLayer = self.container.appendPathSublayer(
                        position=(cursor, baseline),
                        fillColor=self.localFGColor,
                    )
                    gName = getKey(ord(char), GN2UV)
                    glyph = viewFont[gName]
                    glyphPath = glyph.getRepresentation("merz.CGPath")

                    glyphLayer.setPath(glyphPath)
                    cursor += glyph.width

                if self.underlinePosition[fontIdentifier] and self.underlineThickness[fontIdentifier]:
                    underlineLine = self.container.appendLineSublayer(
                        startPoint=(margin, baseline + self.underlinePosition[fontIdentifier] - self.underlineThickness[fontIdentifier] / 2),
                        endPoint=(cursor, baseline + self.underlinePosition[fontIdentifier] - self.underlineThickness[fontIdentifier] / 2),
                        strokeWidth=self.underlineThickness[fontIdentifier] * viewScale,
                        strokeColor=self.localStrokeColor
                    )

                if self.strikePosition[fontIdentifier] and self.strikeThickness[fontIdentifier]:
                    strikethroughLine = self.container.appendLineSublayer(
                        startPoint=(margin, baseline + self.strikePosition[fontIdentifier] - self.strikeThickness[fontIdentifier] / 2),
                        endPoint=(cursor, baseline + self.strikePosition[fontIdentifier] - self.strikeThickness[fontIdentifier] / 2),
                        strokeWidth=self.strikeThickness[fontIdentifier] * viewScale,
                        strokeColor=self.localStrokeColor
                    )

            self.container.addSublayerScaleTransformation(viewScale, name="scale", center=(0, merzH/2))

    def roundInteger(self, value):
        """Same as int(), but accepts None."""
        if value is None:
            return None
        return otRound(value)

    def setAllButtonCallback(self, sender):
        """
        Uses the tool’s dictionary we"ve been building, and writes those values into the UFO files themselves.
        Each UFO will have its own corresponding values.
        """
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition
        for font in self.fonts:
            fontIdentifier = self.getFontIdentifier(font)
            font.info.postscriptUnderlineThickness = self.roundInteger(uT[fontIdentifier])
            # Math only works if there is a underline thickness
            if uT[fontIdentifier]:
                font.info.postscriptUnderlinePosition  = self.roundInteger(uP[fontIdentifier] - uT[fontIdentifier] / 2)
            else:
                font.info.postscriptUnderlinePosition = self.roundInteger(uP[fontIdentifier])
            font.lib["public.openTypePostUnderlinePosition"] = self.roundInteger(uP[fontIdentifier])
            font.info.openTypeOS2StrikeoutSize     = self.roundInteger(sT[fontIdentifier])
            font.info.openTypeOS2StrikeoutPosition = self.roundInteger(sP[fontIdentifier])
        self.w.getItem("setAllLabel").show(True)


registerRoboFontSubscriber(UnderlineStrikethrough)
