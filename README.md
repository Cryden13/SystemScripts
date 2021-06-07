# [System Scripts](https://github.com/Cryden13/SystemScripts)

A collection of scripts that can be easily called from command line.

## Usage

py -m systemscripts \[*method*] \[-h] \[-w] \[-a ARGS]

For additional information on each method, type the method followed by '-h'.

## Methods

### `AlterImages`

Resize image files with specified extensions (from config.ini) within this folder to 2k and optionally convert them to jpg.  
Requires ImageMagick (<https://imagemagick.org/>)

**Parameters:**

- *workingdir* (str): The path of the directory that contains the images

### `CompressVideo`

Compress video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to HEVC/H.265.

**Parameters:**

- *filepath* (str): The path to either a directory to be searched or a video file

### `ConvertVideo`

Convert video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to the preferred format.

**Parameters:**

- *filepath* (str): The path to either a directory to be searched or a video file

### `CreateBorder`

Create a topmost window that acts as a border around the currently active window.

**Parameters:**

- args: *\*rect* (list[int, int, int, int], optional): [default=None] if provided, must be [left, top, right, bottom] of current window

### `CreateSym`

Create a new SymLink in a parent directory.

**Parameters:**

- *parentdir* (str): The path of the directory where the SymLink will be placed

### `LnkToSym`

Convert a link file (*.lnk) to a SymLink.

**Parameters:**

- *linkpath* (str): The path to an existing link file (*.lnk)

### `OpenFolLoc`

Resolve all SymLinks in a folder, opening the resulting path.

**Parameters:**

- *folpath* (str): The path to the folder
- *parent* (str, optional): [default=None] The path to the parent folder, if applicable

### `PullSubfiles`

Move all files in this folder's subdirectories to this folder, recursively.

**Parameters:**

- *topdir* (str): the top-most directory to recurse from

### `TakeOwnership`

Take ownership of a file or folder (optional: recursively).

**Parameters:**

- *filepath* (str): The path to a file or folder

## Changelog

<table>
    <tbody>
        <tr>
            <th align="center">Version</th>
            <th align="left">Changes</th>
        </tr>
        <tr>
            <td align="center">1.0</td>
            <td>Initial release</td>
        </tr>
        <tr>
            <td align="center">2.0</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>added additional methods</li>
                        <li>overhauled just about everything</li>
                        <li>removed _msg.py</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>changed how configparser works for stability</li>
                    </ul>
                </dl>
            </td>
        </tr>
    </tbody>
</table>
