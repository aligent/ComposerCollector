import xml.etree.cElementTree as ET
from xml.dom import minidom
import requests
import ComposerCollector.Program as program
import json
import socket
import socketserver

__author__ = ''

class StatsToXML:
    ET.Element.set
    @staticmethod
    def frequency_outptut(frequencies, use_lists):
        root = ET.Element("root")
        doc = ET.SubElement(root, "doc")

        for package_name, freq in frequencies.items():

            package_elem = ET.SubElement(doc, "package", name=package_name, use_count=str(freq))
            use_elem = ET.SubElement(package_elem, 'used_by')

            if package_name in use_lists:
                for app_name in use_lists[package_name]:
                    ET.SubElement(use_elem, 'php_application', name=app_name)

    #    ET.ElementTree(root).write("composer_stats.xml")

        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")

        with open("composer_stats.xml", "w") as file:
            file.write(xmlstr)


class SatisCommunicator:

    def __init__(self, satis_url, repository_manager):
        self.satis_url = satis_url
        self.repository_manager = repository_manager

    def update_satis(self):
        headers = {'content-type': 'application/json'}

        # add_items = self.get_unique_adds()

        add_items = {'new_items':self.generate_upload()}
        print(add_items)

        req = requests.post("http://localhost:4680/repo_manager.php",
                             headers=headers, json=add_items)
        print(req.text)

    def generate_upload(self):
        repos = self.repository_manager.repositories

        new_items = list()

        for repo in repos:
            require = {}
            comp_repos = []
            if 'require' in repo.master.composer_json:
                require = repo.master.composer_json['require']
            if ('extra' in repo.master.composer_json) \
                    & ('satis-repositories' in repo.master.composer_json['extra']):
                comp_repos = repo.master.composer_json['extra']['satis-repositories']

            new_items.append({'repos': comp_repos, 'requires': require})

        return new_items

SATIS_URL = 'http://localhost:4680/repo_manager.php'

# Progarm run code test
rm = program.RepositoryManager()
rm.load_file('config.json')

#stats = program.Stats(rm.repositories)

#satis = SatisCommunicator(SATIS_URL, rm)
#satis.update_satis()

#StatsToXML.frequency_outptut(stats.package_use_frequency, stats.package_used_by)


