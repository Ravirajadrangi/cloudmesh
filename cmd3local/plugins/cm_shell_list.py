import types
import textwrap
from docopt import docopt
import inspect
import sys
import importlib
from cmd3.shell import command
import cloudmesh
from pprint import pprint
from cloudmesh.util.logger import LOGGER


log = LOGGER(__file__)

class cm_shell_list:

    """opt_example class"""

    def activate_cm_shell_list(self):
        pass

    @command
    def do_list(self, args, arguments):
        """
        Usage:
               list flavors [CLOUD...] 
               list servers [CLOUD...]
               list images [CLOUD...]
               list [CLOUD...]
                              
        Arguments:
        
                CLOUD    the name of the cloud
                
        Options:

           -v       verbose mode

        """
        mesh = cloudmesh.mesh()
        #log.info(args)
        #pprint(arguments)
        #log.info(arguments)
        all = False
        if len(arguments["CLOUD"]) == 0:
            print "get all active clouds"
            all = True
            clouds = ['a', 'b']
        else:
            clouds = arguments['CLOUD']

        if arguments["flavors"] or all:
             for cloud in clouds:
                 mesh.refresh(names=[cloud], types=['flavor'])
                 flavors = mesh.clouds[cloud]['flavor']
                 pprint(flavors)

        if arguments["servers"] or all:
#            log.info ("count servers")
            for cloud in clouds:
                 mesh.refresh(names=[cloud], types=['server'])
                 servers = mesh.clouds[cloud]['server']
                 pprint(servers)

        if arguments["images"] or all:
            #log.info ("list images")
            for cloud in clouds:
                 mesh.refresh(names=[cloud], types=['image'])
                 images = mesh.clouds[cloud]['image']
                 pprint(images)



    @command
    def do_count(self, args, arguments):
        """
        Usage: 
               count flavors [CLOUD...]
               count servers [CLOUD...]
               count images [CLOUD...]
               count [CLOUD...]
               
        Arguments:
        
                CLOUD    the name of the cloud
        
        Options:

           -v       verbose mode

        """
        log.info(args)

        log.info(arguments)

        if len(arguments["CLOUD"]) == 0:
            print "get all active clouds"
            all = True
            clouds = ['a', 'b']
        else:
            clouds = arguments['CLOUD']

        print clouds

        if arguments["flavors"] or all:
            log.info ("count flavors")
            for cloud in clouds:
                print "cloud: flavors", cloud, None

        if arguments["servers"] or all:
            log.info ("count servers")
            for cloud in clouds:
                print "cloud: servers", cloud, None

        if arguments["images"] or all:
            log.info ("list images")
            for cloud in clouds:
                print "cloud: images", cloud, None
