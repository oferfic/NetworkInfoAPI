using Microsoft.AspNetCore.Builder;
using NetworkInfoService.Worker;

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSystemd();

builder.Services.AddHostedService<NetworkInfoWorker>();

builder.Services.AddControllers();

var host = builder.Build();

host.MapControllers();

host.Run();
