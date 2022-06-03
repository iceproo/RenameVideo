"""
Rename video based on audio

Main file to rename a set of videofiles based 
on whats beeing said in the first seconds of videoclip

Version 7, 
Text that tells user that CSV-file can be edited is moved to bottom
Vers 8, 
Bug fixes - Handles when program is run in different folder
----------------------------
"""
# Handle file dialog
from ntpath import join, basename
import shutil
from tkinter import Tk
from tkinter import filedialog
from tkinter.filedialog import askopenfilenames
from shutil import copy
# To save audio
from moviepy.video.io.VideoFileClip import VideoFileClip
# Create new folder
import os, sys
# Speech to text
from speech_recognition import Recognizer, AudioFile, UnknownValueError

import csv


def main():
    csvNames = getCsvPath()
    possibleNames = unpackCSVNames(csvNames)
    possibleNamesWashed = washListNames(possibleNames)
    # Choose video files
    print("Choose what videos you want to categorize!")
    Tk().withdraw()
    filename = askopenfilenames()

    # Choose folder to store video files
    print("Choose directory where to put categorized videos")
    
    goalDirectory = filedialog.askdirectory()
    # Creates new directories to program
    tmpWavStorage = createDirectory(goalDirectory, "tmpWav")
    foldernameUncatigorized = "Uncategorized"
    directoryUndefined = createDirectory(goalDirectory, foldernameUncatigorized)
    directoryGuess = createDirectory(goalDirectory, "Guessing")
    
    # Loop though every viedo that is choosen
    for v in filename:
        orgName = basename(v)
        filenamePathWavtmp = extractAudio(v, tmpWavStorage, orgName)
        speechOutput, importSpeechSuccess = getSpeechToText(filenamePathWavtmp)
        directoryError = directoryUndefined
        # If we got a string from video
        if importSpeechSuccess:
            speechOutput = getListFromGoogleDict(speechOutput)
            speechOutputWashed = washListNames(speechOutput)

            rightName, importSpeechSuccess = chooseName(speechOutputWashed, possibleNamesWashed)
            rightName = convertBackOrgName(rightName,possibleNamesWashed,possibleNames, speechOutput[0])
            # If string dont match possible names
            if importSpeechSuccess == False:
                directoryError = directoryGuess                
        else:
            rightName = speechOutput
            
        # copy video file and set name based on sound
        currentGoalDirectory = setGoalDirectorySuccess(importSpeechSuccess, goalDirectory, directoryError)
        videoTag, suffix = orgName.split('.')
        newName = join(currentGoalDirectory, videoTag + rightName + "." + suffix)
        print(speechOutput)
        print("Choosen name: " + rightName)
        copy(v, newName)
    # Removes temporary audio folder    
    shutil.rmtree(tmpWavStorage)

    # Tell user that CSV-file can be edited
    print("\nFör att ändra möjliga namn som filer kan namnges till så kan CSV-fil" +
            " ändras. \nDen finns i samma mapp som programmet och det är viktigt att" +
            " dess namn fortsätter att vara ListOfNames.csv\n")



def setGoalDirectorySuccess(success, originalDir, errorDir):
    """
    Sets goal directory based on success

    Input:  success - True or False
            originalDir - Path to original directory
            errorDir - Path to error directory

    Output: Returns path to directory. Sets originalDir if true and errorDir if false
    """
    if success:
        path = originalDir
    else:
        path = errorDir
    return path



def createDirectory(dir, name):
    """
    Creates new directory if not exists
    
        dir: path to folder
        name: name on new directory to create
    """
    newDir = join(dir, name)        
    if not os.path.exists(newDir):               # Creates new folder
        os.makedirs(newDir)
    return newDir




def extractAudio(file, tmpStorage, name):
    """
    Extracts audio from first 10 seconds in vidoeclip

        file: Videofile that is source
        tmpStorage: Temporary storage for audio file
        name: Original name on video

        returns: Path to created audio file
    """
    videoFile = VideoFileClip(file)                      # Choosen video file
    duration = min(10,videoFile.duration)
    videoFileFirst = videoFile.subclip(0, duration)     # Save only first 10 sec
    
    nameFirst, format = name.split('.')
    filename = nameFirst + ".wav"
    filePath = join(tmpStorage,filename)
    videoFileFirst.audio.write_audiofile(filePath)      # Save audiofile to wav
    videoFile.close()

    return filePath 



def getSpeechToText(path):
    """
    Converts a .wav file to a text string

        path: Path to .wav file

        returns:    audio in file as string
                    boolean true false if text is collected without error. false if not
    """
    #initialize recognizer
    r = Recognizer()

    #open file
    with AudioFile(path) as source:
        #cleans noise
        r.adjust_for_ambient_noise(source)
        #listen for the data/load audio to memory
        audio_data = r.record(source)
        # convert speech to text
        try:
            text = r.recognize_google(audio_data, language="sv-SE",show_all=True)  
            success = True      
        except UnknownValueError:
            text = "Undefined"
            success = False
        
        if len(text) == 0:
            text = "Undefined" 
            success = False

        return text, success
    

def getCsvPath():
    """
    Returns Path where program is running
    """
    # determine if the application is a frozen `.exe` (e.g. pyinstaller --onefile) 
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    # or a script file (e.g. `.py` / `.pyw`)
    elif __file__:
        application_path = os.path.dirname(__file__)
    csvName = "ListOfNames.csv"
    application_path = os.path.join(application_path, csvName)
    return application_path

def getListFromGoogleDict(dict):
    """
    Get names from output from google recognizer

        Input: dictonarie from google recognizer
        Output: array with only possible outputs
    """
    name = []
    alt = dict['alternative']
    for n in alt:
        name.append(n['transcript'])

    return name

def washListNames(list):
    """
    Takes a list of names and transforms it to a more standardized name

    Puts name in lowercase, changes 'ph' --> 'f', 'y' --> 'j', 'w' --> 'v'

        Input:  List of names to be washed
        Output: List of washed names in same order as earlier
    """
    import re

    washedNames = []
    substitutions = [["ph", "f"],
                    ["y", "j"],
                    ["w", "v"],
                    ["h", ""],
                    ["c", "k"],
                    ["p", "b"]]
    for n in list:
        n = str(n)
        n = n.lower()
        n = re.sub(r'(.)\1+', r'\1', n)
        for s in substitutions:
            n = n.replace(s[0], s[1])
        washedNames.append(n)
    return washedNames
        

def convertBackOrgName(curName, washedNameList, orgNameList, speechOrg):
    """
    Converts an washed name back to original

        Input:  curName - current washed name
                washedNameList - List with washed names
                orgNameList - List with original names
                orgSpeechoutput - most likely speech output
        Output: orgName - original name before washing
    """
    try:
        index = washedNameList.index(curName)
        orgName = orgNameList[index]
    except ValueError:
        orgName = speechOrg

    return orgName

def chooseName(alt, list):
    """
    Check if name is in list and return correct name

        Input:  alt          - name to look for
                list         - list of possible names to look in
        Output: Correct name if found in list, else return string on index 0
                Bool if correct name is found, false if not found
    """
    changed = False
    correctName = alt[0]
    for s in alt:
        for name in list: 
            if name in s:
                correctName = name
                changed = True
                break
        if changed:
            break
        
        
    return correctName, changed


def unpackCSVNames(path):
    """
    Read csv

    Goal is to read from a csv file and import data from it

        Input: Path to csv-file with names
    
        Output: returns list of first names
    """
    with open(path, encoding="utf8") as f:
        reader = csv.reader(f)    
        names = []
        for row in reader:
            names.append(str(row))

    firstName = []
    for name in names:
        fullRow = name.split('\'')
        fullName = fullRow[1]
        fName = fullName.split(' ')
        fName = fName[0]
        if isInList(fName, firstName) == False:
            firstName.append(fName)
    
    return firstName

def isInList(item, list):
    """
    Checks if item is in list 

        Input:  item - string to look for
                list - list to look inside
        
        Output: TRUE if item is in list
                FALSE if object is NOT in list
    """
    isInList = False
    for i in list:
        if i == item:
            isInList = True
    
    return isInList

if __name__ == "__main__":
    main()