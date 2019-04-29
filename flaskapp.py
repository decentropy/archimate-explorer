""" This is the web app server. """

from flask import Flask, request, redirect, render_template
import pandas as pd
from datetime import datetime
import networkx as nx
import random
import string
import os
import xml.etree.ElementTree as ET
import re
import pickle


#========= YOUR CONFIG HERE =============
MODELNAME = "Archisurance"
MODELID = "11f5304f" #find in your xml
#========================================

app = Flask(__name__)
app.debug = True

#Paths to use (xml, html)
approot = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(approot, "static", "data")


#home
@app.route('/')
def index(): 
    return render_template('welcome.html')

#refresh data
@app.route('/refresh', methods=['GET'])
def refreshea():
    #get xml
    with open(os.path.join(datadir, MODELNAME+".xml"), 'r') as myfile:
        xmlstr = myfile.read()
    xmlstr = re.sub(' xmlns="[^"]+"', '', xmlstr, count=1)
    xmlstr = re.sub(' xsi\:', ' ', xmlstr)
    root = ET.fromstring(xmlstr)

    #parse relationships network ==================
    #add edges
    edgelist = []
    for el in root.findall("./relationships/"):
        edgelist.append(el.attrib["source"][3:] + ' ' + el.attrib["target"][3:])    
    G = nx.parse_edgelist(edgelist, create_using=nx.DiGraph()) 
    #add nodes
    elemlist = []
    for el in root.findall("./elements/"):
        elemlist.append((el.attrib["identifier"][3:], el.attrib["type"], el.find("name").text))
    df = pd.DataFrame.from_records(elemlist, columns=['ID','Type','Name'])
    df.to_pickle(os.path.join(datadir, "ea-elements.pickle"))
    #format for visjs
    df['Shape'] = "image"
    df['Imgpath'] = "/static/icons/" + df.Type.str.lower() + ".png"
    df = df.set_index('ID')
    df['id'] = df.index
    G.add_nodes_from(df.index.tolist())
    #node attributes
    nx.set_node_attributes(G, values=pd.Series(df.Name).to_dict(), name='label')
    nx.set_node_attributes(G, values=pd.Series(df.Shape).to_dict(), name='shape') 
    nx.set_node_attributes(G, values=pd.Series(df.Imgpath).to_dict(), name='image')
    nx.set_node_attributes(G, values=pd.Series(df.id).to_dict(), name='id')    
    #serialize
    nx.write_gpickle(G, os.path.join(datadir, "ea-nxgraph.pickle"))

    #parse views usage ==================
    viewnames = {}
    nodeviews = {}
    for el in root.findall("./views/diagrams/"):
        vid = el.attrib["identifier"]
        viewnames[vid] = el.find("name").text #add to viewnames
        for el1 in el.findall(".//node"):
            if el1.attrib.get("elementRef"):
                nid = el1.attrib["elementRef"]
                if not nodeviews.get(nid):
                    nodeviews[nid] = []
                nodeviews[nid].append(vid) #add to nodeviews
    diagrams = {'viewnames': viewnames, 'nodeviews': nodeviews}
    #serialize
    with open(os.path.join(datadir, "ea-diagrams.pickle"), 'wb') as handle:
        pickle.dump(diagrams, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #return
    return redirect("/")


#============= EA SEARCH ====================

#show links to matches found in elements.csv
@app.route('/search/<path:term>', methods=['GET'])
def easearch(term):
    df = pd.read_pickle(os.path.join(datadir, "ea-elements.pickle"))[['ID','Type','Name']]
    df = df[(df.Name.str.contains(term, case=False, regex=False))|(df.Type.str.contains(term, case=False, regex=False))]
    results = "No matches found."
    if not df.empty:
        df['Results'] = df.apply(lambda x: "<li><a href='/node/" + x.ID + "'>" + x.Type + ": " + x.Name + "</a>", axis=1)
        results = ''.join(df['Results'].tolist())
    return render_template('ea-search.html', label=term, results=results)


#============= EA VISUALIZER ====================

#format edge
def fedge(x):
    edge = {}
    edge['to'] = x[0]
    edge['from']= x[1]
    edge['arrows']='to'
    return edge

#show relationships for an elements
@app.route('/node/<nodeid>', methods=['GET'])
def reponode(nodeid):     
    #load graph data
    G = nx.read_gpickle(os.path.join(datadir, "ea-nxgraph.pickle"))
    if not G.node.get(nodeid):
        return '<h3>No element found.</h3>'
    nx.set_edge_attributes(G, 'arrows', 'to')
    #node list
    nlist = [G.node[nodeid]]
    for g in G.neighbors(nodeid):
        nlist.append(G.node[g])
    for g in G.predecessors(nodeid):
        nlist.append(G.node[g])    
    #edge list
    elist = []
    nids = [n['id'] for n in nlist]
    for e in nx.edges(G, nids):
        elist.append(fedge(e))

    #load diagram data
    with open(os.path.join(datadir, "ea-diagrams.pickle"), 'rb') as handle:
        diagdict = pickle.load(handle)
    views = {}
    for vid in diagdict['nodeviews']['id-'+nodeid]:
        views[vid[3:]] = diagdict['viewnames'][vid]
    print(views)
        
    return render_template('ea-node.html', label=G.node[nodeid]['label'], views=views, nlist=nlist, elist=elist, modelid=MODELID)


#=======================================
#=======================================


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)

