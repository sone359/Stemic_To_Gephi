# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 20:44:38 2024

@author: Simon Biffe
"""

import json
import csv
import copy
import os

def stemic_to_data(file:str, destination:str=f'{os.getcwd()}/stemic_csv_files', color_themes:dict={}, group_label:str="included_in"):
    """
    Convert a Stemic json file in two csv files (edges and nodes) which
    can be easely imported in Gephi.
    The subgroups are converted in a node linked with each internal node.

    Parameters
    ----------
    file : str
        Path of the Stemic json file to convert.
    destination : str, optional
        Path of the directory where the csv files created will be 
        written. 
        The default is f'{os.getcwd()}/stemic_csv_files', 
        known that os.getcwd is the working directory.
    color_themes : dict, optional
        Allows to convert Stemic colors in thematics in the csv files.
        The default is {}.
    group_label : str, optional
        Allows to personnalise the label of the links between the 
        subgroups' nodes and their internal nodes. 
        The default is "included_in".

    Returns
    -------
    None.

    """
    
    #Importation du graphe Stemic sous la forme d'un json
    #Importation of the Stemic graph as a json
    with open(file, 'rb') as json_file:
        stemic_data = json.load(json_file)
    
    #Extraction des catégories de noeuds depuis le json Stemic
    #Extraction of nodes's categories from the Stemic json
    categories = {cat["id"]:cat["label"] for cat in stemic_data["categories"]}
    
    #Extraction et formatage des propriétés pour chaque catégorie de noeuds depuis le json Stemic
    #Extraction of the properties for each category of node from the Stemic json
    dict_properties = {}
    id_properties = {}
    for prop in stemic_data["properties"]:
        if prop["label"] in dict_properties.keys():
            dict_properties[prop["label"]].append(categories[prop["categoryId"]])
        else:
            dict_properties[prop["label"]] = [categories[prop["categoryId"]]]
        id_properties[prop["id"]] = prop["label"]
    properties = {prop[0]:f"{prop[0]} ({', '.join(prop[1])})" for prop in dict_properties.items()}
    for prop in id_properties.items():
        id_properties[prop[0]] = properties[prop[1]]
    node_header = ["id", "label", "category", "note", "highlight"] + list(properties.values())
    
    #Reformatage des informations concernant les noeuds contenues dans la partie 'entities' du json Stemic
    #Add of information about nodes stocked in the 'entities' place of the Stemic json
    nodes = [{"id":entity["id"], "label":entity["label"]["blocks"][0]["text"], "category":categories[entity["categoryId"]], "note":"\n".join((block["text"] for block in entity["note"]["blocks"]))}
             if "categoryId" in entity.keys() and "note" in entity.keys()
             else {"id":entity["id"], "label":entity["label"]["blocks"][0]["text"], "category":categories[entity["categoryId"]]}
             if "categoryId" in entity.keys()
             else {"id":entity["id"], "label":entity["label"]["blocks"][0]["text"], "note":"\n".join((block["text"] for block in entity["note"]["blocks"]))}
             if "note" in entity.keys()
             else {"id":entity["id"], "label":entity["label"]["blocks"][0]["text"]}
             for entity in stemic_data["entities"] if entity["id"] != 0]
    id_rank = {node["id"]:i for i, node in enumerate(nodes)}
    
    #Reformatage des informations concernant les noeuds contenues dans la partie 'attributes' du json Stemic
    #Add of information about nodes stocked in the 'attributes' place of the Stemic json
    for attribute in stemic_data["attributes"]:
        if "value" in attribute.keys():
            nodes[id_rank[attribute["entityId"]]][id_properties[attribute["propertyId"]]] = attribute["value"]
            
    #Traitement des liens à partir de la partie 'edges' du json Stemic
    #Add of edges information from the 'edges' place of the Stemic json
    nodes_to_entities = {node["id"]:node["entityId"] for node in stemic_data["nodes"]}
    edge_header = ["id", "source", "target", "type", "label", "weight", "note", "highlight", "hypothetic"]
    edges = []
    for edge in stemic_data["edges"]:
        edges.append({"id":edge["id"], "source":nodes_to_entities[edge["source"]], "target":nodes_to_entities[edge["target"]], "type":"directed", "weight":{"dashed":1, "medium":3, "large":4}[edge["thickness"]] if "thickness" in edge.keys() else 2, "hypothetic":1 if "thickness" in edge.keys() and edge["thickness"] == "dashed" else 0})
        if "label" in edge.keys():
            edges[-1]["label"] = edge["label"]
        if "note" in edge.keys():
            edges[-1]["note"] = "\n".join((block["text"] for block in edge["note"]["blocks"]))
        if "highlightColor" in edge.keys():
            if edge["highlightColor"] in color_themes.keys():
                edges[-1]["highlight"] = color_themes[edge["highlightColor"]]
            else:
                edges[-1]["highlight"] = edge["highlightColor"]
        if edge["isBidirectional"]:
            edges.append(copy.deepcopy(edges[-1]))
            edges[-1]["source"], edges[-1]["target"] = edges[-1]["target"], edges[-1]["source"]
            edges[-1]["id"] = max((edge2["id"] for edge2 in stemic_data["edges"]))*2 + edge["id"]
    
    #Extraction des informations contenues dans la partie 'nodes' du json Stemic
    #Les groupes Stemic sont convertis en liens labellisés par une valeur donnée ('included_in par défaut) allant des noeuds du groupe au noeud du groupe
    for node in stemic_data["nodes"]:
        if "highlightColor" in node.keys():
            if node["highlightColor"] in color_themes.keys():
                nodes[id_rank[node["entityId"]]]["highlight"] = color_themes[node["highlightColor"]]
            else:
                nodes[id_rank[node["entityId"]]]["highlight"] = node["highlightColor"]
        if node["id"] != 0 and node["groupId"] != 0:
            edges.append({"id":max((edge2["id"] for edge2 in stemic_data["edges"]))*3 + node["id"], "source":node["entityId"], "target":nodes_to_entities[node["groupId"]], "label":group_label, "type":"directed", "weight":2, "hypothetic":0})
            
    
    #Ecriture des fichiers csv contenant toutes les informations du graphe
    #Stemic et formaté de manière à pouvoir être importé facilement dans Gephi
    #Writing of the csv files with all information of the Stemic graph and 
    #structured to could be imported in Gephi easely
    with open(f"{destination}/{stemic_data['title']}_edges.csv", "w", newline='') as edges_file:
        writer = csv.DictWriter(edges_file, edge_header, restval=None)
        
        writer.writeheader()
        
        for edge in edges:
            writer.writerow(edge)
    
    with open(f"{destination}/{stemic_data['title']}_nodes.csv", "w", newline='') as nodes_file:
        writer = csv.DictWriter(nodes_file, node_header, restval=None)
        
        writer.writeheader()
        
        for node in nodes:
            writer.writerow(node)