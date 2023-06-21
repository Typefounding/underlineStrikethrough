from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.UI import MultiLineView
from mojo.events import addObserver, removeObserver
from mojo.roboFont import AllFonts, CurrentFont
from mojo.drawingTools import *
from defconAppKit.tools.textSplitter import splitText

from lib.UI.integerEditText import NumberEditText

def listFontNames(fontList):
    return [fontName(font) for font in fontList]

def fontName(font):
    familyName = font.info.familyName
    styleName = font.info.styleName
    if familyName is None: font.info.familyName = familyName = 'Unnamed Font'
    if styleName is None: font.info.styleName = styleName = 'Unnamed style'
    return ' > '.join([familyName, styleName])

class FontList(List):

    def __init__(self, posSize, fontList, callback):
        fontNames = listFontNames(fontList)
        super(FontList, self).__init__(posSize, fontNames, allowsMultipleSelection=False,
            allowsEmptySelection=False, enableDelete=False, selectionCallback=self.updateSelectedFonts)
        self.fonts = fontList
        self.selection = None
        self.callback = callback

    def update(self, fontList=None):
        if fontList is None: self.fonts = AllFonts()
        elif fontList is not None: self.fonts = fontList
        self.set(listFontNames(self.fonts))

    def updateSelectedFonts(self, info):
        self.selection = [self.fonts[i] for i in info.getSelection()]
        self.callback(self.selection[0])

    def selectedFonts(self):
        return self.selection

    def select(self, thisFont):
        for i, font in enumerate(self.fonts):
            if thisFont == font:
                self.setSelection([i])

class UnderlineStrikethroughPreview(BaseWindowController):

    def __init__(self):
        self.fonts = AllFonts()
        self.font = CurrentFont()

        self.testString = "Hlaetgys"

        self.underlineThickness = {}
        self.underlinePosition = {}
        self.strikeThickness = {}
        self.strikePosition = {}

        for font in self.fonts:
            self.underlineThickness[font.path] = font.info.postscriptUnderlineThickness
            self.underlinePosition[font.path] = font.info.postscriptUnderlinePosition
            self.strikeThickness[font.path] = font.info.openTypeOS2StrikeoutSize
            self.strikePosition[font.path] = font.info.openTypeOS2StrikeoutPosition

        # create a window
        self.w = Window((900, 450), "Underline and Strikethrough", minSize=(775, 350))

        # add the preview to the window
        self.w.preview = MultiLineView((270, 10, -10, -175), pointSize=100, hasVerticalScroller=False)

        # labels
        self.w.textStrikethroughTitle = TextBox((275, -165, -10, 17), "Strikethrough")
        self.w.textStrikeThickness = TextBox((278, -115, -10, 17), "Thickness", sizeStyle='small')
        self.w.textStrikePos = TextBox((351, -115, -10, 17), "Position", sizeStyle='small')
        self.w.textUnderlineTitle = TextBox((470, -165, -10, 17), "Underline")
        self.w.textUnderThickness = TextBox((473, -115, -10, 17), "Thickness", sizeStyle='small')
        self.w.textUnderPos = TextBox((546, -115, -10, 17), "Position", sizeStyle='small')
        self.w.textTestText = TextBox((278, -47, -10, 17), "Testing text", sizeStyle='small')

        # data
        # NumberEditText defaults: allowFloat=True, allowNegative=True, allowEmpty=True, minimum=None, maximum=None, decimals=2
        self.w.strike = NumberEditText((277, -140, 70, 22), callback=self.strikeCallback, allowFloat=False, allowNegative=False)
        self.w.strikePos = NumberEditText((350, -140, 70, 22), callback=self.strikePosCallback, allowFloat=False)
        self.w.under = NumberEditText((472, -140, 70, 22), callback=self.underCallback, allowFloat=False, allowNegative=False)
        self.w.underPos = NumberEditText((545, -140, 70, 22), callback=self.underPosCallback, allowFloat=False)
        self.w.testText = EditText((277, -72, 143, 22), text=self.testString, callback=self.testTextCallback)

        # add font list to window
        self.w.fontList = FontList((10, 10, 250, -10), self.fonts, self.updateFont)

        # apply
        self.w.set = Button((645, -139, 120, 20), "Apply to current", callback=self.applySingleCallback)
        self.w.applyAll = Button((645, -109, 120, 20), "Apply to all", callback=self.applyAllCallback)

        # set UI
        self.setUI()

        # subscribe to drawing callback in a multi line view
        addObserver(self, "drawLines", "spaceCenterDraw")

        # setup base behavior (from the defcon BaseWindowController)
        self.setUpBaseWindowBehavior()

        # open the window
        self.w.open()


    def setUI(self):
        self.w.strike.set(self.strikeThickness[self.font.path])
        self.w.strikePos.set(self.strikePosition[self.font.path])
        self.w.under.set(self.underlineThickness[self.font.path])
        self.w.underPos.set(self.underlinePosition[self.font.path])

        marginGlyph = self.font['space']
        self.w.preview.setFont(self.font)
        self.testGlyphs = []
        self.testGlyphs.append(self.font['space'])
        charmap = self.font.getCharacterMapping()

        testGlyphNames = splitText(self.testString, charmap)
        for gn in testGlyphNames:
            if gn in self.font:
                self.testGlyphs.append(self.font[gn])
        self.testGlyphs.append(self.font['space'])
        self.w.preview.set(self.testGlyphs)

    def testTextCallback(self, sender):
        self.testString = sender.get()
        self.setUI()

    def updateFont(self, font):
        self.font = font
        self.setUI()

    def strikeCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.strikeThickness[self.font.path] = value
            self.updateView()

    def applyAllCallback(self, sender):
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition
        cf = self.font

        for font in self.fonts:
            font.info.postscriptUnderlineThickness = uT[cf.path]
            uT[font.path] = uT[cf.path]
            font.info.postscriptUnderlinePosition = uP[cf.path]
            uP[font.path] = uP[cf.path]
            font.info.openTypeOS2StrikeoutSize = sT[cf.path]
            sT[font.path] = sT[cf.path]
            font.info.openTypeOS2StrikeoutPosition = sP[cf.path]
            sP[font.path] = sP[cf.path]


    def applySingleCallback(self, sender):
        font = self.font
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition

        font.info.postscriptUnderlineThickness = uT[font.path]
        font.info.postscriptUnderlinePosition = uP[font.path]
        font.info.openTypeOS2StrikeoutSize = sT[font.path]
        font.info.openTypeOS2StrikeoutPosition = sP[font.path]


    def strikePosCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.strikePosition[self.font.path] = value
            self.updateView()

    def underCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.underlineThickness[self.font.path] = value
            self.updateView()

    def underPosCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.underlinePosition[self.font.path] = value
            self.updateView()

    def updateView(self):
        self.w.preview.contentView().refresh()

    def windowCloseCallback(self, sender):
        super(UnderlineStrikethroughPreview, self).windowCloseCallback(sender)
        removeObserver(self, "spaceCenterDraw")

    def drawLines(self, notification):
        glyph = notification["glyph"]
        if glyph:
            fill(0)
            if self.underlinePosition[self.font.path] is not None and self.underlineThickness[self.font.path] is not None:
                underlineY = self.underlinePosition[self.font.path] - self.underlineThickness[self.font.path] / 2
                rect(-10, underlineY, glyph.width+20, self.underlineThickness[self.font.path])
            if self.strikePosition[self.font.path] is not None and self.strikeThickness[self.font.path] is not None:
                strikeY = self.strikePosition[self.font.path] - self.strikeThickness[self.font.path]
                rect(-10, strikeY, glyph.width+20, self.strikeThickness[self.font.path])



OpenWindow(UnderlineStrikethroughPreview)
