FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY backend/IntegrationTracking.Api.csproj backend/
RUN dotnet restore backend/IntegrationTracking.Api.csproj

COPY backend/ backend/
COPY integrations/ integrations/
COPY test-fixtures/ test-fixtures/
WORKDIR /src/backend
RUN dotnet publish IntegrationTracking.Api.csproj --configuration Release --no-restore --output /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish ./
COPY --from=build /src/integrations ./integrations
COPY --from=build /src/test-fixtures ./test-fixtures
RUN mkdir proposals && chown -R 10001:0 /app
USER 10001
EXPOSE 8080
ENTRYPOINT ["dotnet", "IntegrationTracking.Api.dll"]
