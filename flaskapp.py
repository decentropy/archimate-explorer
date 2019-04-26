""" This is the web app server. """

from flask import Flask, request, redirect, render_template
import pandas as pd
from datetime import datetime
import networkx as nx

import config
import random
import string
import os

app = Flask(__name__)
app.debug = True

#home
@app.route('/')
def index(): 
    return render_template('welcome.html')


#refresh graph data from CSVs
@app.route('/refresh', methods=['GET'])
def refreshea(): #extract network/graph data: serialize into pickle
    #add edges
    df = pd.read_csv(os.path.join(config.DATA_DIR, 'relations.csv'))
    df['Source'] = df['Source'].astype(str)
    df['Target'] = df['Target'].astype(str)
    G = nx.from_pandas_edgelist(df, source='Target', target='Source', create_using=nx.DiGraph()) #backwards, not sure why

    #add nodes
    df = pd.read_csv(os.path.join(config.DATA_DIR, 'elements.csv'))   
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
    nx.write_gpickle(G, os.path.join(config.DATA_DIR, "ea-nxgraph.pickle"))
    return redirect("/")
    

#============= EA SEARCH ====================

#show links to matches found in elements.csv
@app.route('/search/<path:term>', methods=['GET'])
def easearch(term):
    df = pd.read_csv(os.path.join(config.DATA_DIR, "elements.csv"))[['ID','Type','Name']]
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
    G = nx.read_gpickle(os.path.join(config.DATA_DIR, "ea-nxgraph.pickle"))
    
    if not G.node.get(nodeid):
        return '<h3>No element found.</h3>'
    
    #G.node[nodeid]['font'] = {"size": 20}

    nlist = [G.node[nodeid]]
    for g in G.neighbors(nodeid):
        nlist.append(G.node[g])
    for g in G.predecessors(nodeid):
        nlist.append(G.node[g])
    
    nx.set_edge_attributes(G, 'arrows', 'to')
    
    elist = []
    nids = [n['id'] for n in nlist]
    for e in nx.edges(G, nids):
        elist.append(fedge(e))
        
    return render_template('ea-node.html', label=G.node[nodeid]['label'], docpath=config.ELEMENTS_PATH, nodeid=nodeid, nlist=nlist, elist=elist)


#=======================================
#=======================================


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)

