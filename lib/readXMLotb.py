import xml.dom.minidom as minidom
import re


def readXMLotb(file):
    if isinstance(file, (minidom.Document, minidom.Element)):
        # Input is already a DOM object
        xDoc = file
    else:
        # Check if file exists
        try:
            # Try to read the XML file
            xDoc = minidom.parse(file)
        except FileNotFoundError:
            # Try adding .xml extension
            if ".xml" not in file:
                try:
                    xDoc = minidom.parse(file + ".xml")
                except FileNotFoundError:
                    raise FileNotFoundError(f"The file {file} could not be found")
            else:
                raise

    # Parse xDoc into a Python dictionary
    return parse_child_nodes(xDoc)


def parse_child_nodes(node):
    children = {}
    text = {}
    text_flag = "Text"

    if node.hasChildNodes():
        child_nodes = node.childNodes
        num_child_nodes = len(child_nodes)

        for count in range(num_child_nodes):
            child = child_nodes[count]
            child_text, name, attr, child_dict, child_text_flag = get_node_data(child)

            if name not in ["#text", "#comment", "#cdata-section"]:
                # XML allows same elements multiple times
                if name in children:
                    if not isinstance(children[name], list):
                        # Convert existing element to list
                        children[name] = [children[name]]

                    # Add new element
                    if child_dict:
                        children[name].append(child_dict)
                    elif child_text:
                        children[name].append(child_text)

                    # Add attributes
                    if attr and children[name][-1]:
                        children[name][-1]["Attributes"] = attr
                else:
                    # Add new element
                    if child_dict:
                        children[name] = child_dict
                    elif child_text:
                        children[name] = child_text
                    else:
                        children[name] = {}

                    # Add attributes
                    if attr and children[name]:
                        children[name]["Attributes"] = attr
            else:
                # This is text in an element
                ptext_flag = "Text"
                if name == "#cdata-section":
                    ptext_flag = "CDATA"
                elif name == "#comment":
                    ptext_flag = "Comment"

                if child_text.get(child_text_flag, "").strip():
                    if ptext_flag not in text or not text.get(ptext_flag, ""):
                        text[ptext_flag] = child_text[child_text_flag]
                    else:
                        # Append text
                        text[ptext_flag] += child_text[child_text_flag]

    return children, text, text_flag


def get_node_data(node):
    # Check node type and get node name
    if node.nodeType == minidom.Node.TEXT_NODE:
        name = "#text"
    elif node.nodeType == minidom.Node.COMMENT_NODE:
        name = "#comment"
    elif node.nodeType == minidom.Node.CDATA_SECTION_NODE:
        name = "#cdata-section"
    else:
        name = node.nodeName
        name = name.replace("-", "_dash_")
        name = name.replace(":", "_colon_")
        name = name.replace(".", "_dot_")

    # Parse attributes
    attr = parse_attributes(node)

    # Parse child nodes
    child_dict, text, text_flag = parse_child_nodes(node)

    # Get text content if no children
    if not child_dict and not text:
        if hasattr(node, "data"):
            text = {text_flag: node.data}
        elif hasattr(node, "textContent"):
            text = {text_flag: node.textContent}
        else:
            text = {text_flag: ""}

    return text, name, attr, child_dict, text_flag


def parse_attributes(node):
    attributes = {}

    # Check if node is an element and has attributes
    if node.nodeType == minidom.Node.ELEMENT_NODE and node.hasAttributes():
        attrs = node.attributes
        num_attrs = attrs.length

        for i in range(num_attrs):
            attr = attrs.item(i)
            attr_name = attr.name
            attr_name = attr_name.replace("-", "_dash_")
            attr_name = attr_name.replace(":", "_colon_")
            attr_name = attr_name.replace(".", "_dot_")
            attributes[attr_name] = attr.value

    return attributes
