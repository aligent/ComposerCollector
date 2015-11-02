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
    def load_file(self, json_config):
        # Parse XML file into python structure
        with open(json_config) as json_config_file:
            config = json.load(json_config_file)

        # Check for existing repositories - if the repository already exists in the file system then
        # check that it is updated, else download the repositroy
        existing = os.listdir('repos')
        if 'temp' in existing:
            existing.remove('temp')
        print('existing', existing)

        repo_name_list = []

        for name in config["repositories"].keys():
            repo_name_list.append(name)

        # Create repository entry for each repo that is in file system and config repo list
        for repo_name in [val for val in existing if val in repo_name_list]:

            existing_repo = config["repositories"][repo_name]

            self.load_existing_repository(existing_repo['name'], existing_repo['branches'])

        # Load Repository data for any new repositories, preformed on new threads for
        # simultaneous downloading
        for repo in config["repositories"].values():
            try:
                # Flag that a repository is currently loading
                if repo['name'] not in existing:
                    self.repos_loading += 1

                    #get brabch list

                    print(repo['branches'])
                    # Name and URL required, will try without a branch
                    _thread.start_new_thread(self.load_new_repository, (repo['name'],
                                                                        repo['url'],
                                                                        repo['branches']),)
            except _thread.error:
                print('Error loading ', repo['name'])
                self.repos_loading -= 1

        # Wait for repositories to finish downloading
        while self.repos_loading > 0:
            pass

    def load_existing_repository(self, name, branches):
        git_repo = git.Repo(os.path.join('repos', name))
        git_repo.remote().fetch()
        add_repo = dm.Repository(name, self.REPO_DIR)

        for branch in branches:
            try:
                print('Getting from branch', branch["name"])
                # git_repo.pull()
                self.quick_check_out(git_repo, branch)
                print('got')

                new_branch = dm.Branch(branch["name"],
                                       self.load_json_file(os.path.join(self.REPO_DIR, name), 'composer.lock'),
                                       self.load_json_file(os.path.join(self.REPO_DIR, name), 'composer.json'))

                add_repo.branches[new_branch.name] = new_branch
            except Exception:
                print("Could not update branch,", branch)

    def quick_check_out(self, repo, branch):
        repo.head.reference = repo.create_head(branch["name"])
        repo.head.reset(index=True, working_tree=True)

    def load_new_repository(self, name, url, branches):
        # Repositories stored in temp while being created
        complete_path = os.path.join(self.REPO_DIR, name)
        temp_path = os.path.join(self.REPO_DIR, 'temp', name)

        new_repo = dm.Repository(name, complete_path)

        # remove old version of repository
        if os.path.isdir(temp_path):
            shutil.rmtree(temp_path)
        os.makedirs(temp_path)

        # Load Repository from remote
        repo = git.Repo.init(temp_path)
        origin = repo.create_remote('origin', url)

        origin.fetch()

        for branch in branches:
            try:
                print('Getting from branch', branch["name"])
                origin.pull(branch["name"])
                print('got')

                new_branch = dm.Branch(branch["name"],
                                       self.load_json_file(temp_path, 'composer.lock'),
                                       self.load_json_file(temp_path, 'composer.json'))

                new_repo.branches[new_branch.name] = new_branch
            except:
                print("Could not load branch,", branch, "from repo,", name)

        # Downloaded to move to complete
        print(name, "loaded")

        self.lock.acquire()

        self.repos_loading -= 1
        self.repositories.append(new_repo)
        shutil.move(temp_path, complete_path)
        self.lock.release()

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

