import ComposerCollector.Data as dm
import git
import os
import shutil
import xml.etree.ElementTree
import _thread
import json
__author__ = ''

# Facilitates the loading of repository information
class RepositoryManager:

    REPO_DIR = 'repos'
    COMPOSER_JSON_DIR = 'sadis_composer_json_files'

    def __init__(self):

        # Keeps track of repositories that are currently being downloaded
        self.repos_loading = 0

        # Thread locking manager
        self.lock = _thread.allocate_lock()

        # List of repository information that
        self.repositories = []

        # Make directory for storing repos if does not exist
        if not os.path.isdir(self.REPO_DIR):
            os.mkdir(self.REPO_DIR)

        # Make directory for storing composer json files - to be used in populating satis
        if not os.path.isdir(self.REPO_DIR):
            os.mkdir(self.COMPOSER_JSON_DIR)

    # Load XML file of repositories
    def load_file(self, file):
        # Parse XML file into python structure
        repo_xml = xml.etree.ElementTree.parse(file).getroot()

        # Check for existing repositories - if the repository already exists in the file system then
        # check that it is updated, else download the repositroy
        existing = os.listdir('repos')
        if 'temp' in existing:
            existing.remove('temp')
        print('existing', existing)

        # Create repository entry for each repo already in file system
        for repo_name in existing:
            in_repo = repo_xml.find("./repositories/repository[@name='%s']" % repo_name)

            if not in_repo:
                comp_path = in_repo.attrib['composer_path']
                self.load_existing_repository(repo_name, comp_path)
            else:
                print(repo_name + ' is not in XML repository file, repository not loaded')

        # Load Repository data for any new repositories, preformed on new threads for
        # simultaneous downloading
        for child in repo_xml.find("repositories"):
            try:
                # Flag that a repository is currently loading
                if child.attrib['name'] not in existing:
                    self.repos_loading += 1

                    # Name and URL required, will try without a branch
                    _thread.start_new_thread(self.load_new_repository, (child.attrib['name'],
                                                                        child.attrib['url'],
                                                                        child.attrib['branch'] or '',
                                                                        child.attrib['composer_path'] or '',))
            except _thread.error:
                print('Error loading ', child.attrib['name'])
                self.repos_loading -= 1

        # Wait for repositories to finish downloading
        while self.repos_loading > 0:
            pass

    def load_existing_repository(self, name, comp_path):
      #  subprocess.Popen(['git', 'config'], cwd='repos/%s/' % name, shell=True)
        repo = git.Repo(os.path.join('repos', name))
        repo.remote().fetch()
        try:
            repo.remote().pull()
        except:
            print("could not update", name)
        self.create_repository(name, os.path.join('repos', name), comp_path)

    def load_new_repository(self, name, url, branch, comp_path):

        # Repositories stored in temp while being created
        complete_path = os.path.join(self.REPO_DIR, name)
        temp_path = os.path.join(self.REPO_DIR, 'temp', name)

        # remove old version of repository
        if os.path.isdir(temp_path):
            shutil.rmtree(temp_path)
        os.makedirs(temp_path)

        # Load Repository from remote
        repo = git.Repo.init(temp_path)
        origin = repo.create_remote('origin', url)
        print('fetching', name)
        origin.fetch()
        print('fetched', name)

        if branch and branch != '':
            print(branch)
            origin.pull(branch)
        else:
            origin.pull(origin.refs[0].remote_head)

        print(origin.refs)

        # Downloaded to move to complete
        shutil.move(temp_path, complete_path)
        print(name, "loaded")

        self.lock.acquire()
        self.create_repository(name, complete_path, comp_path)
        self.repos_loading -= 1
        self.lock.release()

    # Creates a representation of the needed components of a python repository
    def create_repository(self, name, repo_path, composer_path=''):

        complete_path = os.path.join(repo_path, composer_path)

        composer_lock = self.load_json_file(complete_path, 'composer.lock')

        composer_json = self.load_json_file(complete_path, 'composer.json')

        master = dm.Branch(composer_json, composer_lock)

        new_repo = dm.Repository(name, repo_path, master)
        self.repositories.append(new_repo)

    # Loads a composer json file
    def load_json_file(self, repo_path, file_name):

        lock_file_path = os.path.join(repo_path, file_name)

        if not os.path.isfile(lock_file_path):
            return None

        with open(lock_file_path) as lock_file:
            data = json.load(lock_file)
        return data


class Stats:

    def __init__(self, repositories):
        self.repositories = repositories

        self.package_used_by = dict()
        self.package_use_frequency = dict()
        self.update_stats()

    def update_stats(self):
        for repo in self.repositories:
            if repo.master:
                if repo.master.composer_lock:
                    for module in repo.master.composer_lock['packages']:

                        if not module['name'] in self.package_used_by:
                            self.package_used_by[module['name']] = []

                        self.package_used_by[module['name']].append(repo.name)

                        if not module['name'] in self.package_use_frequency:
                            self.package_use_frequency[module['name']] = 1
                        else:
                            self.package_use_frequency[module['name']] += 1

