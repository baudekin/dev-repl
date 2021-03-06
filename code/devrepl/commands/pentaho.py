import glob
import os
import subprocess
import zipfile
from pathlib import Path
from shutil import rmtree, copyfile, move
from ..util import replace_in_file, httpget
from .. import console_output as out
from ..proc import cmd
from . import ReplCommand
from datetime import date
import sys


class Pentaho(ReplCommand):

    def startup(self):
        if 'active_pentaho' not in self.session:
            self.session['active_pentaho'] = 'qat'

    def do_spoon(self, arg):
        """Starts spoon, with debug port 5006.  enables karaf ssh automatically."""
        if 'suspend' in arg:
            suspend = 'y'
        else:
            suspend = 'n'
        opts = {}
        debug = 'debug' in arg

        out.highlighted('Enabling karaf ssh')
        replace_in_file(self.get_data_integration_dir() + '/system/karaf/etc/org.apache.karaf.features.cfg',
                        'featuresBoot=\\', 'featuresBoot=ssh,\\')

        self.exec_with_debug(self.get_spoon_path(debug=debug), self.get_spoon_log_path(), suspend=suspend,
                             extra_env=opts)

    def do_report_designer(self, arg):
            self.exec_with_debug(self.get_pentaho_reporting_dir() + '/report-designer.sh', self.get_reporting_log_path())

    def do_pentaho_server(self, arg):
        pen_server = self.get_pentaho_server_dir()

        out.highlighted('Enabling karaf ssh')
        replace_in_file(pen_server + '/pentaho-solutions/system/karaf/etc/org.apache.karaf.features.cfg',
                        'featuresBoot=\\', 'featuresBoot=ssh,\\')

        self.exec_with_debug(pen_server + '/start-pentaho-debug.sh',
                             self.get_server_log_path(), debug_port=8044)

    def do_carte(self, arg):
        http_port = '8081'
        env = {'KETTLE_CARTE_OBJECT_TIMEOUT_MINUTES': '1'}
        self.exec_with_debug([self.dot_dir + 'qat/design-tools/data-integration/carte.sh', '127.0.0.1', http_port],
                             self.get_carte_log_path(), extra_env=env, debug_port=5007)

    def exec_with_debug(self, exec_path, log_path, debug_port=5006, extra_env={}, suspend='n'):
        out.highlighted("Starting: " + str(exec_path), "Debug port " + str(debug_port))
        env = os.environ
        env.update(
            {'OPT': '-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=' + suspend + ',address=' + str(
                debug_port)})
        env.update(extra_env)
        log = open(log_path, 'a')
        wd = exec_path if type(exec_path) is str else exec_path[0]
        out.info(env)
        subprocess \
            .Popen(exec_path + ' >> ' + log_path,
                   cwd=Path(wd).parent,
                   shell=True,
                   # stdout=log,
                   # stderr=log,
                   # stdin=sys.stdin,
                   env=env,
                   start_new_session=True)  # start_new_session prevents ctl-c from being passed to this proc

    def do_log(self, arg):
        """tail the running spoon log.  Specify server/carte/reporting to tail their specific logs"""
        if arg == 'server':
            logpath = self.get_server_log_path()
        elif arg == 'carte':
            logpath = self.get_carte_log_path()
        elif arg == 'reporting':
            logpath = self.get_reporting_log_path()
        else:
            logpath = self.get_spoon_log_path()
        cmd(['tail', '-f', '-n', '500', logpath], shell=True, stdout=None)

    def complete_log(self, text, line, begidx, endidx):
        return [i.lstrip('-') for i in ['spoon', 'server', 'carte'] if i.startswith(text) or i.startswith('-' + text)]

    def get_spoon_log_path(self):
        return self.dot_dir + self.session['active_pentaho'] + '/spoon.log'

    def get_reporting_log_path(self):
        return self.dot_dir + self.session['active_pentaho'] + '/prd.log'

    def get_carte_log_path(self):
        return self.dot_dir + self.session['active_pentaho'] + '/carte.log'

    def get_server_log_path(self):
        return self.dot_dir + 'qat/server/pentaho-server/tomcat/logs/catalina.out'

    def get_spoon_path(self, debug=False):
        if debug:
            spoon_cmd = '/SpoonDebug.sh'
        else:
            spoon_cmd = '/spoon.sh'
        return self.get_data_integration_dir() + spoon_cmd

    def get_data_integration_dir(self):
        if 'active_pentaho' in self.session and self.session['active_pentaho'] == 'ss':
            return self.dot_dir + "/ss/data-integration"
        else:
            return self.dot_dir + "/qat/design-tools/data-integration"

    def get_pentaho_reporting_dir(self):
        if 'active_pentaho' in self.session and self.session['active_pentaho'] == 'ss':
            print("snapshot doesn't load reporting")
            return None
        else:
            return self.dot_dir + "/qat/design-tools/report-designer"

    def get_pentaho_server_dir(self):
        if 'active_pentaho' in self.session and self.session['active_pentaho'] == 'ss':
            return self.dot_dir + "/ss/pentaho-server"
        else:
            return self.dot_dir + "/qat/server/pentaho-server"

    def do_install_plugin(self, arg):
        """Installs legacy pentaho plugins.  use the arg 'pdi-legacy' to install PDI plugins, 'puc-legacy' for PUC"""
        dot_dir = self.dot_dir
        # find built artifacts
        if arg == 'pdi-legacy':
            self.install_plugin(self.get_data_integration_dir() + "/plugins")
            self.install_plugin(dot_dir + self.get_pentaho_server_dir() + "/system/kettle/plugins")
        elif arg == 'puc-legacy':
            self.install_plugin(dot_dir + "/qat/server/pentaho-server/pentaho-solutions/system")
        else:
            out.error('Specify "pdi-legacy" or "puc-legacy"')

    def install_plugin(self, plugin_path):
        proj_path = self.get_proj_path()
        zips = [file for file in
                glob.iglob(proj_path + '/**/target/*.zip', recursive=True)
                if 'plugin' in str(file)]
        if len(zips) == 0:
            out.error("No plugin zip found under " + proj_path)
            return
        out.info(". . . . . . \nInstalling plugin \n" + zips[0] + "\n   to  \n" + plugin_path + "\n. . . . . . . .")

        zipref = zipfile.ZipFile(zips[0])
        temp_dir = plugin_path + "/.temp/"
        rmtree(temp_dir, ignore_errors=True)
        zipref.extractall(temp_dir)
        zipref.close()

        subdirs = list(glob.iglob(temp_dir + "*"))
        if len(subdirs) == 1:
            plugin_name = Path(subdirs[0]).name
            out.info("Plugin dir name:  " + plugin_name)
            cur_plugin = plugin_path + "/" + plugin_name
            out.warn("Removing dir " + cur_plugin)
            rmtree(plugin_path + "/" + plugin_name, ignore_errors=True)
            out.info("Installing plugin " + plugin_name)
            move(temp_dir + "/" + plugin_name, plugin_path + "/" + plugin_name)
            out.info("Done.")

    def do_install_lib(self, arg):
        """Copies built jars to the PDI and PUC /lib dirs.  Not for osgi plugins."""
        self.move_artifact_to(self.get_data_integration_dir() + "/lib/")
        self.move_artifact_to(self.get_pentaho_server_dir() + "/tomcat/webapps/pentaho/WEB-INF/lib/")

    def do_install_drivers(self, arg):
        """Retrieves jdbc drivers specified in settings.json and installs in PDI, PUC and PRD."""
        self.load_drivers_to(self.get_data_integration_dir() + "/lib/")
        self.load_drivers_to(self.get_pentaho_server_dir() + "/tomcat/webapps/pentaho/WEB-INF/lib/")
        self.load_drivers_to(self.get_pentaho_reporting_dir() + "/lib/")


    def do_install_bundle(self, arg):
        """copies built jar(s) to the deploy directory of data-integration and pentaho-server"""
        if self.get_active_pen()[0] != 'ss':
            response = input("QAT is currently active, are you sure you want to install a bundle? (y/n)")
            if response.lower() != 'y':
                return
        self.move_artifact_to(self.get_data_integration_dir() + "/system/karaf/deploy/")
        self.move_artifact_to(self.get_pentaho_server_dir() + "/pentaho-solutions/system/karaf/deploy/")

    def do_install_kar(self, arg):
        """copies built kar(s) to the deploy directory of data-integration and pentaho-server"""
        self.move_artifact_to(self.get_data_integration_dir() + "/system/karaf/deploy/", artifact_extension='kar')
        self.move_artifact_to(self.get_pentaho_server_dir() + "/pentaho-solutions/system/karaf/deploy/",
                              artifact_extension='kar')

    def prompt_str(self):
        di_path = Path(self.get_data_integration_dir())
        if di_path.exists():
            jar = glob.glob((di_path / "lib").as_posix() + "/kettle-core-*")
            activepen = self.get_active_pen()
            if activepen[0] == 'ss':  # and activepen[1]:
                version_num = activepen[0] + ' ' + str(
                    date.fromtimestamp(Path(self.dot_dir, "ss/data-integration").lstat().st_mtime))
            else:
                version_num = 'QAT ' + Path(jar[0]).name[12:-4]
                self.session['pentaho_version'] = version_num
            return "[" + version_num + "]"

    def get_active_pen(self):
        val = [None, None]
        if 'active_pentaho' in self.session:
            val[0] = self.session['active_pentaho']
        if 'snapshot_date' in self.session:
            val[1] = self.session['snapshot_date']
        return val

    def do_set_project_version(self, arg):
        if len(arg) > 0:
            version = arg
        else:
            version = self.session['pentaho_version']
        set_version_cmd = ["mvn", "-f", self.session['curproj'][1], "versions:set", "-DnewVersion={}".format(version)]
        cmd(set_version_cmd, stdout=None)

    def do_list_artifacts(self, arg):
        """list built artifacts in current project."""
        out.highlighted(*self.get_artifacts(self.get_proj_path()))

    def do_lineage_on(self, arg):
        """Turn on lineage configuration."""
        replace_in_file(self.get_data_integration_dir() + '/system/karaf/etc/pentaho.metaverse.cfg', '=off', '=on')

    def move_artifact_to(self, to, artifact_extension='jar'):
        if not Path(to).exists():
            out.warn("Destination path " + to + " does not exist.")
            return
        jars = self.get_artifacts(self.get_proj_path(), artifact_extension=artifact_extension)
        if len(jars) == 0:
            out.error("No jars found under " + self.get_proj_path())
            return
        if len(jars) > 1:
            out.table('Artifacts found', rows=jars)
            print()
            answer = input('Copy jars to ' + to + '? Y/N: ')
            if answer.upper() != 'Y':
                return

        for jar in jars:
            jar_name = Path(jar).name
            name_prefix = jar_name[0:jar_name.rfind("-")]
            out.info('Searching for matches "' + name_prefix + '"\n')
            out.info('-' * 40)
            for f in os.listdir(to):
                if name_prefix in f:
                    out.warn("\n > > Deleting " + f)
                    os.remove(to + "/" + f)

            out.highlighted("Copying", jar, "   to   ", to)
            copyfile(jar, to + jar_name)

    def get_proj_path(self):
        return Path(self.session['curproj'][1]).parent.as_posix()

    def get_artifacts(self, proj_path, artifact_extension='jar'):
        return [file for file in
                glob.iglob(proj_path + '/**/target/*.' + artifact_extension, recursive=True)
                if "-sources" not in str(file) and "-test" not in str(file)]

    def do_install_snapshot(self, arg):
        """Installs the zips listed in the 'snapshot_zips' section of settings.json
        Assumes `get_snapshot` has been run to retrieve those zips first."""
        if Path(self.dot_dir, "ss").exists():
            rmtree(self.dot_dir + "ss", ignore_errors=True)
        Path(self.dot_dir, "ss").mkdir()
        for item in self.settings['snapshot_zips']:
            zip = self.dot_dir + item.rsplit('/', 1).pop()
            cmd(["unzip", "-o", "-d", Path(self.dot_dir, "ss").as_posix(), zip])

    def do_qat(self, arg):
        """Make QAT the active installation."""
        self.session['active_pentaho'] = 'qat'

    def do_snapshot(self, arg):
        """Make snapshot the active installation."""
        self.session['active_pentaho'] = 'ss'

    def do_get_snapshot(self, arg):
        """Retrieve snapshot artifacts, storing in the .devrepl directory."""
        dest = self.dot_dir

        for item in self.settings['snapshot_zips']:
            mod_date = httpget(item, dest + item.rsplit('/', 1).pop())

        self.session['snapshot_date'] = mod_date

    def load_drivers_to(self, dest):
        if not Path(dest).exists():
            out.warn(dest + " does not exist")
            return
        for driver in self.settings['jdbc_drivers']:
            httpget(driver, dest + driver.rsplit('/', 1).pop())


def stop_pentaho_server(server_dir):
    if Path(server_dir).exists():
        try:
            out.highlighted('Stopping Pentaho server')
            cmd('stop.command', server_dir)
        except:
            pass
