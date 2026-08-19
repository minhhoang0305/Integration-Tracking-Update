using Microsoft.EntityFrameworkCore;

namespace IntegrationTracking.Api.Data;

public sealed class IntegrationTrackingDbContext(DbContextOptions<IntegrationTrackingDbContext> options)
    : DbContext(options)
{
    public DbSet<EmailAnalysis> EmailAnalyses => Set<EmailAnalysis>();
    public DbSet<EmailSourceRecord> EmailSourceRecords => Set<EmailSourceRecord>();
    public DbSet<GmailSyncState> GmailSyncStates => Set<GmailSyncState>();
    public DbSet<TemplateProposal> TemplateProposals => Set<TemplateProposal>();
    public DbSet<ReviewDecision> ReviewDecisions => Set<ReviewDecision>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var entity = modelBuilder.Entity<EmailAnalysis>();
        entity.ToTable("email_analyses");
        entity.HasKey(x => x.EmailId);
        entity.Property(x => x.EmailId).HasMaxLength(128);
        entity.Property(x => x.Sender).HasMaxLength(512);
        entity.Property(x => x.Subject).HasMaxLength(2048);
        entity.Property(x => x.Status).HasMaxLength(32);
        entity.Property(x => x.ResultJson).HasColumnType("jsonb");

        var message = modelBuilder.Entity<EmailSourceRecord>();
        message.ToTable("email_source_records");
        message.HasKey(x => x.Id);
        message.Property(x => x.Mailbox).HasMaxLength(512);
        message.Property(x => x.Folder).HasMaxLength(128);
        message.Property(x => x.SourceMessageId).HasMaxLength(1024);
        message.Property(x => x.InternetMessageId).HasMaxLength(1024);
        message.Property(x => x.ContentHash).HasMaxLength(64);
        message.Property(x => x.Sender).HasMaxLength(512);
        message.Property(x => x.Subject).HasMaxLength(2048);
        message.Property(x => x.Status).HasMaxLength(32);
        message.Property(x => x.GmailMessageId).HasMaxLength(256);
        message.Property(x => x.GmailThreadId).HasMaxLength(256);
        message.HasIndex(x => new { x.Mailbox, x.GmailMessageId }).IsUnique();
        message.HasIndex(x => x.ContentHash).IsUnique();

        var sync = modelBuilder.Entity<GmailSyncState>();
        sync.ToTable("gmail_sync_states");
        sync.HasKey(x => new { x.Mailbox, x.Folder });
        sync.Property(x => x.Mailbox).HasMaxLength(512);
        sync.Property(x => x.Folder).HasMaxLength(128);
        sync.Property(x => x.HistoryId).HasMaxLength(128);

        var proposal = modelBuilder.Entity<TemplateProposal>();
        proposal.ToTable("template_proposals");
        proposal.HasKey(x => x.Id);
        proposal.Property(x => x.Provider).HasMaxLength(256);
        proposal.Property(x => x.IntegrationId).HasMaxLength(256);
        proposal.Property(x => x.Status).HasMaxLength(32);
        proposal.Property(x => x.BaseManifestHash).HasMaxLength(64);
        proposal.HasIndex(x => new { x.EmailId, x.IntegrationId }).IsUnique();

        var review = modelBuilder.Entity<ReviewDecision>();
        review.ToTable("review_decisions");
        review.HasKey(x => x.Id);
        review.Property(x => x.Decision).HasMaxLength(32);
        review.Property(x => x.AdminIdentity).HasMaxLength(512);
    }
}
