using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IntegrationTracking.Api.Data.Migrations;

[Migration("202608190001_ConvertOutlookToImap")]
public partial class ConvertOutlookToImap : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropIndex(name: "IX_outlook_messages_GraphMessageId", table: "outlook_messages");
        migrationBuilder.DropIndex(name: "IX_outlook_messages_ContentHash", table: "outlook_messages");
        migrationBuilder.RenameTable(name: "outlook_messages", newName: "email_source_records");
        migrationBuilder.RenameColumn(name: "GraphMessageId", table: "email_source_records", newName: "SourceMessageId");
        migrationBuilder.AddColumn<string>(name: "Mailbox", table: "email_source_records", type: "character varying(512)", maxLength: 512, nullable: false, defaultValue: "");
        migrationBuilder.AddColumn<string>(name: "Folder", table: "email_source_records", type: "character varying(128)", maxLength: 128, nullable: false, defaultValue: "INBOX");
        migrationBuilder.AddColumn<long>(name: "UidValidity", table: "email_source_records", type: "bigint", nullable: false, defaultValue: 0L);
        migrationBuilder.AddColumn<long>(name: "ImapUid", table: "email_source_records", type: "bigint", nullable: false, defaultValue: 0L);
        migrationBuilder.CreateIndex(name: "IX_email_source_records_ContentHash", table: "email_source_records", column: "ContentHash", unique: true);
        migrationBuilder.CreateIndex(name: "IX_email_source_records_Mailbox_Folder_UidValidity_ImapUid", table: "email_source_records", columns: new[] { "Mailbox", "Folder", "UidValidity", "ImapUid" }, unique: true);

        migrationBuilder.RenameTable(name: "outlook_sync_states", newName: "imap_sync_states");
        migrationBuilder.DropColumn(name: "DeltaLink", table: "imap_sync_states");
        migrationBuilder.DropColumn(name: "SubscriptionId", table: "imap_sync_states");
        migrationBuilder.DropColumn(name: "SubscriptionExpiresAt", table: "imap_sync_states");
        migrationBuilder.AddColumn<long>(name: "UidValidity", table: "imap_sync_states", type: "bigint", nullable: false, defaultValue: 0L);
        migrationBuilder.AddColumn<long>(name: "LastUid", table: "imap_sync_states", type: "bigint", nullable: false, defaultValue: 0L);
    }

    protected override void Down(MigrationBuilder migrationBuilder) => throw new NotSupportedException("Rollback to Microsoft Graph schema is not supported.");
}
