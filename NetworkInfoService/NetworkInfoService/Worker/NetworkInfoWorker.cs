namespace NetworkInfoService.Worker
{
    public class NetworkInfoWorker : BackgroundService
    {
        private readonly ILogger<NetworkInfoWorker> _logger;

        public NetworkInfoWorker(ILogger<NetworkInfoWorker> logger)
        {
            _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("NetworkInfo Service started at: {time}", DateTimeOffset.Now);

            while (!stoppingToken.IsCancellationRequested)
            {
                await Task.Delay(60000, stoppingToken);
                _logger.LogInformation("NetworkInfo Service running at: {time}", DateTimeOffset.Now);
            }

            _logger.LogInformation("NetworkInfo Service stopped at: {time}", DateTimeOffset.Now);
        }
    }
}
