# Author: Tyler Sherrod
# Created: 16 August 2020

# Timber Analytic - Image Pre-processing script

# This script allows the user to cycle through images, identifying specific objects in the image and designating their location in the image.

import os
import shutil
import sys

import tkinter as tk

from PIL import Image, ImageTk
from time import sleep
from tkinter import filedialog, simpledialog

def createFolders(path, unitName):
    unitFolder = os.path.join(path, unitName)
    trainingFolder = os.path.join(unitFolder, 'Training Images')
    processedFolder = os.path.join(unitFolder, 'Processed Images')
    
    if os.path.isdir(unitFolder):
        # Unit folder exists, verify that subfolders exist
        if not os.path.isdir(trainingFolder):
            os.mkdir(trainingFolder)

        if not os.path.isdir(processedFolder):
            os.mkdir(processedFolder)
            
    else:
        # Unit folder doesn't exist, create and then create subfolders
        os.mkdir(unitFolder)
        os.mkdir(trainingFolder)
        os.mkdir(processedFolder)

    return [path, trainingFolder, processedFolder]

def userInput():
    try:
        path = filedialog.askdirectory()
    except:
        raise Exception('No appropriate folder was chosen')

    
    unitName = simpledialog.askstring('Lot Number', 'Input lot number for this batch of images.')

    if not unitName:
        raise Exception('No name was given for the lot number')
    

    return path, unitName


class MainApp:

    def __init__(self, window, folders):
        
        # Set up file paths
        self.mainFolder, self.trainingFolder, self.processedFolder = folders
        print(self.mainFolder)

        # Build list of images
        self.imageList = os.listdir(self.mainFolder)
        print(self.imageList)

        # Initial setup of GUI
        self.loadImage(setup=True)

    def LeftDown(self, event):
        x1 = event.x
        x2 = x1 + 1
        y1 = event.y
        y2 = y1 + 1

        currentCrop = self.main.create_rectangle(x1,y1,x2,y2, fill='', width=1.5, outline='gray90')
        # draw rectangle, first four args are x,y of top left followed by x,y of bottom right
        #EMTPY STRING IN THE 'FILL' FIELD MEANS TRANSPARENT!!!

        self.cropLocations.append([currentCrop, x1, y1])

    def LeftDrag(self, event):
        xOG, yOG = self.cropLocations[-1][1:]
        xNew = event.x
        yNew = event.y

        if xNew < xOG:
            x1 = xNew
            x2 = xOG
        elif xNew > xOG:
            x1 = xOG
            x2 = xNew
        else:
            x1, y1, x2, y2 = self.main.coords(self.cropLocations[-1][0])

        if yNew < yOG:
            y1 = yNew
            y2 = yOG
        elif yNew > yOG:
            y1 = yOG
            y2 = yNew
        else:
            x1, y1, x2, y2 = self.main.coords(self.cropLocations[-1][0])

        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0

        x1, y1, x2, y2 = self.makeSquare(x1, y1, x2, y2)

        self.main.coords(self.cropLocations[-1][0], (x1,y1,x2,y2))

        sleep(.05)

    def LeftUp(self, event):
        x1, y1, x2, y2 = self.main.coords(self.cropLocations[-1][0])

        print('Tree located at: {}, {}, {}, {}'.format(int(x1), int(y1), int(x2), int(y2)))

    def NextPress(self):

        # Crop image
        self.cropImage()

        if len(self.imageList) == 0:
            sys.exit(0)

        # Load next image to canvas
        # Returns -1 for unacceptable file types
        while self.loadImage() != 0:
            pass

    def UndoPress(self):
        self.main.delete(self.cropLocations[-1][0])
        del self.cropLocations[-1]

    def DeletePress(self, event=None):
        self.UndoPress()

    def ReturnPress(self, event=None):
        self.DeletePress()

    def loadImage(self, setup=False):
        imageName = self.imageList[0]
        self.imageFile = os.path.join(self.mainFolder, imageName)

        print('Processing {}'.format(self.imageFile))

        _, ext = os.path.splitext(self.imageFile)
        if ext.lower() not in ['.png','.jpg','.jpeg']:
            print('Bypassing {}; {} is not an accepted file type'.format(imageName, ext))
            del self.imageList[0]
            return -1

        self.cropLocations = []

        #image = Image.open(self.imageFile)
        with Image.open(self.imageFile) as image:

            W, H = image.size
            print('Original image is {}x{}'.format(W,H))
            screenWidth = window.winfo_screenwidth()
            screenHeight = window.winfo_screenheight()

            if W > screenWidth or H > screenHeight:
                # Scale image so that largest dimensions fits within screen dimensions
                self.scaleFactor = min(screenWidth/W, screenHeight/H)

                W = round(W*self.scaleFactor)
                H = round(H*self.scaleFactor)

                print('Image was resized to {}x{}\n'.format(W,H))

                image = image.resize((W, H), Image.ANTIALIAS)

            UndoButtonX = 10
            UndoButtonY = H - 130

            NextButtonX = W - 10
            NextButtonY = H - 130

            if setup:
                self.main = tk.Canvas(window, width=W, height=H)
                self.main.pack()

                self.main.image = image = ImageTk.PhotoImage(image)
                # this additional main.image is a way to prevent tkinter from trashing the image by
                # attaching it to an attribute of the canvas (would also work with window.image)
                # Why? idk. http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm said to do this so I tried and it worked

                self.currentImage = self.main.create_image(0, 0, anchor='nw', image=image)
                # anchor seems to designate the location on the widget (in this case, image)
                # that the coordiantes are measured to

                # Insert buttons onto cavas:
                self.UndoButton = tk.Button(text = "Undo", command = self.UndoPress)
                self.UndoButton.configure(width=10, activebackground = "#33B5E5", relief=tk.FLAT)

                self.NextButton = tk.Button(text = "Next", command = self.NextPress)
                self.NextButton.configure(width = 10, activebackground = "#33B5E5", relief=tk.FLAT)

                self.UndoButtonWindow = self.main.create_window(UndoButtonX, UndoButtonY, anchor=tk.SW, window=self.UndoButton)
                self.NextButtonWindow = self.main.create_window(NextButtonX, NextButtonY, anchor=tk.SE, window=self.NextButton)

                self.main.bind('<Button-1>', self.LeftDown)
                self.main.bind("<B1-Motion>", self.LeftDrag)
                self.main.bind("<ButtonRelease-1>", self.LeftUp)
                window.bind("<Return>", self.ReturnPress)
                window.bind("<BackSpace>", self.DeletePress)

            else:
                # Adjust window size
                self.main.config(width=W, height=H)
                # Reposition Next Button
                self.NextButton.place(x=NextButtonX, y=NextButtonY, anchor=tk.SE)
                # Replace image
                self.main.image = image = ImageTk.PhotoImage(image)
                self.main.itemconfig(self.currentImage, image=image)

            del self.imageList[0]
            
            return 0

    def makeSquare(self, x1, y1, x2, y2):
        width = x2 - x1
        height = y2 - y1
        
        if width > height:
            y2 = y1 + width
        elif height > width:
            x2 = x1 + height
        
        return x1, y1, x2, y2

    def cropImage(self):

        _, img = os.path.split(self.imageFile)
        name, ext = os.path.splitext(img)
        
        for count, tree in enumerate(self.cropLocations):
            # Make a copy of the original image file
            newImageFile = self.trainingFolder + '/' + name + '-tree ' + str(count+1) + ext
            shutil.copyfile(self.imageFile, newImageFile)

            print(newImageFile)

            newImage = Image.open(newImageFile)

            x1, y1, x2, y2 = self.main.coords(tree[0])

            # Rescale cropping locations to match original image file
            x1 = int(round(x1/self.scaleFactor))
            y1 = int(round(y1/self.scaleFactor))
            x2 = int(round(x2/self.scaleFactor))
            y2 = int(round(y2/self.scaleFactor))

            cropped_image = newImage.crop((x1, y1, x2, y2))

            #cropped_image.show()
            cropped_image.save(newImageFile)

            self.main.delete(tree[0])

        # Move processed file
        os.replace(self.imageFile, os.path.join(self.processedFolder, img))
            


if __name__ == '__main__':
    
    # Set up initial window
    window = tk.Tk()
    
    # Prompy user for selection of folder location and lot identifier
    folderPath, unitName = userInput()

    # Check/build folders corresponding to image lot numbers
    folders = createFolders(folderPath, unitName)

    # Build main app and begin loop
    app = MainApp(window, folders)
    window.mainloop()
    