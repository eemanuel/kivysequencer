import xml.etree.ElementTree as ET
from xml.dom import minidom

from aengine_thread import AudioItem


class FileSystem:
    @staticmethod
    def read_project_file(ai, filename, can):
        tree = ET.parse(filename)
        root = tree.getroot()
        for elem in root:
            for subelem in elem:
                # basic attributes to an audio item
                filename = subelem.attrib["filename"]
                volume = subelem.attrib["volume"]
                pan = subelem.attrib["pan"]
                velocity = subelem.attrib["velocity"]
                posX = subelem.attrib["posX"]
                posY = subelem.attrib["posY"]
                sizeW = subelem.attrib["sizeW"]
                sizeH = subelem.attrib["sizeH"]

                with can:
                    audioitem = AudioItem(
                        filename, volume, pan, velocity, [posX, posY], [sizeW, sizeH]
                    )
                    ai.append(audioitem)

                # check if we have a sub element aka a list of effects
                if len(subelem) > 1:
                    for item in subelem:
                        if item.tag == "effect":
                            for k, v in item.attrib.items():
                                print("  {} {}".format(k, v))
                            print("  ----------")
                print("-" * 20)

    @staticmethod
    def write_project_file(self, audioitems, filename):
        # create the file structure
        data = ET.Element("data")
        items = ET.SubElement(data, "items")

        for item in audioitems:
            item1 = ET.SubElement(items, "audioitem")
            item1.set("filename", str(item.filename))
            item1.set("volume", str(item.volume))
            item1.set("pan", str(item.pan))
            item1.set("effects", str(item.effects))
            item1.set("velocity", str(item.velocity))
            item1.set("posX", str(item.pos[0]))
            item1.set("posY", str(item.pos[1]))
            item1.set("sizeW", str(item.size[0]))
            item1.set("sizeH", str(item.size[1]))

        # create a new XML file with the results
        xmlstr = minidom.parseString(ET.tostring(data)).toprettyxml(
            indent="   ", encoding="UTF-8"
        )
        mydata = str(xmlstr.decode("UTF-8"))
        myfile = open(filename, "w")
        myfile.write(mydata)
