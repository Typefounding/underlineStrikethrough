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
        > |-----|                 @table
        > |     |
        > |-----|
        
        > * VerticalStack
        >> * MerzView             @merzView
        
        >> * HorizontalStack
        >>> [_ _]                 @testText
        >>> * ColorWell           @colorWell
        
        >> ---
        
        >> * HorizontalStack
        
        >>> !!!!! Underline
        >>> * TwoColumnForm       @form1
        
        >>>> : Thickness:
        >>>> [_ _]                @ulThicknessText
        
        >>>> : Position:
        >>>> [_ _]                @ulPosText
        
        >>>> : 
        >>>> (Descender)          @ulDescButton
        >>>> (Below Descender)    @ulBelowDescButton
        
        >>> ---
        
        >>> !!!!! Strikethrough
        >>> * TwoColumnForm       @form2
        
        >>>> : Thickness:
        >>>> [_ _]                @stThicknessText
        
        >>>> : Position:
        >>>> [_ _]                @stPosText
        
        >>>> : 
        >>>> (Mid-Cap-Height)     @stMidCapButton
        >>>> (Mid-X-Height)       @stMidXButton
        
        ---
        """
        footer="""
        !- All values have been written into their respective UFOs.  @setAllLabel 
        (Set Values)              @setAllButton
        """
        
        tableWidth  = 225
        titleWidth  = 70
        itemWidth   = 120
        fieldWidth  = 55
        
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
                width='fill'
            ),
            colorWell=dict(
                width=fieldWidth,
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
            ),
            ulPosText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
            ),
            stThicknessText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
            ),
            stPosText=dict(
                valueType='integer',
                valueWidth=fieldWidth,
            ),
            ulDescButton=dict(
                width=itemWidth,
            ),
            ulBelowDescButton=dict(
                width=itemWidth,
            ),
            stMidCapButton=dict(
                width=itemWidth,
            ),
            stMidXButton=dict(
                width=itemWidth,
            ),
            setAllButton=dict(
                width=tableWidth,
                gravity='leading'
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
        
        self.strokeColor = (0,0,0,1)
        self.w.getItem('colorWell').set(self.strokeColor)
        
        self.w.getItem('setAllLabel').show(False)
        
        self.testString = getExtensionDefault(extensionKey + '.testString', fallback="Hloxtps")
        self.w.getItem('testText').set(self.testString)
        
        self.lineColor = getDefault("spaceCenterGlyphColor") # Light mode by default
        if NSApp().appearance() == NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua):
            self.lineColor = getDefault("spaceCenterGlyphColor.dark")  # Dark mode foreground color
            
        self.underlineThickness = {}
        self.underlinePosition  = {}
        self.strikeThickness    = {}
        self.strikePosition     = {}
        
        self.strokeColor = getExtensionDefault(extensionKey + '.strokeColor', fallback=(0,0,0,1))
        self.w.getItem('colorWell').set(self.strokeColor)
        
    def started(self):
        self.w.open()
        
        self.fonts = AllFonts()
        self.selectedFonts = []
        if self.fonts:
            self.selectedFonts = [self.fonts[0]]
            self.updateFontList()          
            self.updateTextFields()
            self.updatePreview()
        
    def destroy(self):
        self.selectedFonts = []
        self.underlineThickness = {}
        self.underlinePosition  = {}
        self.strikeThickness    = {}
        self.strikePosition     = {}
        
    def fontDocumentDidOpen(self, info):
        self.updateFontList()
    
    def fontDocumentDidClose(self, info):
        self.updateFontList()
        
    def updateFontList(self):
        '''
        Updates the font list upon open and when new UFOs 
        are opened/closed while the extension is open.
        '''
        self.w.getItem('setAllLabel').show(False)
        self.fonts = AllFonts()
        self.fontsList = []
        
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
                    self.fontsList.append(font.info.familyName + " - " + font.info.styleName)
                else:
                    self.fontsList.append('Untitled')
            # Set the font list in the UI
            self.w.getItem("table").set(self.fontsList)
            
            # Select what was selected before
            fontIndexesToSelect = []
            for font in self.selectedFonts:
                for i, afFont in enumerate(self.fonts):
                    if font == afFont:
                        fontIndexesToSelect.append(i)
                    
            self.w.getItem("table").setSelectedIndexes(fontIndexesToSelect)
            self.updateTextFields()
        
    def getValueIfConsistent(self, fonts, dictionary):
        '''
        Check whether the fonts selected in list have the same value for any given attribute. 
        If so, returns that value. If not, return an empty string.
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
            
    def updateTextFields(self):
        self.w.getItem('setAllLabel').show(False)
        self.w.getItem("ulThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.underlineThickness))
        self.w.getItem("ulPosText").set(self.getValueIfConsistent(self.selectedFonts, self.underlinePosition))
        self.w.getItem("stThicknessText").set(self.getValueIfConsistent(self.selectedFonts, self.strikeThickness))
        self.w.getItem("stPosText").set(self.getValueIfConsistent(self.selectedFonts, self.strikePosition))

    def testTextCallback(self, sender):
        self.testString = sender.get()
        setExtensionDefault(extensionKey + '.testString', self.testString)
        self.updatePreview()

    def tableSelectionCallback(self, sender):
        selectedIndexes = sender.getSelectedIndexes()
        self.selectedFonts = [self.fonts[index] for index in selectedIndexes]
        self.updateTextFields()
        self.updatePreview()

    def ulThicknessTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.underlineThickness[font.path] = value
            self.updatePreview()

    def ulPosTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.underlinePosition[font.path] = value
            self.updatePreview()
            
    def ulDescButtonCallback(self, sender):
        '''Snaps the underline value to bottom-align with the descender.'''
        for font in self.selectedFonts:
            value = font.info.descender + self.underlineThickness[font.path] / 2
            self.underlinePosition[font.path] = value
        self.updatePreview()
        self.updateTextFields()
        
    def ulBelowDescButtonCallback(self, sender):
        '''Snaps the underline value to an underline thickness distance below the descender.'''
        for font in self.selectedFonts:
            value = font.info.descender - self.underlineThickness[font.path]
            self.underlinePosition[font.path] = value
        self.updatePreview()
        self.updateTextFields()

    def stThicknessTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.strikeThickness[font.path] = value
            self.updatePreview()

    def stPosTextCallback(self, sender):
        value = sender.get()
        if value != '-':
            for font in self.selectedFonts:
                self.strikePosition[font.path] = value
            self.updatePreview()
            
    def stMidCapButtonCallback(self, sender):
        '''Snaps the strikethrough value to the middle of the cap-height'''
        for font in self.selectedFonts:
            value = font.info.capHeight / 2 + self.strikeThickness[font.path] / 2
            self.strikePosition[font.path] = value
        self.updatePreview()
        self.updateTextFields()
            
    def stMidXButtonCallback(self, sender):
        '''Snaps the strikethrough value to the middle of the x-height'''
        for font in self.selectedFonts:
            value = font.info.xHeight / 2 + self.strikeThickness[font.path] / 2
            self.strikePosition[font.path] = value
        self.updatePreview()
        self.updateTextFields()
                
    def colorWellCallback(self, sender):
        self.strokeColor = sender.get()
        setExtensionDefault(extensionKey + '.strokeColor', self.strokeColor)
        self.updatePreview()
        

    def updatePreview(self):
        '''
        Updates the Merz View which shows the test string with underline and strikethrough applied.
        '''
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
                baseline = merzH / 2 - 200
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
            
            container.addSublayerScaleTransformation(viewScale, name='scale', center=(0, merzH/2))
        
    def setAllButtonCallback(self, sender):
        '''
        Use the tool’s dictionary we've been building, and write those values into the UFO files themselves.
        Each UFO will have its own corresponding values.
        '''
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition
        for font in self.fonts:
            font.info.postscriptUnderlineThickness = int(uT[font.path])
            font.info.postscriptUnderlinePosition  = int(uP[font.path])
            font.info.openTypeOS2StrikeoutSize     = int(sT[font.path])
            font.info.openTypeOS2StrikeoutPosition = int(sP[font.path])
        self.w.getItem('setAllLabel').show(True)


registerRoboFontSubscriber(UnderlineStrikethrough)