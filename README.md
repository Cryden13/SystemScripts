# [System Scripts](https://github.com/Cryden13/Python/tree/main/systemscripts)

A collection of scripts that can be easily called from command line.

## Usage

py -m systemscripts \[_method_] \[-h] \[-w] \[-a ARGS]

For additional information on each method, type the method followed by '-h'.

## Methods

### `alterImages`

- args: _workingdir_

Resize all image files in a directory to 2k and optionally convert them to jpg.  
Requires ImageMagick (<https://imagemagick.org/>)

### `convertToWebm`

- args: _workingdir_

Convert all \*.gif and \*.mp4 files within this folder and its subfolders to webm.  
Requires FFmpeg (<https://www.ffmpeg.org/>)

### `createBorder`

- args: _\*rect_

Create a topmost window that acts as a border around the currently active window.  
For use with my AutoHotkey script `SetOnTop` (TBD)

### `createSym`

- args: _parentdir_

Create a new SymLink in a parent directory.

### `lnkToSym`

- args: _linkpath_

Convert a link file (*.lnk) to a SymLink.

### `pullSubfiles`

- args: _topdir_

Move all files in `topdir`'s subdirectories to `topdir`, recursively.

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
    </tbody>
</table>
