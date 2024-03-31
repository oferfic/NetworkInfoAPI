using NetworkInfoService.Models;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;

namespace NetworkInfoService.Utils
{
    /**
    * NetworkInfoBuilder
    *  The class serves as a utility for obtaining the required network info and prepare the required structured output accordingly.
    *  The class is implemented as a singleton.
    */
    public static class NetworkInfoBuilder
    {
        public static IEnumerable<NetworkInterfaceInfo> GetNetworkInterfacesInfo()
        {
            //Getting only the network interfaces that are Up
            IEnumerable<NetworkInterface> netInterfaces =
                NetworkInterface.GetAllNetworkInterfaces().Where(ni => ni.OperationalStatus == OperationalStatus.Up);
            List<NetworkInterfaceInfo> interfacesInfo = new List<NetworkInterfaceInfo>();
            foreach (NetworkInterface netInterface in netInterfaces)
            {
                NetworkInterfaceInfo interfaceInfo = new NetworkInterfaceInfo(netInterface.NetworkInterfaceType.ToString(),
                                                                              netInterface.Name);
                interfaceInfo.IPs = new List<IPinfo>();
                IPInterfaceProperties ip_sProperties = netInterface.GetIPProperties();
                UnicastIPAddressInformationCollection uniCast = ip_sProperties.UnicastAddresses;
                if (uniCast != null)
                {
                    foreach (UnicastIPAddressInformation uni in uniCast)
                    {
                        IPAddress ipAddr = uni.Address;
                        IPinfo ipInfo = new IPinfo((ipAddr.AddressFamily == AddressFamily.InterNetwork) ? "IPv4" : "IPv6",
                                                   ipAddr.ToString());
                        interfaceInfo.IPs.Add(ipInfo);
                    }
                }

                if (interfaceInfo.IPs.Count() > 0)
                {
                    interfacesInfo.Add(interfaceInfo);
                }
            }

            return interfacesInfo;
        }
    }
}
