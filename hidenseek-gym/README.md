# Hide'n'Seek Multi-Agent Gym Environment

## Prerequisites

- [Docker](https://www.docker.com/)
- [Xming X Server for Windows](https://sourceforge.net/projects/xming/)
- Root/Admin Privileges

## How to
1. Download and install Docker
    * Download and install Xming X Server for Windows
	* Open XLaunch from Start Menu (it needs to be opened every time you test something or learn model)
2. Get your Internal IP Address (**ipconfig**)
3. Open CMD in folder with **Dockerfile**
4. Type: *docker build . -hns:latest*
    * It may take up to 15 mins to install
5. Type: *docker run --rm -it -e DISPLAY=****<Your_Internal_IP_Address>****:0.0 --volume=****<Where_To_Save_Monitor_MP4>****:/opt/app/monitor hns*
6. ...
7. Profit