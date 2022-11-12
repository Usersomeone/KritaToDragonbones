import os
import json
import re

from PyQt5.QtWidgets import (QFileDialog, QMessageBox)

from krita import * 


class DragonbonesExport(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.directory = None
        self.msgBox = None
        self.fileFormat = 'png'
        self.bonePattern = re.compile("\(bone\)|\[bone\]", re.IGNORECASE)
        self.mergePattern = re.compile("\(merge\)|\[merge\]", re.IGNORECASE)
        self.slotPattern = re.compile("\(slot\)|\[slot\]", re.IGNORECASE)
        self.ignorePattern = re.compile("\(ignore\)|\[ignore\]", re.IGNORECASE)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("dragonbonesexportAction", "Export to Dragonbones", "tools/scripts")
        action.triggered.connect(self.exportDocument)

    def exportDocument(self):
        document = Krita.instance().activeDocument()

        if document is not None:
            if not self.directory:
                self.directory = os.path.dirname(document.fileName()) if document.fileName() else os.path.expanduser("~")
            self.directory = QFileDialog.getExistingDirectory(None, "Select a folder", self.directory, QFileDialog.ShowDirsOnly)

            if not self.directory:
                return
            
            picturePathName = document.fileName()
            pictureName = picturePathName.split(r'/')[-1]
            targetName = pictureName.split('.')[0]
            jsonName = targetName + r'.json'

            folderPath = self.directory + r'/DragonBones_' + targetName

            if not os.path.exists(folderPath):
              os.mkdir(folderPath)


            self.json = {
                "name": targetName,
                "version":"4.5",
                "armature":[{
                  "name":"armatureName",
                  "bone": [{"name": "root"}],
                  "slot": [],
                  "skin": [{"slot": []}],
                }]    
            }
            self.spineBones = self.json['armature'][0]['bone']
            self.spineSlots = self.json['armature'][0]['slot']
            self.spineDefaultSkin = self.json['armature'][0]['skin'][0]['slot']

            Krita.instance().setBatchmode(True)
            self.document = document
            self._export(document.rootNode(), folderPath)
            Krita.instance().setBatchmode(False)
            with open('{0}/{1}'.format(folderPath, jsonName), 'w') as outfile:
                json.dump(self.json, outfile, indent=2)
            self._alert("Export Successful")
        else:
            self._alert("Please select a Document")

    def _alert(self, message):
        self.msgBox = self.msgBox if self.msgBox else QMessageBox()
        self.msgBox.setText(message)
        self.msgBox.exec_()

    def _export(self, node, directory, bone="root", xOffset=0, yOffset=0, slot=None):
        newfolder = directory + r'/texture'
        if not os.path.exists(newfolder):
          os.mkdir(newfolder)

        for child in node.childNodes():
            if "selectionmask" in child.type():
                continue

            if not child.visible():
                continue

            if self.ignorePattern.search(child.name()):
                continue

            if child.childNodes():
                if not self.mergePattern.search(child.name()):
                    newBone = bone
                    newSlot = slot
                    newX = xOffset
                    newY = yOffset
                    if self.bonePattern.search(child.name()):
                        newBone = self.bonePattern.sub('', child.name()).strip()
                        rect = child.bounds()
                        newX = rect.left() + rect.width() / 2 - xOffset
                        newY = (- rect.bottom() + rect.height() / 2) - yOffset
                        self.spineBones.append({
                            'name': newBone,
                            'parent': bone,
                            'x': newX,
                            'y': newY
                        })
                        newX = xOffset + newX
                        newY = yOffset + newY
                    if self.slotPattern.search(child.name()):
                        newSlotName = self.slotPattern.sub('', child.name()).strip()
                        newSlot = {
                            'name': newSlotName,
                            'parent': bone,
                        }
                        self.spineSlots.append(newSlot)

                    self._export(child, directory, newBone, newX, newY, newSlot)
                    continue

            name = self.mergePattern.sub('', child.name()).strip()
            layerFileName = '{0}/{1}.{2}'.format(newfolder, name, self.fileFormat)
            child.save(layerFileName, 96, 96, InfoObject())

            newSlot = slot
            if not newSlot:
                newSlot = {
                    'name': name,
                    'parent': 'root',
                }
                self.spineSlots.append(newSlot)
            else:
                if not newSlot['attachment']:
                    newSlot['attachment'] = name

            rect = child.bounds()
            slotName = {
              'name':name,
              'display':[{
                'name':name,
                'transform':{
                'x': rect.left() + rect.width() / 2 - xOffset,
                'y': -((- rect.bottom() + rect.height() / 2) - yOffset),
                },
                'pivot':{
                  'x':0.5,
                  'y':0.5,
                }
              }],
            }
            self.spineDefaultSkin.append(slotName)
            


# And add the extension to Krita's list of extensions:
Krita.instance().addExtension(DragonbonesExport(Krita.instance()))

