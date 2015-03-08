from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.fontList import FontList
from mojo.UI import MultiLineView
from mojo.events import addObserver, removeObserver
from mojo.roboFont import AllFonts, CurrentFont
from mojo.drawingTools import *
from robofab.interface.all.dialogs import Message
from defconAppKit.tools.textSplitter import splitText

from lib.UI.integerEditText import NumberEditText

class UnderlineStrikethroughPreview(BaseWindowController):

    def __init__(self):
        self.fonts = AllFonts()
        self.font = CurrentFont()

        self.testString = "Hlaetgys"

        # Callbacks get grumpy if the window isn't opened yet. Ask Tal/Frederick if there is a better
        # way of doing this
        self.windowOpen = False


        # create a window
        self.w = FloatingWindow((900, 450), "Underline and Strikethrough", minSize=(775, 350))

        # add font list to window
        self.w.fontList = FontList((10, 10, 250, -10), self.fonts, selectionCallback=self.selectionCallback, allowsMultipleSelection=False, allowsEmptySelection=False, enableDelete=False)

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

        # apply
        self.w.set = Button((645, -139, 120, 20), "Set values", callback=self.setCallback)
        self.w.applyAll = Button((645, -109, 120, 20), "Apply to all", callback=self.applyAllCallback)
        self.w.applySingle = Button((645, -79, 120, 20), "Apply to current", callback=self.applySingleCallback)

        # set UI
        self.setUI()

        # subscribe to drawing callback in a multi line view
        addObserver(self, "drawLines", "spaceCenterDraw")

        # setup base behavior (from the defcon BaseWindowController)
        self.setUpBaseWindowBehavior()

        # open the window
        self.w.open()
        self.windowOpen = True


    def setUI(self):
        self.underlineThickness = self.font.info.postscriptUnderlineThickness
        self.underlinePosition = self.font.info.postscriptUnderlinePosition
        self.strikeThickness = self.font.info.openTypeOS2StrikeoutSize
        self.strikePosition = self.font.info.openTypeOS2StrikeoutPosition

        self.w.strike.set(self.strikeThickness)
        self.w.strikePos.set(self.strikePosition)
        self.w.under.set(self.underlineThickness)
        self.w.underPos.set(self.underlinePosition)

        self.w.preview.setFont(self.font)
        self.testGlyphs = []
        self.testGlyphs.append(self.font['space'])
        charmap = self.font.getCharacterMapping()
        self.testGlyphNames = splitText(self.testString, charmap)
        for gn in self.testGlyphNames:
            if gn in self.font:
                self.testGlyphs.append(self.font[gn])
        self.testGlyphs.append(self.font['space'])
        self.w.preview.set(self.testGlyphs)

    def testTextCallback(self, sender):
        self.testString = sender.get()
        self.setUI()

    def selectionCallback(self, sender):
        index = sender.getSelection()
        if len(index) != 0:
            if self.font != sender[index[0]] and self.windowOpen:
                self.font = sender[index[0]]
                self.setUI()


    def setCallback(self, sender):
        self.font.info.postscriptUnderlineThickness = self.underlineThickness
        self.font.info.postscriptUnderlinePosition = self.underlinePosition
        self.font.info.openTypeOS2StrikeoutSize = self.strikeThickness
        self.font.info.openTypeOS2StrikeoutPosition = self.strikePosition

    def strikeCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.strikeThickness = value
            self.updateView()

    def applyAllCallback(self, sender):
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition

        for font in self.fonts:
            font.info.postscriptUnderlineThickness = uT
            font.info.postscriptUnderlinePosition = uP
            font.info.openTypeOS2StrikeoutSize = sT
            font.info.openTypeOS2StrikeoutPosition = sP


    def applySingleCallback(self, sender):
        font = self.font
        uT = self.underlineThickness
        uP = self.underlinePosition
        sT = self.strikeThickness
        sP = self.strikePosition

        font.info.postscriptUnderlineThickness = uT
        font.info.postscriptUnderlinePosition = uP
        font.info.openTypeOS2StrikeoutSize = sT
        font.info.openTypeOS2StrikeoutPosition = sP


    def strikePosCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.strikePosition = value
            self.updateView()

    def underCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.underlineThickness = value
            self.updateView()

    def underPosCallback(self, sender):
        value = sender.get()
        if value != '-':
            self.underlinePosition = value
            self.updateView()

    def updateView(self):
        self.w.preview.contentView().refresh()

    def windowCloseCallback(self, sender):
        super(UnderlineStrikethroughPreview, self).windowCloseCallback(sender)
        removeObserver(self, "spaceCenterDraw")
        self.windowOpen = False

    def drawLines(self, notification):
        glyph = notification["glyph"]
        if glyph:
            if self.underlinePosition is not None and self.underlineThickness is not None:
                underlineY = self.underlinePosition - self.underlineThickness / 2
                rect(-10, underlineY, glyph.width+20, self.underlineThickness)
            if self.strikePosition is not None and self.strikeThickness is not None:
                strikeY = self.strikePosition - self.strikeThickness
                rect(-10, strikeY, glyph.width+20, self.strikeThickness)



OpenWindow(UnderlineStrikethroughPreview)
