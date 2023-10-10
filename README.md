# [System Scripts](https://github.com/Cryden13/SystemScripts)

A collection of scripts made to be easily called from command line.

## Usage

py -m systemscripts \[*method*] \[-h | --help] \[-w | --window] \[-a | --args ARGS]

For additional information on each method, type the method followed by '-h | --help'.

## Methods

### `AlterImages`

Resize image files with specified extensions (from config.ini) within this folder and/or convert them to JPG or PNG.  
**(Requires [ImageMagick](<https://imagemagick.org/>))

**Parameters:**

- *workingdir* (str): The path of the directory that contains the images

### `CompressVideo`

Convert and compress video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to HEVC/AAC or VP9/OPUS.

**Parameters:**

- *top_path* (str): The path to either a directory to be searched or a video file

### `CreateSym`

Create a new SymLink in a parent directory.

**Parameters:**

- *parentdir* (str): The path of the directory where the SymLink will be placed

### `LnkToSym`

Convert a link file (*.lnk) to a SymLink.

**Parameters:**

- *linkpath* (str): The path to an existing link file (*.lnk)

### `OpenFolLoc`

Resolve all SymLinks in a folder recursively, opening the resulting path.

**Parameters:**

- *folpath* (str): The path to the folder
- *parent* (str, optional): [default=None] The path to the parent folder, if applicable

### `PullSubfiles`

Move all files in this folder and its subdirectories to this folder, recursively.

**Parameters:**

- *topdir* (str): the top-most directory to recurse from/move to

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
        <tr>
            <td align="center">2.1</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>combined ConvertVideo and CompressVideo for simplicity</li>
                        <li>added a bunch of customization to ConvertVideo</li>
                        <li>added a bunch of customization to AlterImages</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>none👍</li>
                    </ul>
                </dl>
            </td>
        </tr>
        <tr>
            <td align="center">2.2</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>overhauled ConvertVideo</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>fixed ConvertVideo errors</li>
                    </ul>
                </dl>
            </td>
        </tr>
        <tr>
            <td align="center">2.3</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>ConvertVideo checks for subtitle language</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>Fixed selecting streams in ConvertVideo not working</li>
                    </ul>
                </dl>
            </td>
        </tr>
        <tr>
            <td align="center">3.0</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>createSim updated to PyQt5</li>
                        <li>ConvertVideo is now a sub-package for readability</li>
                        <li>Added a lot more options for ConvertVideo</li>
                        <li>Added a lot more info transparency in ConvertVideo</li>
                        <li>Added more options for ConvertVideo</li>
                        <li>Added more editable options for ConvertVideo in config</li>
                        <li>Added application icon for ConvertVideo</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>ConvertVideo properly parses audio</li>
                        <li>ConvertVideo properly parses subtitles</li>
                        <li>Stopped ConvertVideo from attempting to convert previously converted items</li>
                        <li>ConvertVideo properly closes after completion</li>
                    </ul>
                </dl>
            </td>
        </tr>
        <tr>
            <td align="center">3.1</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>Added more info for transparency in ConvertVideo</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>Fixed error in ConvertVideo dealing with audio channels</li>
                        <li>Fixed syntax error in AlterImages</li>
                    </ul>
                </dl>
            </td>
        </tr>
        <tr>
            <td align="center">3.2</td>
            <td>
                <dl>
                    <dt>new</dt>
                    <ul>
                        <li>Added more info for transparency in ConvertVideo</li>
                        <li>Added the option to NOT convert streams in ConvertVideo</li>
                        <li>Added the option to add arguments in ConvertVideo</li>
                    </ul>
                    <dt>bugfixes</dt>
                    <ul>
                        <li>Fixed error in ConvertVideo that caused sequential files to not be properly processed</li>
                        <li>Fixed syntax error in ConvertVideo that caused issues with webms</li>
                    </ul>
                </dl>
            </td>
        </tr>
    </tbody>
</table>
