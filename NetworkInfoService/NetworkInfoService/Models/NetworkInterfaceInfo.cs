namespace NetworkInfoService.Models
{
    /**
     * InterfaceInfo
     *  The model class for each network interface
     */
    public class NetworkInterfaceInfo
    {
        public NetworkInterfaceInfo(string networkInterfaceType, string networkInterfaceName)
        {
            NetworkInterfaceType = networkInterfaceType;
            NetworkInterfaceName = networkInterfaceName;
        }

        public string NetworkInterfaceType { get; }

        public string NetworkInterfaceName { get; }

        public List<IPinfo>? IPs { get; set;  }
    }
}
