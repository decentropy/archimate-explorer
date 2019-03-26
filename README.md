# Archimate-Explorer
A web application to search and explore ArchiMate models.

## About
This web application let's others explore your repository, by searching model elements and traversing (network graph) relationships . It's intended to expose basic functionality of the 'Visualizer' tab in Archi, for a broader audience. It is a python(flask) web server which ingests CSV data exported from Archi. 

![screenshot](https://raw.githubusercontent.com/steve-vincent/archimate-explorer/master/screen.png "Screenshot")

## Get started

### Requirements
* Python, including modules: flask, pandas, networkx

### Instructions
- Download and run: 'python flaskapp.py'
- Open browser, e.g. http://localhost
- Follow instructions in welcome.html, to export your Archi data. (it's initially using Archinsurance example data)

### Advanced Tip
You can add a search box and "visualizer" links in your Archi published HTML, by customizing your report plugin STL files - so users can use them together. Bug me if you're interested... can add detailed instructions.
