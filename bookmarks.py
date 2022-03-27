#JG

#simple program to handle opening of my favorite websites
#
#[TODO]--expand idea

#new,open,

''' The program maintains a set of bookmarks as pairs of (name, (URL, site_description))
strings and has facilities for the user to add, edit, and remove bookmarks, and
to open their web browser at a particular bookmarked web page.
The program has two windows: the main window with the menu bar, toolbar,
list of bookmarks, and status bar; and a dialog window for adding or editing
bookmarks'''

import tkinter
from tkinter.constants import *
import tkinter.ttk as ttk
#import ttkthemes as tk
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import pickle

import webbrowser
import os, sys

#[TODO]-- check out binding problem
#[TODO]-- customise GUI looks
#[TODO]-- consider an alternative like opening a specific browser with SELENIUM
       

class ScrolledListBox(tkinter.Listbox):
    def __init__(self, master=None, **kw):
        self._frame = tkinter.Frame(master)
        self._vbar = tkinter.Scrollbar(self._frame)
        #packing::::-after, -anchor, -before, -expand, -fill, -in, -ipadx, -ipady, -padx, -pady, or -side
        #griding::::-column, -columnspan, -in, -ipadx, -ipady, -padx, -pady, -row, -rowspan, or -sticky
        self._vbar.pack(side=RIGHT, fill=Y)
        #nb... packing trick for hbar and status bar skeptical

        kw.update({'yscrollcommand': self._vbar.set})# 'xscrollcommand':self._hbar.set})
        tkinter.Listbox.__init__(self, self._frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        self._vbar['command'] = self.yview
        self['relief'] = SUNKEN
        self['borderwidth'] = 5

        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        list_meths = vars(tkinter.Listbox).keys()
        methods = vars(tkinter.Pack).keys() | vars(tkinter.Grid).keys() | vars(tkinter.Place).keys()
        methods = methods.difference(list_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self._frame, m))


    def __str__(self):
        return str(self._frame)

#custom dialog
class AddEditForm(tkinter.Toplevel):
    def __init__(self, parent, name=None, url=None, description=None):
        super().__init__(parent)
        self.name = name
        self.url = url
        self.description=description if description is not None else 'None'
                     
        self.parent = parent
        self.accepted = False
        self.transient(self.parent)
        self.title("Bookmarks - " + (
            "Edit" if name is not None else "Add"))
        
        self.nameVar = tkinter.StringVar()
        if name is not None:
            self.nameVar.set(name)
        self.urlVar = tkinter.StringVar()
        self.urlVar.set(url if url is not None else "http://")
        
        frame = tkinter.Frame(self)
        nameLabel = tkinter.Label(frame, text="Name:", underline=0, font='times 13')
        nameEntry = tkinter.Entry(frame, textvariable=self.nameVar,font=('courier new', 15, 'bold'),fg='#20AA20', width=25)
        nameEntry.focus_set()

        urlLabel = tkinter.Label(frame, text="URL:", font='times 13',underline=0)
        urlEntry = tkinter.Entry(frame, textvariable=self.urlVar,font=('courier new', 15,'bold'), fg='#2020AA',width=25)

        destLabel=tkinter.Label(frame, text="Description",font='times 13', underline=0)
        self.destBox = tkinter.Text(frame, fg='blue', wrap=WORD, font=('courier new', 15, 'bold'),height=3, width=25)
        self.destBox.insert(1.0, self.description)
        okButton = tkinter.Button(frame, text="OK", width=5, font=('courier new', 15), command=self.ok)
        cancelButton = tkinter.Button(frame, text="Cancel",font=('courier new', 15),command=self.close)

        nameLabel.grid(row=0, column=0, sticky=tkinter.W, pady=3,padx=3)
        nameEntry.grid(row=0, column=1, columnspan=3,sticky=tkinter.EW, pady=3, padx=3)

        urlLabel.grid(row=1, column=0, sticky=tkinter.W, pady=3,padx=3)
        urlEntry.grid(row=1, column=1, columnspan=3,sticky=tkinter.EW, pady=3, padx=3)

        destLabel.grid(row=2, columnspan=3, column=0, sticky=E+W, pady=3,padx=3)
        self.destBox.grid(row=3, columnspan=3, column=0, sticky=tkinter.W, pady=3,padx=3)

        okButton.grid(row=4, column=2, sticky=tkinter.EW, pady=3,padx=3)
        cancelButton.grid(row=4, column=3, sticky=tkinter.EW, pady=3,padx=3)

        frame.grid(row=0, column=0, sticky=tkinter.NSEW)
        frame.columnconfigure(1, weight=1)
        window = self.winfo_toplevel()
        window.columnconfigure(0, weight=1)
        self.bind("<Alt-n>", lambda *ignore: nameEntry.focus_set())
        self.bind("<Alt-u>", lambda *ignore: urlEntry.focus_set())
        self.bind("<Alt-d>", lambda *ignore: self.destBox.focus_set())
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.close)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.grab_set()
        self.wait_window(self)

    def ok(self, event=None):
        self.name = self.nameVar.get()
        self.url = self.urlVar.get()
        self.description = self.destBox.get(1.0, END+'-1c')
        self.accepted = True
        self.close()

    def close(self, event=None):
        self.parent.focus_set()
        self.destroy()



class BookMarker(object):

    def __init__(self, parent):
        self.parentwindow=parent
        self.parentwindow.resizable(False,False)
        self.current_filename=None
        self.is_saved=False
        self.data={}
        
        self.parentwindow.title('Bookmark - Unnamed')

        self.init_widgets()

    def init_widgets(self):
        self.create_menu()
        
        tool_bar_frame=ttk.Frame(self.parentwindow)
        commands=(self.new_file, self.open_file, self.save_file, self.add_item,
                  self.edit_item, self.delete_item,self.open_in_newtab, self.open_in_newwindow)
        for label, command in zip(('New', 'Open', 'Save','Add', 'Edit',
                                   'Delete','ViewNT', 'ViewNW'),commands):
            tkinter.Button(tool_bar_frame, text=label, command=command).pack(side=LEFT)

        tool_bar_frame.grid(row=0, pady=2)

        frame=tkinter.Frame(self.parentwindow, relief=RAISED, borderwidth=4)
        self.lis_frame=tkinter.Frame(frame)#, relief=RAISED, borderwidth=4)
        frame.grid(row=1)

        self.list_box = ScrolledListBox(self.lis_frame, font=('courier new', 16, 'bold'), width=25,foreground='aqua',
                                        background='black',  #bg='#202020'
                                        selectmode=SINGLE,selectborderwidth=1,activestyle=DOTBOX,
                                        height=15,selectbackground='teal')
        self.list_box.grid(row=0, padx=7)
        self.statusbar=tkinter.Label(frame, font=('times', 12, 'bold'), foreground='green')
        self.statusbar.pack(side=BOTTOM, fill=X)
        self.lis_frame.pack(side=BOTTOM,fill=BOTH)
        self.setstatusbar_text('Getting Ready...')
        self.parentwindow.bind('<Double-Button-1>', lambda ev:self.open_in_newtab())
        self.parentwindow.bind('<Shift-Double-Button-1>', lambda ev:self.open_in_newwindow())


    def create_menu(self):
        menubar = tkinter.Menu(self.parentwindow, tearoff=0)
        file_menu = tkinter.Menu(menubar, tearoff=0,font='times 13')
        edit_menu = tkinter.Menu(menubar, tearoff=0, font='times 13')

        #[FILEMENU]
        for label, command, shortcut_text, shortcut in (
            ("New...", self.new_file, "Ctrl+N", "<Control-n>"),
            ("Open...", self.open_file, "Ctrl+O", "<Control-o>"),
            ("Save", self.save_file, "Ctrl+S", "<Control-s>"),
            (None, None, None, None),
            ("Quit", self.quit_, "Ctrl+Q", "<Control-q>")):
            if label is None:
                file_menu.add_separator()
            else:
                file_menu.add_command(label=label, underline=0,
                                        command=command, accelerator=shortcut_text)
                self.parentwindow.bind(shortcut, lambda event:command())
        menubar.add_cascade(label="File ", menu=file_menu, underline=0)
        
        #[EDIT MENU]
        for label, command, shortcut_text, shortcut in (
            ("Add...", self.add_item, "Ctrl+A", "<Control-a>"),
            ("Edit...", self.edit_item, "Ctrl+A", "<Control-e>"),
            ("Delete", self.delete_item, "Del", "<Delete>"),
            (None, None, None, None),
            ("Open in New tab", self.open_in_newtab, "Ctrl+B", "<Control-b>"),
            ("Open in New Window", self.open_in_newwindow, "Ctrl+Shift+B", "<Control-Shift-b>")):
            if label is None:
                edit_menu.add_separator()
            else:
                edit_menu.add_command(label=label, underline=0,
                                        command=command, accelerator=shortcut_text)
                self.parentwindow.bind(shortcut, lambda ev:command())
                #print('bind ', shortcut, ' to ', command)
        menubar.add_cascade(label="Edit ", menu=edit_menu, underline=0)
        
        self.parentwindow['menu']=menubar

    def setstatusbar_text(self, text,timeout=5000):
        def clear():
            self.statusbar['text']=''

        self.statusbar['text']=text
        self.statusbar.after(timeout, clear)#clear labe after 5 seconds
        

    def okaytocontinue(self):
        if self.current_filename is None:
            return True
        if self.is_saved:
            return True
        reply = tkinter.messagebox.askyesnocancel(
                        "Bookmarks - Unsaved Changes",
                        f"Save Changes to '{self.current_filename}'?",
                        parent=self.parentwindow)
        if reply is None:
            return False
        if reply:
            self.save_file()
            return True

    def load_file(self, filename):
        self.current_filename = filename
        self.list_box.delete(0, END)
        self.is_saved = True
        try:
            with open(self.current_filename, "rb") as fh:
                self.data = pickle.load(fh)
            for name in sorted(self.data, key=str.lower):
                self.list_box.insert(END, name)
            self.setstatusbar_text("Loaded {0} bookmarks from {1}".format(
            self.list_box.size(), os.path.basename(self.current_filename)))
            self.parentwindow.title("Bookmarks - {0}".format(os.path.basename(self.current_filename)))
        except (EnvironmentError, pickle.PickleError) as err:
            messagebox.showwarning("Bookmarks - Error",
                        "Failed to load {0}:\n{1}".format(self.current_filename, err),
                                           parent=self.parentwindow)

    def new_file(self):
        if self.okaytocontinue():
            self.list_box.delete(0,END)
            self.parentwindow.title('Bookmark - Unnamed')
           

    def open_file(self):
        if not self.okaytocontinue():
             return
        filename = tkinter.filedialog.askopenfilename(
                    title="Bookmarks - Open File",
                    initialdir='.',
                    filetypes=[("Bookmarks files", "*.bmf")],
                    defaultextension=".bmf", parent=self.parentwindow)
        if filename:
            self.load_file(filename)
            
    def save_file(self):
        if self.current_filename is None:
            filename = tkinter.filedialog.asksaveasfilename(
                                        title="Bookmarks - Save File",
                                        initialdir=".",
                                        filetypes=[("Bookmarks files", "*.bmf")],
                                        defaultextension=".bmf",
                                        parent=self.parentwindow)
            if not filename:
                return 
            if not filename.endswith(".bmf"):
                self.current_filename += ".bmf"
            self.current_filename = filename
        try:
            with open(self.current_filename, "wb") as fh:
                pickle.dump(self.data, fh, pickle.HIGHEST_PROTOCOL)
                self.is_saved = True
                #[check
                self.setstatusbar_text("Saved {0} items to {1}".format(len(self.data), os.path.basename(self.current_filename)))
                self.parentwindow.title("Bookmarks - {0}".format(os.path.basename(self.current_filename)))
        except (EnvironmentError, pickle.PickleError) as err:
            messagebox.showwarning("Bookmarks - Error",
                            "Failed to save {0}:\n{1}".format(self.currrent_filename, err),
                            parent=self.parentwindow)


    def edit_item(self):
        selection = self.list_box.curselection()
        if not selection:
            return messagebox.showinfo('Edit', 'Select an item to edit !!')
        index = selection[0]
        name = self.list_box.get(index)
        form = AddEditForm(self.parentwindow, name, self.data[name][0], self.data[name][1])
        if form.accepted and form.name:
            self.data[form.name] = (form.url, form.description)
        if form.name != name:
            del self.data[name]
            
        self.list_box.delete(0, tkinter.END)
        for name in sorted(self.data, key=str.lower):
            self.list_box.insert(tkinter.END, name)
        self.is_saved=False
        
    def add_item(self):
        form = AddEditForm(self.parentwindow)
        if form.accepted and form.name:
            self.data[form.name] = (form.url, form.description)
        self.list_box.delete(0, tkinter.END)
        for name in sorted(self.data, key=str.lower):
            self.list_box.insert(tkinter.END, name)
        self.is_saved=False

    def delete_item(self):
        indexes = self.list_box.curselection()
        if not indexes or len(indexes) > 1:
            return messagebox.showinfo('Delete', 'Select an item to delete !!')
        index = indexes[0]
        name = self.list_box.get(index)
        if tkinter.messagebox.askyesno("Bookmarks - Delete",
            "Delete '{0}'?".format(name)):
            self.list_box.delete(index)
            self.list_box.focus_set()
            del self.data[name]
            self.is_saved=False
    def open_in_newtab(self):#bind to double click
        indexes = self.list_box.curselection()
        if not indexes or len(indexes) > 1:
            return messagebox.showinfo('Open In New Tab', 'Select an item to open in a new tab')
        index = indexes[0]
        url = self.data[self.list_box.get(index)][0]
        webbrowser.open_new_tab(url)
        
    def open_in_newwindow(self):#bind to shift double click
        indexes = self.list_box.curselection()
        if not indexes or len(indexes) > 1:
            return messagebox.showinfo('Open In New Window', 'Select an item to open in a new window') 
        index = indexes[0]
        url = self.data[self.list_box.get(index)][0]
        webbrowser.open_new(url)

    def quit_(self):
        if not self.current_filename:#if self.current_filename is None
            messagebox.showwarning('Warning', "You haven't saved this file yet")
            if messagebox.askyesnocancel('Save', 'Do you want to save now?'):
                self.save_file()
        if not self.okaytocontinue():
            return
        if messagebox.askokcancel('Exit', 'Exit Bookmarker?'):
            self.parentwindow.quit()
            self.parentwindow.destroy()
            sys.exit(0)

    
        
if __name__=='__main__':
    root=tkinter.Tk()
    app=BookMarker(root)
    root.protocol('WM_DELETE_WINDOW', app.quit_)
    root.mainloop()













