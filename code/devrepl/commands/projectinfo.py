import glob
from . import ReplCommand
import sqlite3
import xml.etree.ElementTree
import re
from pathlib import Path
from .. import console_output as out
from .. import treewalk as tree


def find_pom_dir(path):
    par = path.parent
    if 'pom.xml' in [Path(child).name for child in par.iterdir()]:
        return par.as_posix()
    elif not par.parent is None:
        return find_pom_dir(par)


class ProjectInfo(ReplCommand):

    def startup(self):
        if not Path(self.dot_dir + 'devrepl.db').exists():
            print("Loading project info, please wait.")
            self.do_projectinfo_sync(None)

    def do_class_info(self, arg):
        conn = self.connect_devrepl_db()
        rows = conn.execute(
            "select import, pom from class_imports where import like '" + arg + "' group by import, pom")

        for row in rows:
            out.info(row[0] + ' - ' + row[1])
        conn.close

    def do_projectinfo_sync(self, arg):

        conn = self.connect_devrepl_db()
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS projects')
        c.execute('''CREATE TABLE IF NOT EXISTS projects
             (pom text, proj text, lastaccessed timestamp)''')

        def record_project(pomx):
            pom = pomx.path
            out.info("Loading info for %s" % pom)
            proj = self.proj_name_from_pom(pom)
            c.execute("INSERT INTO projects (pom, proj) VALUES (?, ?)", (pom, proj))
            conn.commit()

        tree.tree_actions(self.settings['proj_dir'], lambda entry: entry.path.endswith('pom.xml'),
                          record_project)
        conn.close()

    def proj_name_from_pom(self, pom):
        proj = "unknown"
        try:
            pomxml = xml.etree.ElementTree.parse(pom).getroot()
            find = pomxml.find("{http://maven.apache.org/POM/4.0.0}artifactId")
            if not find == None:
                proj = find.text
        except:
            # ignore
            print("failed to parse " + pom)
        return proj

    def do_classinfo_sync(self, arg):
        conn = self.connect_devrepl_db()
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS class_imports')
        c.execute('''CREATE TABLE IF NOT EXISTS class_imports
             (import text, classname text, pom text)''')
        classes = [file for file in
                   glob.iglob(self.settings['proj_dir'] + '/pentaho/pentaho-kettle.git/' + '**/*.java', recursive=True)]
        print('Found {} class files.'.format(len(classes)))
        for clazz in classes:
            pom = "unknown"
            classname = re.sub(r'.*/([^/.]*)[.]java', r'\1', clazz)
            try:
                file = open(clazz)
                package = None
                importz = []
                for line in file:
                    if not package and line.startswith('package '):
                        package = line[8:-2]
                        print('class={}, package={}'.format(clazz[:-4], package))
                    if line.startswith('import '):
                        importz.append(line[7:-2])
                file.close()
                pom = find_pom_dir(Path(clazz))
                for impor in importz:
                    c.execute("INSERT INTO class_imports (import, classname, pom) VALUES (?, ?, ?)",
                              (impor, package + '.' + classname, pom))
            except:
                # ignore
                print("failed to interpret " + clazz)

        conn.commit()
        conn.close()

    def switch_project_sql(self, arg):
        curproj = self.get_cur_project()
        if arg == '..':
            curpom = Path(curproj[1])
            parentpom = Path(curpom.parent.parent, 'pom.xml').as_posix()
            sql = "select proj, pom from projects where pom = '" + parentpom + "'"
        elif arg == '-':
            sql = "select proj, pom  from projects where proj <> '" + curproj[
                0] + "' order by lastaccessed desc limit 1"
        else:
            sql = "select proj, pom from projects where proj = '" + arg + "'"
        return sql

    def get_cur_project(self):
        if 'curproj' in self.session:
            curproj = self.session['curproj']
        else:
            curproj = None
        return curproj

    def do_switch_project(self, arg):
        """Sets the project to have in context."""
        sql = self.switch_project_sql(arg)
        conn = self.connect_devrepl_db()
        curs = conn.cursor()
        rows = conn.execute(sql)

        proj_matches = [row for row in rows]
        if not len(proj_matches) == 1:
            rows = conn.execute(
                "select proj, pom from projects where proj like '%" + arg + "%' order by lastaccessed desc")
            proj_matches = [row for row in rows]
        if len(proj_matches) == 0:
            print('Project {} not found'.format(arg))
            conn.close()
            return
        if len(proj_matches) == 1:
            verify = 'Y'
        else:
            verify = input('Selecting {}.  \nY/N/A (Yes/No/Alternatives) ?> '.format(proj_matches[0][1]))

        if verify.upper() == 'Y':
            curs.execute(
                "update projects set lastaccessed = CURRENT_TIMESTAMP where proj = ?", (proj_matches[0][0],))
            self.session['curproj'] = proj_matches[0]
        if verify.upper() == 'A':
            strip_len = len(self.settings['proj_dir'])
            out.table("Matching Projects",
                      rows=[(i, val[0], val[1][strip_len:]) for i, val in enumerate(proj_matches[:20])])
            inputnum = input('Selection:  ')
            proj_index = int(inputnum)
            self.session['curproj'] = proj_matches[proj_index]
            curs.execute(
                "update projects set lastaccessed = CURRENT_TIMESTAMP where proj = ?",
                (proj_matches[proj_index][0],))
        conn.commit()
        conn.close()

    def do_list_child_projects(self, arg):
        """Lists child maven projects below the currently selected project"""
        poms = [file for file in
                glob.iglob(Path(self.session['curproj'][1]).parent.as_posix() + '/' + '**/pom.xml', recursive=False)]
        out.table(self.session['curproj'][0], rows=[self.proj_name_from_pom(pom) for pom in poms])

    def complete_sp(self, text, line, begidx, endidx):
        conn = sqlite3.connect('devrepl.db')
        mline = line.partition(' ')[2]
        rows = conn.execute("select proj from projects where proj like '" + mline + "%' order by lastaccessed desc")

        proj_matches = [row[0] for row in rows]
        offs = len(mline) - len(text)
        return [s[offs:] for s in proj_matches]

    def prompt_str(self):
        if self.session.get('curproj'):
            return "[{}]".format(self.session['curproj'][0])
