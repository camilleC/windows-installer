import command
import packagemanager
class Command(command.BasePackageCommand):
    def __init__(self, args):
        command.BasePackageCommand.__init__(self,
            {'prog': "localVersion",
             'description': "Determines Version Information for local packages. Tots Implemented!"})

        self.ParseArgs(args)
		
		
    def ExecutePackage(self, package):
        version = package.findLocalVersion()
        if version!=None:
            self.logger.info(package.name()+ "\n\tLocal: " + version)
        else:
            self.logger.info(package.name()+ "\n\tNo Local Version Info")
