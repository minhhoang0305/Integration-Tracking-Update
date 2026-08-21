using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IntegrationTracking.Api.Data.Migrations;

[DbContext(typeof(IntegrationTrackingDbContext))]
[Migration("202608210001_AddProposalImpactAnalysis")]
public partial class AddProposalImpactAnalysis : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.AddColumn<string>(name: "ImpactJson", table: "template_proposals", type: "jsonb", nullable: false, defaultValue: "{}");
        migrationBuilder.AddColumn<string>(name: "ImpactSeverity", table: "template_proposals", type: "character varying(32)", maxLength: 32, nullable: false, defaultValue: "Unknown");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropColumn(name: "ImpactJson", table: "template_proposals");
        migrationBuilder.DropColumn(name: "ImpactSeverity", table: "template_proposals");
    }
}
