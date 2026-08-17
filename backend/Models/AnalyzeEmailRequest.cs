using System.ComponentModel.DataAnnotations;

namespace IntegrationTracking.Api.Models;

public sealed class AnalyzeEmailRequest
{
    public string EmailId { get; set; } = Guid.NewGuid().ToString();

    [Required]
    public string Sender { get; set; } = string.Empty;

    public string Subject { get; set; } = string.Empty;

    [Required]
    public string Body { get; set; } = string.Empty;

    public DateTime ReceivedAt { get; set; } = DateTime.UtcNow;
}