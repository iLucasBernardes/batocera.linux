#!/usr/bin/env python
import Command
#~ import reicastControllers
import recalboxFiles
from generators.Generator import Generator
import reicastControllers
import shutil
import os.path
import ConfigParser
from shutil import copyfile
from os.path import dirname
from os.path import isdir
from os.path import isfile

class ReicastGenerator(Generator):

    # Main entry of the module
    # Configure fba and return a command
    def generate(self, system, rom, playersControllers, gameResolution):
        # Write emu.cfg to map joysticks, init with the default emu.cfg
        Config = ConfigParser.ConfigParser()
        Config.optionxform = str
        if os.path.exists(recalboxFiles.reicastConfig):
            Config.read(recalboxFiles.reicastConfig)
        
        if not Config.has_section("input"):
            Config.add_section("input")
        # For each pad detected
        for index in playersControllers:
            controller = playersControllers[index]
        
            # Get the event number
            eventNum = controller.dev.replace('/dev/input/event', '')
            
            # Write its mapping file
            controllerConfigFile = reicastControllers.generateControllerConfig(controller)
            
            # set the evdev_device_id_X
            Config.set("input", 'evdev_device_id_' + controller.player, eventNum)
            
            # Set the evdev_mapping_X
            Config.set("input", 'evdev_mapping_' + controller.player, controllerConfigFile)
        
        if not Config.has_section("players"):
            Config.add_section("players")
        # number of players
        Config.set("players", 'nb', len(playersControllers))

        if not Config.has_section("config"):
            Config.add_section("config")
        # wide screen mode
        if system.config["ratio"] == "16/9":
            Config.set("config", "rend.WideScreen", "1")
        # seems buggy + works only in 60hz on my side, so don't apply it automatically
        #elif system.config["ratio"] == "auto" and gameResolution["width"] / float(gameResolution["height"]) >= (16.0 / 9.0) - 0.1: # let a marge
        #    Config.set("config", "WideScreen", "1")
        else:
            Config.set("config", "rend.WideScreen", "0")

        ### update the configuration file
        if not os.path.exists(os.path.dirname(recalboxFiles.reicastConfig)):
            os.makedirs(os.path.dirname(recalboxFiles.reicastConfig))
        with open(recalboxFiles.reicastConfig, 'w+') as cfgfile:
            Config.write(cfgfile)        
            cfgfile.close()
            
        # internal config
        # vmuA1
        if not isfile(recalboxFiles.reicastVMUA1):
            if not isdir(dirname(recalboxFiles.reicastVMUA1)):
                os.mkdir(dirname(recalboxFiles.reicastVMUA1))
            copyfile(recalboxFiles.reicastVMUBlank, recalboxFiles.reicastVMUA1)
        # vmuA2
        if not isfile(recalboxFiles.reicastVMUA2):
            if not isdir(dirname(recalboxFiles.reicastVMUA2)):
                os.mkdir(dirname(recalboxFiles.reicastVMUA2))
            copyfile(recalboxFiles.reicastVMUBlank, recalboxFiles.reicastVMUA2)

        # the command to run  
        commandArray = [recalboxFiles.recalboxBins[system.config['emulator']]]
        commandArray.append(rom)
        # Here is the trick to make reicast find files :
        # emu.cfg is in $XDG_CONFIG_DIRS or $XDG_CONFIG_HOME. The latter is better
        # VMU will be in $XDG_DATA_HOME because it needs rw access -> /userdata/saves/dreamcast
        # BIOS will be in $XDG_DATA_DIRS
        # controller cfg files are set with an absolute path, so no worry
        return Command.Command(array=commandArray, env={"XDG_CONFIG_HOME":recalboxFiles.CONF, "XDG_DATA_HOME":recalboxFiles.reicastSaves, "XDG_DATA_DIRS":recalboxFiles.reicastBios})