using Microsoft.EntityFrameworkCore;

namespace IntegrationTracking.Api.Data;

public sealed class IntegrationTrackingDbContext(DbContextOptions<IntegrationTrackingDbContext> options)
    : DbContext(options)
{
    public DbSet<EmailAnalysis> EmailAnalyses => Set<EmailAnalysis>();
    public DbSet<EmailSourceRecord> EmailSourceRecords => Set<EmailSourceRecord>();
    public DbSet<ImapSyncState> ImapSyncStates => Set<ImapSyncState>();

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
        message.HasIndex(x => new { x.Mailbox, x.Folder, x.UidValidity, x.ImapUid }).IsUnique();
        message.HasIndex(x => x.ContentHash).IsUnique();

        var sync = modelBuilder.Entity<ImapSyncState>();
        sync.ToTable("imap_sync_states");
        sync.HasKey(x => new { x.Mailbox, x.Folder });
        sync.Property(x => x.Mailbox).HasMaxLength(512);
        sync.Property(x => x.Folder).HasMaxLength(128);
    }
}
