# archimate-explorer
A navigator to search and explore Archi information via web browser

## About
This application allows searching repository model elements and navigating relationships (network graph) via web browser. It's intended to expose basic functionality of the 'Visualizer' tab in Archi, for those who don't have Archi installed. It is a python(flask) web server which uses CSV data exported from Archi. 

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
