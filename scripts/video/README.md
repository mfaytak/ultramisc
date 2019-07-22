# Setup

Some of the scripts in this module have additional dependencies. To run them, you must install the VLC media player and its Python bindings (in `python-vlc`), as well as the `easygui` package. 

If you are using the Berkeley Phonetics Machine, the following commands have worked for me. Note that you must start by updating aptitude, or the vlc player will not download. (I imagine these will also work on lots of other Unix systems with `pip` and aptitude installed).

```
sudo apt-get update
sudo apt-get install vlc
pip install python-vlc
pip install easygui
```
