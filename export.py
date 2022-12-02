import os
import subprocess
import sys
import tempfile

if len(sys.argv) <= 1 or sys.argv[1] == "-h" or sys.argv[1] == "?":
    print("Usage: python export.py <filename.scad> [fileType]\n")
    print("This script searches for \"module export()\" and individually renders and exports each item in it.")
    print("Each item is expected to be on its own line. The file name will be the comment on the same line, or the module call if no comment exists.")
    print("All files will be put in a folder with the same name as the scad file it's created from.")
    print("\nExample:\n")
    print("ExampleFile.scad")
    print("module export() {\n  cube(10);\n  sphere(5); //Ball\n}\n")
    print("\"python export.py ExampleFile.scad\" will generate a folder named \"ExampleFile exported\", and will contain the files \"cube.stl\" and \"Ball.stl\"")
    sys.exit()

scadFileName = sys.argv[1]
fileType = "stl"
if len(sys.argv) >= 3:
    fileType = sys.argv[2]
path = os.path.abspath(scadFileName)
endofpath = max(path.rfind("/"), path.rfind("\\"))+1
path = path[:endofpath]
folder = path + scadFileName[:scadFileName.rfind(".")] + " exported"
tempdir = tempfile.gettempdir()

lines = [""]

exportStart = 0
exportEnd = 0

def readFile(fileName):
    global exportStart
    global exportEnd
    global lines
    bracketCount = 0

    #read file contents
    fileIn = open(fileName, "r")
    lines = fileIn.read().splitlines()
    fileIn.close()

    lines = lines + ["", "module ____single(index) {", "\tchildren(index);", "}"]

    #fix relative imports
    for i in range(len(lines)):
        indexStart = -1
        indexEnd = -1
        if "use" in lines[i] or "include" in lines[i]:
            indexStart = lines[i].find("<")+1
            indexEnd = lines[i].find(">", indexStart)
        if "import" in lines[i]:
            indexStart = lines[i].find("\"")+1
            indexEnd = lines[i].find("\"", indexStart)
        if indexStart >= 0 and indexEnd >= 0:
            lines[i] = lines[i][:indexStart] + os.path.abspath(lines[i][indexStart:indexEnd]) + lines[i][indexEnd:]

        if "module export()" in lines[i]:
            index = lines[i].find("module export()")+14
            lines[i] = lines[i][:index] + "index) ____single(index" + lines[i][index:]

    #search for "module export()" and determine module size
    for i in range(len(lines)):
        if exportStart == 0 and "module export(index)" in lines[i]:
            if "{" in lines[i]:
                exportStart = i
            elif "{" in lines[i+1]:
                exportStart = i+1
        if exportStart != 0 and exportEnd == 0:
            for c in lines[i]:
                if c == "{":
                    bracketCount += 1
                if c == "}":
                    bracketCount -= 1
                    if bracketCount <= 0:
                        exportEnd = i
                        return


def runOpenSCAD(appendLine, fileName):
    #create temp scad file
    file = open(os.path.join(tempdir, "temp.scad"), "w")
    file.write("use <" + os.path.join(tempdir, "modified.scad") + ">")
    file.write("\n" + appendLine)
    file.flush()
    file.close()

    #export stl file
    subprocess.run(["openscad", "-o" + os.path.join(folder, fileName) + "." + fileType, os.path.join(tempdir, "temp.scad")])


def findFileName(string):
    #if a comment exists, use that as the file name
    if "//" in string:
        i = string.rfind("//")+2
        return string[i:]

    #if no comment exists, use the module name as the file name
    #this has the potential to overwrite previous files in this batch
    bracket = string.rfind("(")
    endWord = -1
    startWord = -1
    for i in range(bracket-1, -1, -1):
        if (string[i] != " "):
            endWord = i
            break
    for i in range(endWord-1, -1, -1):
        if (i == 0 or string[i] == " " or string[i] == "\t"):
            startWord = i+1
            break
    if startWord != -1 and endWord != -1:
        return string[startWord:endWord+1]


def compileRunSCAD():
    #create modified version of original
    modified = open(os.path.join(tempdir, "modified.scad"), "w")
    modified.write("\n".join(lines))
    modified.flush()
    modified.close()

    index = 0
    #for each module called in export(), create a temp scad file and call it at the end
    for i in range(exportStart + 1, exportEnd):
        if ";" in lines[i]:
            name = findFileName(lines[i])
            print("Generating " + name + ".stl")
            runOpenSCAD("export(" + str(index) + ");", name)
            index += 1

    #cleanup temp files
    os.remove(os.path.join(tempdir, "modified.scad"))
    os.remove(os.path.join(tempdir, "temp.scad"))


readFile(scadFileName)
if not os.path.exists(folder):
    os.mkdir(folder)
compileRunSCAD()
