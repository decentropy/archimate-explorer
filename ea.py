
import pandas as pd
import os
import networkx as nx
import xml.etree.ElementTree as ET
import re
from networkx.readwrite import json_graph
import json

#========= YOUR CONFIG HERE =============
MODELNAME = "Archisurance"
MODELID = "11f5304f" #find in your xml
#========================================


#Paths to use (xml, html)
path_root = os.path.dirname(os.path.abspath(__file__))
path_data = os.path.join(path_root, "static", "_data")
datafile = lambda x: os.path.join(path_data, x)

# usage, e.g.:  dfe[dfe.Type.isin(ea.layers["application"])]
layers = {
    "application": ["ApplicationCollaboration", "ApplicationComponent", "ApplicationEvent", "ApplicationFunction", "ApplicationInteraction", "ApplicationInterface", "ApplicationProcess", "ApplicationService", "DataObject"],
    "business": ["Contract", "BusinessActor", "BusinessCollaboration", "BusinessEvent", "BusinessFunction", "BusinessInteraction", "BusinessInterface", "BusinessObject", "BusinessProcess", "BusinessRole", "BusinessService", "Representation", "Product"],
    "strategy": ["Capability", "Resource", "CourseOfAction", "ValueStream"],
    "technology": ["Artifact", "CommunicationNetwork", "Device", "Node", "Path", "SystemSoftware", "TechnologyCollaboration", "TechnologyEvent", "TechnologyFunction", "TechnologyInteraction", "TechnologyInterface", "TechnologyProcess", "TechnologyService"],
    "motivation": ["Assessment", "Constraint", "Driver", "Goal", "Outcome", "Meaning", "Principle", "Requirement", "Stakeholder", "Value"],
    "physical": ["DistributionNetwork", "Equipment", "Material", "Facility"],
    "implementation": ["Deliverable", "Gap", "ImplementationEvent", "WorkPackage", "Plateau"],
    "other": ["Grouping", "Junction", "Location"]
    }


#load dataframe from csv
def getcsv(name):
    return pd.read_csv(datafile(name + '.csv'))


#load dataframe from pickle
def getdf(name):
    return pd.read_pickle(datafile(name + '.pickle'))

#function: return dataframe, merging names from "elements" table by idcol. (use suffix for duplicate columns)
def addnames(dfleft, idcol, suffix):
    dfe = getcsv('elements')
    dfn = dfe.query('ID in (%s)' % dfleft[idcol].tolist())[['ID','Name']]
    return pd.merge(dfleft, dfn, how='left', left_on=[idcol], right_on=['ID'], suffixes=('','_'+suffix)).drop(idcol,1)


class dataobj:
    def __init__(self):
        self.dfe = None # ID,Type,Name
        self.dfr = None # Type,Source,Target
        self.dfprops = None # ID,Type,Name,Prop1,Prop2,etc.
        self.G = None # ID,Type,Name,Prop1,Prop2,etc.
        self.refresh()

    def refresh(self):
        self.refresh_data()
        self.refresh_proplist()
        self.refresh_graphnodes()
        self.refresh_graphviews()

    def refresh_data(self):
        self.dfe = pd.read_csv(datafile("elements.csv"))[['ID','Type','Name']]
        self.dfr = pd.read_csv(datafile("relations.csv"))[['Type','Source','Target']]

    def refresh_proplist(self):
        dfp = getcsv("properties")
        df = pd.merge(self.dfe, dfp, how='left').fillna(value='-')
        df = df.set_index(['ID', 'Type', 'Name','Key'])['Value'].unstack('Key').reset_index()
        df.drop(['-'], axis=1, inplace=True)
        df.fillna('', inplace=True)
        df = df.sort_values(['Type','Name'], ascending=[True,True]).reset_index(drop=True)
        df.to_csv(datafile("ea-searchlist.csv"), index = False)
        self.dfprops = df

    def refresh_graphnodes(self):
        #basic graph
        G = nx.from_pandas_edgelist(self.dfr, source='Source', target='Target', create_using=nx.DiGraph())
        #node attributes
        dfetmp = self.dfprops.copy()
        dfetmp = dfetmp.set_index('ID')
        dfetmp['id'] = dfetmp.index
        nx.set_node_attributes(G, values=pd.Series(dfetmp.id).to_dict(), name='id') #vizjs
        nx.set_node_attributes(G, values=pd.Series(dfetmp.Name).to_dict(), name='label') #vizjs
        nx.set_node_attributes(G, values=pd.Series(dfetmp.Type).to_dict(), name='type')
        #add for vizjs
        dfetmp['Shape'] = "image"
        dfetmp['Imgpath'] = "/static/_icons/" + dfetmp.Type.str.lower() + ".png"
        nx.set_node_attributes(G, values=pd.Series(dfetmp.Shape).to_dict(), name='shape')
        nx.set_node_attributes(G, values=pd.Series(dfetmp.Imgpath).to_dict(), name='image')
        self.G = G
        #Serialize pickle
        nx.write_gpickle(self.G, datafile("parsed/ea-nxgraph.pickle"))

    def refresh_graphviews(self):
        with open(datafile(MODELNAME+".xml"), 'r', encoding="utf8") as myfile:
            xmlstr = myfile.read()
        xmlstr = re.sub(' xmlns="[^"]+"', '', xmlstr, count=1)
        xmlstr = re.sub(' xsi\:', ' ', xmlstr)
        root = ET.fromstring(xmlstr)
        #Parse views
        nodeids = {}
        nodelabels = {}
        nodetypes = {}
        edges = []
        #for diagrams in xml
        for el in root.findall("./views/diagrams/"):
            vid = el.attrib["identifier"] #view id
            nodelabels[vid] = el.find("name").text #view name
            nodetypes[vid] = "view" #view name
            nodeids[vid] = vid #view name
            for el1 in el.findall(".//node"):
                if el1.attrib.get("elementRef"): #elements in view
                    nid = el1.attrib["elementRef"]
                    edges.append((nid.replace("id-",""), vid))
        #add to graph
        self.G.add_edges_from(edges)
        nx.set_node_attributes(self.G, values=nodeids, name='id')
        nx.set_node_attributes(self.G, values=nodelabels, name='label')
        nx.set_node_attributes(self.G, values=nodetypes, name='type')
        #Serialize JSON
        with open(datafile("parsed/nxv.json"), 'w') as handle:
            json.dump(json_graph.node_link_data(self.G), handle)
