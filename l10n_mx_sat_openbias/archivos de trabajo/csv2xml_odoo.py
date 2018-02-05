###################################################
# csv2xml_odoo.py
# First row of the csv file must be header!
# First col of the csv file must be id
###################################################

import csv, sys

csvFile =  str(sys.argv[1])
xmlFile = csvFile.replace("csv", "xml")

csvData = csv.reader(open(csvFile))
xmlData = open(xmlFile, 'w')
xmlData.write( '<?xml version="1.0" encoding="utf-8"?>' + "\n")
# there must be only one top-level tag
xmlData.write('<odoo><data noupdate="1">' + "\n")

rowNum = 0
for row in csvData:
    if rowNum == 0:
        tags = row
        # replace spaces w/ underscores in tag names
        for i in range(len(tags)):
            tags[i] = tags[i].replace(' ', '_')
    else: 
        xmlData.write('<record' + "\n")
        for i in range(len(tags)):
            if tags[i]== "id":
                xmlData.write('    ' + 'id="' + row[i] + '" model = "' + csvFile.replace(".csv","") + '">' + "\n")
            else:
                xmlData.write('    ' + '<field name="' + tags[i] + '">' \
                          + row[i] + '</field>' + "\n")
        xmlData.write('</record>' + "\n")
            
    rowNum +=1

xmlData.write('</data>  </odoo>' + "\n")
xmlData.close()
