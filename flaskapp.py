""" This is the web app server. """

from flask import Flask, request, redirect, render_template, jsonify
import pandas as pd
from datetime import datetime
import networkx as nx
import os
import random
import string
import xml.etree.ElementTree as ET
import re
import pickle
import json
import ea


app = Flask(__name__)
app.debug = True

eadata = ea.dataobj() #persistent data

#=======================================
#    UI & RENDER
#=======================================


#test
@app.route('/test')
def test():
    return 'done.'


# Main/home
# -------------------------------------------------
@app.route('/')
def index():
    return redirect("/static/index.html")


# Search UI (wrapper frame)
# -------------------------------------------------
@app.route('/search/<path:type>/<path:term>', methods=['GET'])
def ui_search(type, term):
    return render_template('ea-search-frame.html', type=type, label=term)


# Search Results Frame UI
# -------------------------------------------------
@app.route('/results/<path:type>/<path:term>', methods=['GET'])
def ui_results(type, term):
    df = eadata.dfprops
    df = df[(df[type].str.contains(term, case=False, regex=False))]
    df = df.sort_values(['Type','Name'], ascending=[True,True]).reset_index(drop=True)
    respstr = "No matches found."
    if not df.empty:
        df['Results'] = df.apply(lambda x: "<li><a href='javascript:clickResult(\"" + x.ID + "\")'>" + x.Type + ": " + x.Name + "</a>", axis=1)
        respstr = ''.join(df['Results'].tolist())
    return render_template('ea-search-results.html', type=type, label=term, results=respstr)


# Node UI - Relations and Views
# -------------------------------------------------
@app.route('/node/<nodeid>', methods=['GET'])
def UI_node(nodeid):
    #load graph data
    G = eadata.G
    if not G.node.get(nodeid):
        return '<h2>No relationships for this element.</h2>'
    nlist = [G.node[nodeid]] #node list of dicts
    views = {} #view dict
    elist = [] #edge list of dicts

    #filter by layer: sbatpmio
    filter = request.args.get('filter')
    filterlookup = {"s":"strategy", "b":"business", "a":"application", "t":"technology", "p":"physical", "m":"motivation", "i":"implementation", "o":"other"}

    def fedge(x): #format for html
        edge = {}
        edge['to'] = x[0]
        edge['from']= x[1]
        edge['arrows']='from'
        return edge

    def addnode(x):
        #check filter
        if filter:
            for letter in filter:
                if x["type"] in ea.layers[filterlookup[letter]]:
                    return False
        #add node
        nlist.append(x)
        return True

    #iterate graph
    nids = [] #avoid dupes
    for g in G.successors(nodeid):
        if G.node[g]['type'] == "view":
            views[G.node[g]['id'].replace("id-","")] = G.node[g]['label']
        else:
            if addnode(G.node[g]):
                nids.append(G.node[g]['id']) #watch dupes
    for g in G.predecessors(nodeid):
        if G.node[g]['id'] not in nids: #no dupes
            addnode(G.node[g])
    #edge list
    buildedges = [n['id'] for n in nlist]
    for e in nx.edges(G, buildedges):
        elist.append(fedge(e))

    #get label
    dfe =  eadata.dfe.loc[eadata.dfe['ID'] == nodeid]
    label = dfe['Name'].values[0]
    type = dfe['Type'].values[0]

    #TODO - fix me, this WAS sloppy attribute rename for visjs 'Plan' coloring
    nlist2 = []
    for n in nlist:
        #n["group"] = n["plan"]
        nlist2.append(n)

    return render_template('ea-node.html', nodeid=nodeid, label=label, type=type, nlist=nlist2, elist=elist, views=views, modelid=ea.MODELID)


#=======================================
#    DATA PARSE & REFRESH
#=======================================

# Main refresh
# -------------------------------------------------
@app.route('/refreshea', methods=['GET'])
def refreshea():
    eadata.refresh()
    refresh_html()
    return redirect("/static/index.html")



# HTML Refresh
# -------------------------------------------------
#main function
def refresh_html():
    htmlpath = os.path.join(ea.path_root, "static")

    def gethtmlfiles(directory):
        filelist = []
        for filename in os.listdir(directory):
            if filename.endswith(".html"):
                filelist.append(os.path.join(directory, filename))
                continue
            else:
                continue
        return filelist

    def refresh_url_randomize(filepath):
        # Read in the file
        with open(filepath, 'r') as file :
          filedata = file.read()

        # Replace the target string
        randstr = ''.join(random.choice(string.ascii_letters) for m in range(5))
        filedata = filedata.replace('.html', '.html?' + randstr)
        filedata = filedata.replace('.png', '.png?' + randstr)

        # Write the file out again
        with open(filepath, 'w') as file:
          file.write(filedata)

    #randomize urls - CHROME IFRAME CACHING
    refresh_url_randomize(os.path.join(htmlpath, "index.html"))
    for htmlfiles in gethtmlfiles(os.path.join(htmlpath, ea.MODELID, "views")):
        refresh_url_randomize(htmlfiles)
    for htmlfiles in gethtmlfiles(os.path.join(htmlpath, ea.MODELID, "elements")):
        refresh_url_randomize(htmlfiles)


#=======================================
#    START
#=======================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)
