namespace NetworkInfoService.Models
{
    /**
     * InterfaceInfo
     *  The model class for each IP address
     */
    public class IPinfo
    {
        public IPinfo(string type, string address)
        {
            Type = type;
            Address = address;
        }

        public string Type { get; }

        public string Address { get; }
    }
}
