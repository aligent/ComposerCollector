import ComposerCollector.DataModel as dm
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

    def __init__(self):
        self.repos_loading = 0

        self.lock = _thread.allocate_lock()

        self.repositories = []
        if not os.path.isdir(self.REPO_DIR):
            os.mkdir(self.REPO_DIR)

    # Load XML file of repositories
    def load_file(self, file):

        # Parse XML file into python structure
        repX = xml.etree.ElementTree.parse(file).getroot()

        # Load Repository data for each repository
        # new thread is started for each repository, loading a repository consists of
        for child in repX:
            print(child.tag, child.attrib)

            try:
                # Flag that a repository is currently loading
                self.repos_loading += 1
                _thread.start_new_thread(self.load_repository, (child.attrib['name'], child.attrib['url'],))
            except _thread.error:
                print('Error loading ', child.attrib['name'])
                self.repos_loading -= 1

    def load_repository(self, name, url):

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
        origin.pull(origin.refs[0].remote_head)

        # Downloaded to move to complete
        shutil.move(temp_path, complete_path)
        print(name, "loaded")
        self.create_repository(name, complete_path)

        self.lock.acquire()
        self.repos_loading -= 1
        self.lock.release()

    def create_repository(self, name, repo_path):

        composer_lock = self.load_json_file(repo_path, 'composer.lock')

        composer_json = self.load_json_file(repo_path, 'composer.json')

        master = dm.Branch(composer_json, composer_lock)

        new_repo = dm.Repository(name, repo_path, master)
        self.repositories.append(new_repo)

    def load_json_file(self, repo_path, file_name):

        lock_file_path = os.path.join(repo_path, file_name)

        if not os.path.isfile(lock_file_path):
            return None

        with open(lock_file_path) as lock_file:
            data = json.load(lock_file)

        print(data)

        return data


class Stats:

    def __init__(self, repositories):
        self.repositories = repositories

        self.module_use = dict()
        self.update_module_use()

    def update_module_use(self):
        print(self.repositories)
        for repo in self.repositories:
            print('repo.master', repo.master)
            if repo.master:
                print('repo.master.composer_lock', repo.master.composer_lock['packages'])
                if repo.master.composer_lock:
                    for module in repo.master.composer_lock['packages']:
                        if not module['name'] in self.module_use:
                            print(module['name'], 'created')
                            self.module_use[module['name']] = 1
                        else:
                            self.module_use[module['name']] += 1
                            print(module['name'], '++')
        print(self.module_use)

test = RepositoryManager()
test.load_file('example.xml')


while test.repos_loading > 0:
    pass

stats = Stats(test.repositories)




