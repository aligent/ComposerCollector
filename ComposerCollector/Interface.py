import xml.etree.cElementTree as ET
from xml.dom import minidom
__author__ = ''

class StatsToXML:

    @staticmethod
    def frequency_outptut(frequencies, use_lists):
        root = ET.Element("root")
        doc = ET.SubElement(root, "doc")

        for package_name, freq in frequencies.items():

            package_elem = ET.SubElement(doc, "package", name=package_name, frequency=str(freq))

            freq_elem = ET.SubElement(package_elem, 'frequency')
            use_elem = ET.SubElement(package_elem, 'used_by')

            if package_name in use_lists:
                for app_name in use_lists[package_name]:
                    ET.SubElement(use_elem, 'php_application', name=app_name)

    #    ET.ElementTree(root).write("composer_stats.xml")

        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")

        with open("composer_stats.xml", "w") as file:
            file.write(xmlstr)

