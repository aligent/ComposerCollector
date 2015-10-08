import ComposerCollector.DataModel as dm
import git
import os
import shutil
import xml.etree.ElementTree
import _thread
import time
__author__ = ''

# Facilitates the loading of repository information
class RepositoryManager:

    REPO_DIR = 'repos'

    def __init__(self):
        self.reposLoading = 0

        self.lock = _thread.allocate_lock()

        self.repositories = []
        if not os.path.isdir(self.REPO_DIR):
            os.mkdir(self.REPO_DIR)

    # Load XML file of repositories
    def load_file(self, file):

        # Parse XML file into python structure
        repX = xml.etree.ElementTree.parse(file).getroot()



        # Load Repository data for each repository
        for child in repX:
            print(child.tag, child.attrib)

            try:
                _thread.start_new_thread(self.load_repository, (child.attrib['name'], child.attrib['url'],))
            except _thread.error:
                print('Error loading ', child.attrib['name'])

            while self.reposLoading > 0:
                print(self.reposLoading)


        c = input("Type something to quit.")


    def load_repository(self, name, url):
        self.lock.acquire()

        #Flag that a repository is currently loading
        self.reposLoading += 1

        path = os.path.join(self.REPO_DIR, name)
        # remove old version of repository
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.mkdir(path)

        self.lock.release()

        repo = git.Repo.init(path)
        origin = repo.create_remote(name, url)
        print('fetching', name)
        origin.fetch()
        print('fetched', name)


        #repository has finished loading
        self.lock.acquire()
        origin.pull(origin.refs)
        self.reposLoading -= 1
        self.lock.release()


test = RepositoryManager()
test.load_file('example.xml')





