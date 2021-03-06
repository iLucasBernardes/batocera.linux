#!/usr/bin/env python
import xml.etree.ElementTree as ET
import batoceraFiles

esInputs = batoceraFiles.esInputs


class Input:
    def __init__(self, name, type, id, value, code):
        self.name = name
        self.type = type
        self.id = id
        self.value = value
        self.code = code


class Controller:
    def __init__(self, configName, type, guid, player, index="-1", realName="", inputs=None, dev=None, nbbuttons=None, nbhats=None, nbaxes=None):
        self.type = type
        self.configName = configName
        self.index = index
        self.realName = realName
        self.guid = guid
        self.player = player
        self.dev = dev
        self.nbbuttons = nbbuttons
        self.nbhats = nbhats
        self.nbaxes = nbaxes
        if inputs == None:
            self.inputs = dict()
        else:
            self.inputs = inputs

    def generateSDLGameDBLine(self):
        # Making a dirty assumption here : if a dpad is an axis, then it shouldn't have any analog joystick
        nameMapping = {
            'a'             : { 'button' : 'b' },
            'b'             : { 'button' : 'a' },
            'x'             : { 'button' : 'y' },
            'y'             : { 'button' : 'x' },
            'start'         : { 'button' : 'start' },
            'select'        : { 'button' : 'back' },
            'pageup'        : { 'button' : 'leftshoulder' },
            'pagedown'      : { 'button' : 'rightshoulder' },
            'l2'            : { 'button' : 'lefttrigger', 'axis' : 'lefttrigger' },
            'r2'            : { 'button' : 'righttrigger', 'axis' : 'righttrigger' },
            'l3'            : { 'button' : 'leftstick' },
            'r3'            : { 'button' : 'rightstick' },
            'up'            : { 'button' : 'dpup',    'hat' : 'dpup', 'axis' : 'lefty' },
            'down'          : { 'button' : 'dpdown',  'hat' : 'dpdown' },
            'left'          : { 'button' : 'dpleft',  'hat' : 'dpleft', 'axis' : 'leftx' },
            'right'         : { 'button' : 'dpright', 'hat' : 'dpright' },
            'joystick1up'   : { 'axis' : 'lefty' },
            'joystick1left' : { 'axis' : 'leftx' },
            'joystick2up'   : { 'axis' : 'righty' },
            'joystick2left' : { 'axis' : 'rightx' },
            'hotkey'        : { 'button' : 'guide' }
        }
        typePrefix = {
            'axis'   : 'a',
            'button' : 'b',
            'hat'    : 'h0.' # Force dpad 0 until ES handles others
        }

        if not self.inputs:
            return None
        # TODO: python3 - force to use unicode
        strOut = u"{},{},platform:Linux,".format(self.guid, self.configName)

        for idx, input in self.inputs.iteritems():
            if input.name in nameMapping and input.type in typePrefix and input.type in nameMapping[input.name] :
                if input.type == 'hat':
                    # TODO: python3 - force to use unicode
                    strOut += u"{}:{}{},".format(nameMapping[input.name][input.type], typePrefix[input.type], input.value)
                else:
                    # TODO: python3 - force to use unicode
                    strOut += u"{}:{}{},".format(nameMapping[input.name][input.type], typePrefix[input.type], input.id)
        return strOut


# Load all controllers from the es_input.cfg
def loadAllControllersConfig():
    controllers = dict()
    tree = ET.parse(esInputs)
    root = tree.getroot()
    for controller in root.findall(".//inputConfig"):
        controllerInstance = Controller(controller.get("deviceName"), controller.get("type"),
                                        controller.get("deviceGUID"), None, None)
        uidname = controller.get("deviceGUID") + controller.get("deviceName")
        controllers[uidname] = controllerInstance
        for input in controller.findall("input"):
            inputInstance = Input(input.get("name"), input.get("type"), input.get("id"), input.get("value"), input.get("code"))
            controllerInstance.inputs[input.get("name")] = inputInstance
    return controllers


# Load all controllers from the es_input.cfg
def loadAllControllersByNameConfig():
    controllers = dict()
    tree = ET.parse(esInputs)
    root = tree.getroot()
    for controller in root.findall(".//inputConfig"):
        controllerInstance = Controller(controller.get("deviceName"), controller.get("type"),
                                        controller.get("deviceGUID"), None, None)
        deviceName = controller.get("deviceName")
        controllers[deviceName] = controllerInstance
        for input in controller.findall("input"):
            inputInstance = Input(input.get("name"), input.get("type"), input.get("id"), input.get("value"), input.get("code"))
            controllerInstance.inputs[input.get("name")] = inputInstance
    return controllers


# Create a controller array with the player id as a key
def loadControllerConfig(controllersInput):
    playerControllers = dict()
    controllers = loadAllControllersConfig()

    for i, ci in enumerate(controllersInput):
        newController = findBestControllerConfig(controllers, str(i+1), ci["guid"], ci["index"], ci["name"], ci["devicepath"], ci["nbbuttons"], ci["nbhats"], ci["nbaxes"])
        if newController:
            playerControllers[str(i+1)] = newController
    return playerControllers

def findBestControllerConfig(controllers, x, pxguid, pxindex, pxname, pxdev, pxnbbuttons, pxnbhats, pxnbaxes):
    # when there will have more joysticks, use hash tables
    # TODO: python3 - workawround for names with utf-8 chars
    if (pxname != None):
        pxname = pxname.decode('utf-8')
    for controllerGUID in controllers:
        controller = controllers[controllerGUID]
        if controller.guid == pxguid and controller.configName == pxname:
            return Controller(controller.configName, controller.type, pxguid, x, pxindex, pxname,
                              controller.inputs, pxdev, pxnbbuttons, pxnbhats, pxnbaxes)
    for controllerGUID in controllers:
        controller = controllers[controllerGUID]
        if controller.guid == pxguid:
            return Controller(controller.configName, controller.type, pxguid, x, pxindex, pxname,
                              controller.inputs, pxdev, pxnbbuttons, pxnbhats, pxnbaxes)
    for controllerGUID in controllers:
        controller = controllers[controllerGUID]
        if controller.configName == pxname:
            return Controller(controller.configName, controller.type, pxguid, x, pxindex, pxname,
                              controller.inputs, pxdev, pxnbbuttons, pxnbhats, pxnbaxes)
    return None

def generateSDLGameDBAllControllers(controllers, outputFile = "/tmp/gamecontrollerdb.txt"):
    finalData = []
    for idx, controller in controllers.iteritems():
        finalData.append(controller.generateSDLGameDBLine())
    sdlData = "\n".join(finalData).encode("utf-8")
    with open(outputFile, "w") as text_file:
        text_file.write(sdlData)
    return outputFile
