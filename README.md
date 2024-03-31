## NetworkInfo API

The repository includes:
* Visual Studio Project source files.  VS Project name is **NetworkInfoService**  (created as a worker service), using .NET Core 6 .
* **Dockerfile** (inside the directory: my_ubuntu_dotnet6_sdk_with_network_info_published_folder) for creating the docker image of Ubuntu 20.04 , with .NET Core 6 SDK and the published folder of the NetworkInfo API (NetworkInfoService VS project)
  
<br />
Creating and running the docker container: <br />

&nbsp; [Following using docker image named &nbsp; *my_ubuntu_dotnet6_sdk_and_network_info* <br /> &nbsp;&nbsp; and docker container named &nbsp; *my_ubuntu_dotnet6_sdk_and_network_info_container*]
1. Create the docker image: &nbsp; &nbsp;   *docker build -t my_ubuntu_dotnet6_sdk_and_network_info .*
2. Create and run the docker container (interactive bash session): &nbsp; &nbsp;   *docker run --cap-add=NET_ADMIN --name my_ubuntu_dotnet6_sdk_and_network_info_container -ti --rm my_ubuntu_dotnet6_sdk_and_network_info /bin/bash*

<br />

Testing the API on the Ubuntu container session: <br />
&nbsp; Either configure the service on the Ubuntu or run its binary directy from the command line as follows: <br />
&nbsp; *$ cd network_info_service* <br />
&nbsp; Run on two terminal sessions (may use the tmux utility):
* On one terminal session run the service: &nbsp; &nbsp;   *$ dotnet NetworkInfoService.dll*
* On the other terminal run the following curl command (the web API is configured to be accessed by http protocol using 5275 port): &nbsp; &nbsp;   *curl -X 'GET' 'http://localhost:5275/NetworkInfo/GetIPinfo' -H 'accept: text/plain'*

