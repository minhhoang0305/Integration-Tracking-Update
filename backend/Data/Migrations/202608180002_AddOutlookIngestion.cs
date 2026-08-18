using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IntegrationTracking.Api.Data.Migrations;

[Migration("202608180002_AddOutlookIngestion")]
public partial class AddOutlookIngestion : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "outlook_messages",
            columns: table => new
            {
                Id = table.Column<string>(type: "text", nullable: false),
                GraphMessageId = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: false),
                InternetMessageId = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: false),
                ContentHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                Sender = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                Subject = table.Column<string>(type: "character varying(2048)", maxLength: 2048, nullable: false),
                Status = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                IgnoreReason = table.Column<string>(type: "text", nullable: true),
                EmailAnalysisId = table.Column<string>(type: "text", nullable: true),
                ReceivedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table => table.PrimaryKey("PK_outlook_messages", x => x.Id));
        migrationBuilder.CreateIndex(name: "IX_outlook_messages_ContentHash", table: "outlook_messages", column: "ContentHash", unique: true);
        migrationBuilder.CreateIndex(name: "IX_outlook_messages_GraphMessageId", table: "outlook_messages", column: "GraphMessageId", unique: true);

        migrationBuilder.CreateTable(
            name: "outlook_sync_states",
            columns: table => new
            {
                Mailbox = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                Folder = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                DeltaLink = table.Column<string>(type: "text", nullable: true),
                SubscriptionId = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                SubscriptionExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table => table.PrimaryKey("PK_outlook_sync_states", x => new { x.Mailbox, x.Folder }));
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "outlook_messages");
        migrationBuilder.DropTable(name: "outlook_sync_states");
    }
}
