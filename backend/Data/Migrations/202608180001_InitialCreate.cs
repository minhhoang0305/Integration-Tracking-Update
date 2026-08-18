using System;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IntegrationTracking.Api.Data.Migrations;

[DbContext(typeof(IntegrationTrackingDbContext))]
[Migration("202608180001_InitialCreate")]
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "email_analyses",
            columns: table => new
            {
                EmailId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                Sender = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                Subject = table.Column<string>(type: "character varying(2048)", maxLength: 2048, nullable: false),
                Body = table.Column<string>(type: "text", nullable: false),
                ReceivedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                Status = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                ResultJson = table.Column<string>(type: "jsonb", nullable: true),
                ErrorMessage = table.Column<string>(type: "text", nullable: true),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table => table.PrimaryKey("PK_email_analyses", x => x.EmailId));
    }

    protected override void Down(MigrationBuilder migrationBuilder) => migrationBuilder.DropTable("email_analyses");
}
