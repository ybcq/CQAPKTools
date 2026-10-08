#!/usr/bin/env python3
"""Local file/folder picker helper using tkinter native dialogs."""
import sys
import os
import tkinter as tk
from tkinter import filedialog

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'file'
    title = sys.argv[2] if len(sys.argv) > 2 else '选择文件'
    filt = sys.argv[3] if len(sys.argv) > 3 else ''
    initial = sys.argv[4] if len(sys.argv) > 4 else os.path.expanduser('~')

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    try:
        if mode == 'folder':
            path = filedialog.askdirectory(
                title=title,
                initialdir=initial
            )
        else:
            filetypes = [('所有文件', '*.*')]
            if filt:
                exts = [e.strip().lower() for e in filt.split(',') if e.strip()]
                if exts:
                    patterns = ';'.join(f'*{e}' for e in exts)
                    filetypes = [(f'{filt} 文件', patterns), ('所有文件', '*.*')]
            path = filedialog.askopenfilename(
                title=title,
                initialdir=initial,
                filetypes=filetypes
            )
        if path:
            print(path, end='')
        else:
            print('', end='')
    finally:
        root.destroy()

if __name__ == '__main__':
    main()
