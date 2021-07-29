#!/ef/efabless/opengalaxy/venv/bin/python3
#
# Simple ttk treeview with scrollbar and select button

import os
import json

import tkinter
from tkinter import ttk
import natsort
#------------------------------------------------------
# Tree view used as a multi-column list box
#------------------------------------------------------

class TreeViewChoice(ttk.Frame):
    def __init__(self, parent, fontsize=11, markDir=False, deferLoad=False, selectVal=None, natSort=False, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        s = ttk.Style()
        s.configure('normal.TLabel', font=('Helvetica', fontsize))
        s.configure('title.TLabel', font=('Helvetica', fontsize, 'bold'))
        s.configure('normal.TButton', font=('Helvetica', fontsize),
			border = 3, relief = 'raised')
        s.configure('Treeview.Heading', font=('Helvetica', fontsize, 'bold'))
        s.configure('Treeview.Column', font=('Helvetica', fontsize))
        self.markDir = markDir
        self.initSelected = selectVal
        self.natSort = natSort
        self.emptyMessage1 = '(no items)'
        self.emptyMessage  = '(loading...)' if deferLoad else self.emptyMessage1

    # Last item is a list of 2-item lists, each containing the name of a button
    # to place along the button bar at the bottom, and a callback function to
    # run when the button is pressed.

    def populate(self, title, itemlist=[], buttons=[], height=10, columns=[0],
		versioning=False):
        self.itemlist = itemlist[:]
        
        treeFrame = ttk.Frame(self)
        treeFrame.pack(side='top', padx=5, pady=5, fill='both', expand='true')
        
        scrollBar = ttk.Scrollbar(treeFrame)
        scrollBar.pack(side='right', fill='y')
        self.treeView = ttk.Treeview(treeFrame, selectmode='browse', columns=columns, height=height)
        self.treeView.pack(side='left', fill='both', expand='true')
        scrollBar.config(command=self.treeView.yview)
        self.treeView.config(yscrollcommand=scrollBar.set)
        self.treeView.heading('#0', text=title, anchor='w')
        buttonFrame = ttk.Frame(self)
        buttonFrame.pack(side='bottom', fill='x')

        self.treeView.tag_configure('odd',background='white',foreground='black')
        self.treeView.tag_configure('even',background='gray90',foreground='black')
        self.treeView.tag_configure('select',background='darkslategray',foreground='white')

        self.func_buttons = []
        for button in buttons:
            func = button[2]
            # Each func_buttons entry is a list of two items;  first is the
            # button widget, and the second is a boolean that is True if the
            # button is to be present always, False if the button is only
            # present when there are entries in the itemlist.
            self.func_buttons.append([ttk.Button(buttonFrame, text=button[0],
			style = 'normal.TButton',
			command = lambda func=func: self.func_callback(func)),
			button[1]])

        self.selectcallback = None
        self.lastselected = None
        self.lasttag = None
        self.treeView.bind('<<TreeviewSelect>>', self.retag)
        self.repopulate(itemlist, versioning)

    def get_button(self, index):
        if index >= 0 and index < len(self.func_buttons):
            return self.func_buttons[index][0]
        else:
            return None

    def retag(self, value):
        treeview = value.widget
        try:
            selection = treeview.selection()[0]
            oldtag = self.treeView.item(selection, 'tag')[0]
        except IndexError:
            # No items in view;  can't select the "(no items)" line.
            return

        self.treeView.item(selection, tag='selected')
        if self.lastselected:
            try:
                self.treeView.item(self.lastselected, tag=self.lasttag)
            except:
                # Last selected item got deleted.  Ignore this.
                pass
        if self.selectcallback:
            self.selectcallback(value)
        self.lastselected = selection
        self.lasttag = oldtag

    def repopulate(self, itemlist=[], versioning=False):

        # Remove all children of treeview
        self.treeView.delete(*self.treeView.get_children())

        if self.natSort:
            self.itemlist = natsort.natsorted( itemlist,
                                               alg=natsort.ns.INT |
                                               natsort.ns.UNSIGNED |
                                               natsort.ns.IGNORECASE )
        else:
            self.itemlist = itemlist[:]
            self.itemlist.sort()

        mode = 'even'
        for item in self.itemlist:
            # Special handling of JSON files.  The following reads a JSON file and
            # finds key 'ip-name' in dictionary 'data-sheet', if such exists.  If
            # not, it looks for key 'project' in the top level.  Failing that, it
            # lists the name of the JSON file (which is probably an ungainly hash
            # name).
            
            fileext = os.path.splitext(item)
            if fileext[1] == '.json':
                # Read contents of JSON file
                with open(item, 'r') as f:
                    try:
                        datatop = json.load(f)
                    except json.decoder.JSONDecodeError:
                        name = os.path.split(item)[1]
                    else:
                        name = []
                        if 'data-sheet' in datatop:
                            dsheet = datatop['data-sheet']
                            if 'ip-name' in dsheet:
                                name = dsheet['ip-name']
                        if not name and 'project' in datatop:
                            name = datatop['project']
                        if not name:
                            name = os.path.split(item)[1]
            elif versioning == True:
                # If versioning is true, then the last path component is the
                # version number, and the penultimate path component is the
                # name.
                version = os.path.split(item)[1]
                name = os.path.split(os.path.split(item)[0])[1] + ' (v' + version + ')'
            else:
                name = os.path.split(item)[1]

            # Watch for duplicate items!
            n = 0
            origname = name
            while self.treeView.exists(name):
                n += 1
                name = origname + '(' + str(n) + ')'
            mode = 'even' if mode == 'odd' else 'odd'
            # Note: iid value with spaces in it is a bad idea.
            if ' ' in name:
                name = name.replace(' ', '_')

            # optionally: Mark directories with trailing slash
            if self.markDir and os.path.isdir(item):
                origname += "/"
                
            self.treeView.insert('', 'end', text=origname, iid=name, value=item, tag=mode)
        if self.initSelected and self.treeView.exists(self.initSelected):
            self.setselect(self.initSelected)
            self.initSelected = None

        for button in self.func_buttons:
            button[0].pack_forget()

        if len(self.itemlist) == 0:
            self.treeView.insert('', 'end', text=self.emptyMessage)
            self.emptyMessage = self.emptyMessage1  # discard optional special 1st loading... message
            for button in self.func_buttons:
                if button[1]:
                    button[0].pack(side='left', padx = 5)
        else:
            for button in self.func_buttons:
                button[0].pack(side='left', padx = 5)

    # Return values from the treeview
    def getvaluelist(self):
        valuelist = []
        itemlist = self.treeView.get_children()
        for item in itemlist:
            value = self.treeView.item(item, 'values')
            valuelist.append(value)
        return valuelist

    # Return items from the treeview
    def getlist(self):
        return self.treeView.get_children()

    # This is a bit of a hack way to populate a second column,
    # but it works.  It only works for one additional column,
    # though, or else tuples will have to be generated differently.

    def populate2(self, title, itemlist=[], valuelist=[]):
        # Populate another column
        self.treeView.heading(1, text = title)
        self.treeView.column(1, anchor='center')
        n = 0
        for item in valuelist:
            child = os.path.split(itemlist[n])[1]
            # Get the item at this index
            oldvalue = self.treeView.item(child, 'values')
            newvalue = (oldvalue, item)
            self.treeView.item(child, values = newvalue)
            n += 1

    def func_callback(self, callback, event=None):
        callback(self.treeView.item(self.treeView.selection()))

    def bindselect(self, callback):
        self.selectcallback = callback

    def setselect(self, value):
        self.treeView.selection_set(value)

    def selected(self):
        value = self.treeView.item(self.treeView.selection())
        if value['values']:
            return value
        else:
            return None
