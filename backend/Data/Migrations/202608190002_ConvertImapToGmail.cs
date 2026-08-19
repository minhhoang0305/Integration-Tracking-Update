using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IntegrationTracking.Api.Data.Migrations;

[DbContext(typeof(IntegrationTrackingDbContext))]
[Migration("202608190002_ConvertImapToGmail")]
public partial class ConvertImapToGmail : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropIndex(name: "IX_email_source_records_Mailbox_Folder_UidValidity_ImapUid", table: "email_source_records");
        migrationBuilder.DropColumn(name: "UidValidity", table: "email_source_records");
        migrationBuilder.DropColumn(name: "ImapUid", table: "email_source_records");
        migrationBuilder.AddColumn<string>(name: "GmailMessageId", table: "email_source_records", type: "character varying(256)", maxLength: 256, nullable: false, defaultValue: "");
        migrationBuilder.AddColumn<string>(name: "GmailThreadId", table: "email_source_records", type: "character varying(256)", maxLength: 256, nullable: false, defaultValue: "");
        migrationBuilder.Sql("UPDATE email_source_records SET \"GmailMessageId\" = 'legacy-' || \"Id\" WHERE \"GmailMessageId\" = '';");
        migrationBuilder.CreateIndex(name: "IX_email_source_records_Mailbox_GmailMessageId", table: "email_source_records", columns: new[] { "Mailbox", "GmailMessageId" }, unique: true);

        migrationBuilder.RenameTable(name: "imap_sync_states", newName: "gmail_sync_states");
        migrationBuilder.DropColumn(name: "UidValidity", table: "gmail_sync_states");
        migrationBuilder.DropColumn(name: "LastUid", table: "gmail_sync_states");
        migrationBuilder.AddColumn<string>(name: "HistoryId", table: "gmail_sync_states", type: "character varying(128)", maxLength: 128, nullable: false, defaultValue: "");
        migrationBuilder.AddColumn<DateTime>(name: "WatchExpiresAt", table: "gmail_sync_states", type: "timestamp with time zone", nullable: true);

        migrationBuilder.CreateTable(
            name: "template_proposals",
            columns: table => new
            {
                Id = table.Column<string>(type: "text", nullable: false),
                EmailId = table.Column<string>(type: "text", nullable: false),
                Provider = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                IntegrationId = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                BaseManifestHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                Status = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                ErrorMessage = table.Column<string>(type: "text", nullable: true),
                ArtifactDirectory = table.Column<string>(type: "text", nullable: false),
                EvidenceJson = table.Column<string>(type: "text", nullable: false),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            }, constraints: table => table.PrimaryKey("PK_template_proposals", x => x.Id));
        migrationBuilder.CreateIndex(name: "IX_template_proposals_EmailId_IntegrationId", table: "template_proposals", columns: new[] { "EmailId", "IntegrationId" }, unique: true);
        migrationBuilder.CreateTable(
            name: "review_decisions",
            columns: table => new
            {
                Id = table.Column<string>(type: "text", nullable: false), ProposalId = table.Column<string>(type: "text", nullable: false),
                Decision = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false), AdminIdentity = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false), Note = table.Column<string>(type: "text", nullable: true), CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            }, constraints: table => table.PrimaryKey("PK_review_decisions", x => x.Id));
    }
    protected override void Down(MigrationBuilder migrationBuilder) => throw new NotSupportedException("Rollback to IMAP schema is not supported.");
}
