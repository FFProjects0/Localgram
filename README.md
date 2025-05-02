# Localgram
![localgram](https://github.com/user-attachments/assets/33982019-c02a-453b-b0a5-2fc68ad69c16)
<!-- Issues Badge -->
[issues-shield]: https://img.shields.io/github/issues/FFProjects0/Localgram?style=flat&label=Issues&labelColor=001224&color=1DB954
[issues-url]: https://github.com/FFProjects0/Localgram/issues
<!-- Stars Badge -->
[stars-shield]: https://img.shields.io/github/stars/FFProjects0/Localgram?style=flat&label=Stars&labelColor=001224&color=1DB954
[stars-url]: https://github.com/FFProjects0/Localgram/stargazers
<!-- Downloads Badge -->
[downloads-shield]: https://img.shields.io/github/downloads/FFProjects0/Localgram/total.svg?style=flat&label=Downloads&labelColor=001224&color=1DB954
[downloads-url]: https://github.com/FFProjects0/Localgram/releases/

*A Program for viewing posts like Instagram does; just for local files.*
> [!CAUTION]
> This program often crashes when trying to close a video/slideshow. The cause is still unknown to me so use at your own risk.

# $$\color{lightgreen}Basic \space Usage \space Instructions$$
First, download the [template](https://github.com/FFProjects0/Localgram/tree/main/Template), then put the program in the root of that folder, play around and see what happens, you'll eventually know what to do, here's just a brief ovverview.
| File | Example |
| - | - |
| user.txt | @user.name |
| display.txt | Display Name |
| desc.txt | User Description<br>multi-line |
| counts.txt| 4788 - Follower Count<br>44 - Following Count |
| links.txt | link1.com<br>link2.com<br>link3.org<br>... |
|||
| videos.txt | 0001$04.29.2025:VideoTitle - `{index}${date:MM.DD.YYYY}:{title}` |
| slideshows.txt | 0001$04.29.2025:SlideshowTitle - `{index}${date:MM.DD.YYYY}:{title}` |
| ./Slideshows/0001/offset.txt | 7 - offsets song start by seconds in `./Slideshows/0001` |
| cover.png | Profile's profile picture |


| Files/Directories | Example | Disclaimer
| - | - | - |
| ./Slideshows | `./Slideshows/0001/1.png, 2.png, 3.png/song.mp3` - used with slideshows.txt | `0001 (videos.txt)` `0001 (slideshows.txt)` ARE NOT THE SAME THING!!
| ./Videos | `./Slideshows/0001.mp4` - used with videos.txt | `0001 (videos.txt)` `0001 (slideshows.txt)` ARE NOT THE SAME THING!!
