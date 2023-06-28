from AppKit import NSApp, NSAppearance, NSAppearanceNameDarkAqua
import ezui
import merz
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
from mojo.UI import getDefault
from mojo.extensions import getExtensionDefault, setExtensionDefault
from defconAppKit.tools.textSplitter import splitText
from lib.tools.unicodeTools import GN2UV


def getKey(val, di): 
    for key, value in di.items(): 
        if val == value: 
            return key
            
extensionKey = 'com.typefounding.underlineStrikethrough'

class UnderlineStrikethrough(Subscriber, ezui.WindowController):

    def build(self):
        content = """
        * HorizontalStack  
        > |-----|              @table
        > |     |
        > |-----|
        
        > * VerticalStack
        >> * MerzView          @merzView
        
        >> * HorizontalStack
        >>> [_ _]              @testText
        >>> * ColorWell        @colorWell
        
        >> ---
        
        >> * HorizontalStack
        
        >>> * TwoColumnForm    @form1
        >>>> : Underline:
        >>>> [_ _]             @ulThicknessText
        >>>> [_ _]             @ulPosText
        
        >>> ---
        
        >>> * TwoColumnForm    @form2
        >>>> : Strikethrough:
        >>>> [_ _]             @stThicknessText
        >>>> [_ _]             @stPosText
        
        >>> ---
        
        >>> * VerticalStack
        >>>> (Copy to All)     @copyAllButton
        >>>> !- Copied!           @copiedLabel
        
        ---
        """
        footer="""
        !- All values have been written into their respective UFOs.  @setAllLabel 
        (Set Values)           @setAllButton
        """
        
        titleWidth = 88
        itemWidth = 120
        fieldWidth = 40
        buttonWidth = 120
        
        descriptionData = dict(
            table=dict(
                items=[],
                width=220,
            ),
            merzView=dict(
                backgroundColor=(1, 1, 1, 1),
                delegate=self,
                height=300
            ),
            testText=dict(
                width='fill'
            ),
            colorWell=dict(
                width=50,
            ),
            form1=dict(
                titleColumnWidth=titleWidth,
                itemColumnWidth=itemWidth
            ),
            form2=dict(
                titleColumnWidth=titleWidth,
                itemColumnWidth=itemWidth
            ),
            ulThicknessText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
                trailingText="Thickness",
            ),
            ulPosText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
                trailingText="Position",
            ),
            stThicknessText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
                trailingText="Thickness",
            ),
            stPosText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
                trailingText="Position",
            ),
            copyAllButton=dict(
                width=buttonWidth,
            ),
            copiedText=dict(
                width=buttonWidth,
                alignment='justified',
            ),
            setAllButton=dict(
                width=buttonWidth,
            ),
        )
        self.w = ezui.EZWindow(
            content=content,
            title='Underline Strikethrough',
            descriptionData=descriptionData,
            controller=self,
            size='auto',
            footer=footer
        )
        
        self.merzView = self.w.getItem("merzView")
        print(dir(self.merzView))
        
        self.strokeColor = (0,0,0,1)
        self.w.getItem('colorWell').set(self.strokeColor)
        
        self.w.getItem('copiedLabel').show(False)
        self.w.getItem('setAllLabel').show(False)
        
        self.testString = "Hlpxtys"
        self.w.getItem('testText').set(self.testString)
        
        self.lineColor = getDefault("spaceCenterGlyphColor") # Light mode by default
        if NSApp().appearance() == NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua):
            self.lineColor = getDefault("spaceCenterGlyphColor.dark")  # Dark mode foreground color
            
        self.underlineThickness = {}
        self.underlinePosition  = {}
        self.strikeThickness    = {}
        self.strikePosition     = {}
        
        self.selectedFonts = []
        
        # Select the first one in the list
        self.refreshFontList()
        if self.fonts:
            self.selectedFonts = [self.fonts[0]]
            
            for font in self.fonts:
                self.underlineThickness[font.path] = font.info.postscriptUnderlineThickness
                self.underlinePosition[font.path]  = font.info.postscriptUnderlinePosition
                self.strikeThickness[font.path]    = font.info.openTypeOS2StrikeoutSize
                self.strikePosition[font.path]     = font.info.openTypeOS2StrikeoutPosition
            
            self.w.getItem("table").setSelectedIndexes([0])            
            self.refreshTextFields()
            self.updateView()
            
        self.strokeColor = getExtensionDefault(extensionKey + '.strokeColor', fallback=(0,0,0,1))
        self.w.getItem('colorWell').set(self.strokeColor)
        
    def started(self):
        self.w.open()
        
    def destroy(self):
        self.selectedFonts = []
        self.underlineThickness = {}
        self.underlinePosition  = {}
        self.strikeThickness    = {}
        self.strikePosition     = {}
        
    def fontDocumentDidOpen(self, info):
        self.refreshFontList()
    
    def fontDocumentDidClose(self, info):
        self.refreshFontList()
        
    def refreshFontList(self):
        self.w.getItem('copiedLabel').show(False)
        self.w.getItem('setAllLabel').show(False)
        self.fonts = AllFonts()
        self.fonts_list = []
        print(self.selectedFonts)
        if self.fonts:
            
            # Update internal account of data when new font is added            
            for font in self.fonts:
                dictionaryToValue = [
                    (self.underlineThickness , font.info.postscriptUnderlineThickness),
                    (self.underlinePosition  , font.info.postscriptUnderlinePosition),
                    (self.strikeThickness    , font.info.openTypeOS2StrikeoutSize),
                    (self.strikePosition     , font.info.openTypeOS2StrikeoutPosition)
                    ]
                for dictionary, value in dictionaryToValue:
                    if font.path not in dictionary.keys() and value:
                        dictionary.update({font.path: value}) 
                
            for font in self.fonts:
                if font.info.familyName and font.info.styleName:
                    self.fonts_list.append(font.info.familyName + " - " + font.info.styleName)
                else:
                    self.fonts_list.append('Untitled')
            # Set the font list in the UI
            self.w.getItem("table").set(self.fonts_list)
            
            # Select what was selected before
            fontIndexesToSelect = []
            for font in self.selectedFonts:
                for i, afFont in enumerate(self.fonts):
                    if font == afFont:
                        fontIndexesToSelect.append(i)
                    
            self.w.getItem("table").setSelectedIndexes(fontIndexesToSelect)
            self.refreshTextFields()
                    
            print("self.selectedFonts", self.selectedFonts)
            print("all listed", self.w.getItem("table").get())
        
    def getValueIfConsistent(self, fonts, dictionary):
        '''
        Check whether the fonts selected in list have the same value for any given attribute. If so, returns that value. If not, return empty.
        '''
        if fonts and dictionary:
            value = dictionary[fonts[0].path]
            for font in fonts:
                checkValue = dictionary[font.path]
                if checkValue != value:
                    return ''
            return value
        else:
            return ''
            
    def refreshTextFields(self):
        self.w.getItem('copiedLabel').show(False)
        self.w.getItem('setAllLabel').show(False)
        self.w.getItem("ulThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.underlineThickness))
        self.w.getItem("ulPosText").set(self.getValueIfConsistent(self.selectedFonts, self.underlinePosition))
        self.w.getItem("stThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.strikeThickness))
        self.w.getItem("stPosText").set(self.getValueIfConsistent(self.selectedFonts, self.strikePosition))

    def testTextCallback(self, sender):
        self.testString = sender.get()
        self.updateView()

    def tableSelectionCallback(self, sender):
        selectedIndexes = sender.getSelectedIndexes()
        self.selectedFonts = [self.fonts[index] for index in selectedIndexes]
        print("self.selectedFonts", self.selectedFonts)
        self.refreshTextFields()
        self.updateView()
        self.w.getItem('copiedLabel').show(False)  # Hide the "Copied" text if it's not already.

    def ulThicknessTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.underlineThickness[font.path] = value
                self.updateView()

    def ulPosTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.underlinePosition[font.path] = value
                self.updateView()

    def stThicknessTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.strikeThickness[font.path] = value
                self.updateView()

    def stPosTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.strikePosition[font.path] = value
                self.updateView()
                
    def colorWellCallback(self, sender):
        self.strokeColor = sender.get()
        setExtensionDefault(extensionKey + '.strokeColor', self.strokeColor)
        self.updateView()
        

    def updateView(self):
        self.w.getItem('copiedLabel').show(False)
        self.w.getItem('setAllLabel').show(False)
        
        container = self.merzView.getMerzContainer()
        container.clearSublayers()
        merzW, merzH = container.getSize()
        margin = 300
        
        if self.selectedFonts:
            for viewFont in self.selectedFonts:
                self.localFillColor   = (0,0,0,1)
                self.localStrokeColor = self.strokeColor
                if viewFont != self.selectedFonts[0]:
                    self.localFillColor = (0,0,0,0.2)
                    r,g,b,a  = self.strokeColor
                    self.localStrokeColor = r,g,b,0.2
                baseline = merzH / 2
                viewScale = merzH / (viewFont.info.unitsPerEm + margin*2) * 0.75
            
                cursor = margin
                for char in self.testString:
                    glyphLayer = container.appendPathSublayer(
                        position=(cursor, baseline),
                        fillColor=self.localFillColor,
                    )
                    gName = getKey(ord(char), GN2UV)
                    glyph = viewFont[gName]
                    glyphPath = glyph.getRepresentation("merz.CGPath")
            
                    glyphLayer.setPath(glyphPath)
                    cursor += glyph.width
                
                underlineLine = container.appendLineSublayer(
                    startPoint=(margin, baseline + self.underlinePosition[viewFont.path]),
                    endPoint=(cursor, baseline + self.underlinePosition[viewFont.path]),
                    strokeWidth=self.underlineThickness[viewFont.path] * viewScale,
                    strokeColor=self.localStrokeColor
                )
            
                strikethroughLine = container.appendLineSublayer(
                    startPoint=(margin, baseline + self.strikePosition[viewFont.path] - self.strikeThickness[viewFont.path] / 2),
                    endPoint=(cursor, baseline + self.strikePosition[viewFont.path] - self.strikeThickness[viewFont.path] / 2),
                    strokeWidth=self.strikeThickness[viewFont.path] * viewScale,
                    strokeColor=self.localStrokeColor
                )
            
                # # Figure out the scales from a horizontal and vertical perspective...
                # scaleH = merzH / (viewFont.info.ascender - viewFont.info.descender + margin*2)
                # scaleW = merzW / (cursor + margin)
                # # Choose the smallest
                # container.addSublayerScaleTransformation(min([scaleH, scaleW]), name='scale', center=(0, merzH/2))
            container.addSublayerScaleTransformation(viewScale, name='scale', center=(0, merzH/2))
        
    def setAllButtonCallback(self, sender):
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition
        for font in self.fonts:
            font.info.postscriptUnderlineThickness = uT[font.path]
            font.info.postscriptUnderlinePosition  = uP[font.path]
            font.info.openTypeOS2StrikeoutSize     = sT[font.path]
            font.info.openTypeOS2StrikeoutPosition = sP[font.path]
        self.w.getItem('setAllLabel').show(True)

    def copyAllButtonCallback(self, sender):
        for font in self.fonts:
            self.underlineThickness[font.path] = self.getValueIfConsistent(self.selectedFonts, self.underlineThickness)
            self.underlinePosition[font.path]  = self.getValueIfConsistent(self.selectedFonts, self.underlinePosition)
            self.strikeThickness[font.path]    = self.getValueIfConsistent(self.selectedFonts, self.strikeThickness)
            self.strikePosition[font.path]     = self.getValueIfConsistent(self.selectedFonts, self.strikePosition)
        self.w.getItem('copiedLabel').show(True)


registerRoboFontSubscriber(UnderlineStrikethrough)