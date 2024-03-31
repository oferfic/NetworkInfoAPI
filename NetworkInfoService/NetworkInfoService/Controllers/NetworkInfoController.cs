using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using NetworkInfoService.Models;
using NetworkInfoService.Utils;

namespace NetworkInfoService.Controllers
{
    /**
    * NetworkInfoController
    *  The controller class that implements the required REST APIs.
    */
    [ApiController]
    [Route("[controller]")]
    public class NetworkInfoController : ControllerBase
    {
        private readonly ILogger<NetworkInfoController> _logger;

        public NetworkInfoController(ILogger<NetworkInfoController> logger)
        {
            _logger = logger;
        }


        /**
         *  The API to obtain the IP/s configuration of the network interface/s
         */
        [HttpGet]
        [Route("GetIPinfo")]
        [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(IEnumerable<NetworkInterfaceInfo>))]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public IActionResult GetIPinfo()
        {
            _logger.LogInformation("Calling GetIPinfo API");


            List<NetworkInterfaceInfo> interfacesInfo = NetworkInfoBuilder.GetNetworkInterfacesInfo().ToList();

            if (interfacesInfo.Count() == 0)
            {
                _logger.LogWarning("GetIPinfo API failed: Could not obtain proper IP configuration info");
                return NotFound("Could not obtain proper IP configuration info");
            }

            _logger.LogInformation("GetIPinfo API succeeded");
            return Ok(interfacesInfo);
        }
    }
}
